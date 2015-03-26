import base64
from distutils.version import StrictVersion
import datetime
import hashlib
import json
import os
import random
import re
import socket
import shutil
import time
import sys

import seesaw
from seesaw.config import realize, NumberConfigValue
from seesaw.externalprocess import WgetDownload, ExternalProcess
from seesaw.item import ItemInterpolation, ItemValue
from seesaw.pipeline import Pipeline
from seesaw.project import Project
from seesaw.task import SimpleTask, SetItemKey, LimitConcurrent
from seesaw.tracker import PrepareStatsForTracker, GetItemFromTracker, \
    UploadWithTracker, SendDoneToTracker
from seesaw.util import find_executable


# check the seesaw version
if StrictVersion(seesaw.__version__) < StrictVersion("0.8.3"):
    raise Exception("This pipeline needs seesaw version 0.8.3 or higher.")



###########################################################################
# The version number of this pipeline definition.
#
# Update this each time you make a non-cosmetic change.
# It will be added to the WARC files and reported to the tracker.
VERSION = "20150321.03"
# USER_AGENT = 'ArchiveTeam'
TRACKER_ID = 'furaffinitydisco'
TRACKER_HOST = 'localhost:9080'
DISCO_TRACKER_URL = 'http://localhost:8058'


###########################################################################
# This section defines project-specific tasks.
#
# Simple tasks (tasks that do not need any concurrency) are based on the
# SimpleTask class and have a process(item) method that is called for
# each item.


class CheckIP(SimpleTask):
    def __init__(self):
        SimpleTask.__init__(self, "CheckIP")
        self._counter = 0

    def process(self, item):
        if self._counter <= 0:
            item.log_output('Checking IP address.')
            ip_set = set()

            ip_set.add(socket.gethostbyname('twitter.com'))
            ip_set.add(socket.gethostbyname('facebook.com'))
            ip_set.add(socket.gethostbyname('youtube.com'))
            ip_set.add(socket.gethostbyname('microsoft.com'))
            ip_set.add(socket.gethostbyname('icanhas.cheezburger.com'))
            ip_set.add(socket.gethostbyname('archiveteam.org'))

            if len(ip_set) != 6:
                item.log_output('Got IP addresses: {0}'.format(ip_set))
                item.log_output(
                    'You are behind a firewall or proxy. That is a big no-no!')
                raise Exception(
                    'You are behind a firewall or proxy. That is a big no-no!')

        # Check only occasionally
        if self._counter <= 0:
            self._counter = 10
        else:
            self._counter -= 1


def get_hash(filename):
    with open(filename, 'rb') as in_file:
        return hashlib.sha1(in_file.read()).hexdigest()


CWD = os.getcwd()
PIPELINE_SHA1 = get_hash(os.path.join(CWD, 'pipeline.py'))
SCRIPT_SHA1 = get_hash(os.path.join(CWD, 'discovery.py'))


def stats_id_function(item):
    # For accountability and stats.
    d = {
        'pipeline_hash': PIPELINE_SHA1,
        'script_hash': SCRIPT_SHA1,
        'python_version': sys.version,
    }

    return d


class DiscoveryArgs(object):
    def realize(self, item):
        args = [
            sys.executable,
            'discovery.py',
        ]

        item_type, item_value = item['item_name'].split(':', 1)

        doc = {
            'nickname': downloader,
            'discovery_type': item_type,
            'usernames': item_value.split(','),
            'disco_tracker': DISCO_TRACKER_URL,
        }

        if 'bind_address' in globals():
            doc['bind_address'] = globals()['bind_address']
            print('')
            print('*** Will bind address at {0} ***'.format(
                globals()['bind_address']))
            print('')

        args.append(base64.b64encode(json.dumps(doc).encode('ascii')))

        return realize(args, item)


###########################################################################
# Initialize the project.
#
# This will be shown in the warrior management panel. The logo should not
# be too big. The deadline is optional.
project = Project(
    title="FurAffinity discovery",
    project_html="""
        <img class="project-logo" alt="Project logo" src="http://archiveteam.org/images/1/1b/Fa_logo.png" height="50px" title=""/>
        <h2>FurAffinity discovery
            <span class="links">
                <a href="http://furaffinity.net/">Website</a> &middot;
                <a href="http://tracker.archiveteam.org/furaffinitydisco">Leaderboard</a> &middot;
                <a href="http://archiveteam.org/index.php?title=FurAffinity">Wiki</a>
            </span>
        </h2>
        <p>Discovering items.</p>
        <!--<p class="projectBroadcastMessage"></p>-->
    """,
    # utc_deadline=datetime.datetime(2000, 1, 1, 23, 59, 0)
)

pipeline = Pipeline(
    CheckIP(),
    GetItemFromTracker("http://%s/%s" % (TRACKER_HOST, TRACKER_ID), downloader,
                       VERSION),
    LimitConcurrent(
        NumberConfigValue(
            min=1, max=6, default=globals().get("num_disco_procs", "1"),
            name="shared:fadisco:num_disco_procs", title="Number of Processes",
            description="The maximum number of concurrent discovery processes."
        ),
        ExternalProcess(
            'Discovery',
            DiscoveryArgs(),
            max_tries=1,
            accept_on_exit_code=[0],
        ),
    ),
    PrepareStatsForTracker(
        defaults={"downloader": downloader, "version": VERSION},
        file_groups={"data": []},
        id_function=stats_id_function,
    ),
    SendDoneToTracker(
        tracker_url="http://%s/%s" % (TRACKER_HOST, TRACKER_ID),
        stats=ItemValue("stats")
    )
)
