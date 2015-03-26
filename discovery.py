from __future__ import print_function
import base64

import json
import random
import requests
import socket
import sys
import time
import re


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3 Safari/600.3.18',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:36.0) Gecko/20100101 Firefox/36.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36',
]


def make_user_agent(seed):
    rand = random.Random(seed)

    user_agent = rand.choice(USER_AGENTS)
    user_agent += ' ArchiveTeam (compatible)'

    return user_agent


def print_(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()


def main():
    arg_doc = json.loads(base64.b64decode(sys.argv[1].decode('ascii')))
    # arg_doc = {
    #     'nickname': 'testuser',
    #     'discovery_type': 'usernames',
    #     'usernames': ['toberkitty', 'furryguitarherosam', 'jjake33', 'narnla'],
    #     'disco_tracker': 'http://localhost:8058'
    # }

    if 'bind_address' in arg_doc:
        # https://stackoverflow.com/questions/1150332/source-interface-with-python-and-urllib2
        real_socket_socket = socket.socket
        def bound_socket(*a, **k):
            sock = real_socket_socket(*a, **k)
            sock.bind((arg_doc['bind_address'], 0))
            return sock
        socket.socket = bound_socket

    user_agent = make_user_agent(arg_doc['nickname'])

    def fetch(url):
        headers = {'user-agent': user_agent}

        for try_num in range(5):
            print_('Fetch', url, '...', end='')
            response = requests.get(url, headers=headers, timeout=60)
            print_(str(response.status_code))

            if response.status_code != 200 or \
                    'Page generated in' not in response.text and \
                    'This user cannot be found.' not in response.text:
                print_('Problem detected. Sleeping.')
                time.sleep(60)
            else:
                time.sleep(random.uniform(0.5, 1.5))
                return response

        raise Exception('Giving up!')

    discovery_type = arg_doc['discovery_type']
    assert discovery_type == 'usernames'

    disco_tracker = arg_doc['disco_tracker']

    results = discover_usernames(arg_doc['usernames'], fetch)

    upload_username_results(results, disco_tracker)

    print_('Done!')


def upload_username_results(results, tracker_url):
    for try_count in range(10):
        print_('Uploading results...', end='')
        response = requests.post(
            tracker_url + '/api/user_discovery',
            data=json.dumps(results).encode('ascii'),
            timeout=60
        )
        print_(response.status_code)

        if response.status_code == 200:
            return
        else:
            print_('Sleeping...')
            time.sleep(60)


def discover_usernames(usernames, fetch):
    username_private_map = {}
    username_disabled_map = {}
    scraped_usernames = set()

    for username in usernames:
        url = 'https://www.furaffinity.net/user/{0}/'.format(username)
        response = fetch(url)

        if 'This user cannot be found.' in response.text:
            continue

        is_private = 'has elected to make their content available to registered users only' in response.text
        username_private_map[username] = is_private

        is_disabled = 'This user has voluntarily disabled access to their userpage.' in response.text
        username_disabled_map[username] = is_disabled

        if not is_private and not is_disabled:
            scraped_usernames.update(scrape_usernames(response.text))

    return {
        'discovered_usernames': tuple(scraped_usernames),
        'username_private_map': username_private_map,
        'username_disabled_map': username_disabled_map
    }


def scrape_usernames(text):
    for match in re.finditer(r'href="/user/([^"]+)"', text):
        username = match.group(1)
        username = username.strip('/')
        yield username


if __name__ == '__main__':
    main()
