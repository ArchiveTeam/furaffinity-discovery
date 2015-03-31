import base64
import itertools
import json
import logging
import random


_logger = logging.getLogger(__name__)


class Model(object):
    def __init__(self, database, secrets_path):
        self._database = database
        self._secrets_path = secrets_path

    def add_user_discovery(self, results):
        usernames = tuple(itertools.chain(
            results['discovered_usernames'],
            results['username_private_map'].keys(),
            results['username_disabled_map'].keys(),
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

        user_infos = [
            {
                'username': key,
                'disabled': value,
                }
            for key, value in results['username_disabled_map'].items()
        ]
        self._database.update_disabled_users(user_infos)

    def add_user_private_discovery(self, results):
        usernames = tuple(itertools.chain(
            results['discovered_usernames'],
            results['username_disabled_map'].keys(),
        ))

        _logger.info('Add %d users.', len(usernames))

        self._database.add_users(usernames)

        user_infos = [
            {
                'username': key,
                'disabled': value,
            }
            for key, value in results['username_disabled_map'].items()
        ]
        self._database.update_disabled_users(user_infos)

    def get_secrets(self, ip_address):
        with open(self._secrets_path, 'r') as file:
            doc = json.loads(file.read())

        rand = random.Random(ip_address)
        secrets = doc['secrets']
        secret = rand.choice('secrets')

        return {
            'username': secret['username'],
            'password': base64.b64encode(secret['password'].encode('ascii')).decode('ascii')
        }
