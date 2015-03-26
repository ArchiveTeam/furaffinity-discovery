import itertools
import logging


_logger = logging.getLogger(__name__)


class Model(object):
    def __init__(self, database):
        self._database = database

    def add_user_discovery(self, results):
        usernames = tuple(itertools.chain(
            results['discovered_usernames'],
            results['username_private_map'].keys()
        ))

        _logger.info('Add %d users.', len(usernames))

        self._database.add_users(usernames)

        user_infos = [
            {
                'username': key,
                'private': value,
            }
            for key, value in results['username_private_map'].items()
        ]

        self._database.update_private_users(user_infos)
