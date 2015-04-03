from __future__ import print_function
import base64
import codecs
import json
import random
import socket
import sys
import time
import re

import requests
import requests.exceptions


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
    # arg_doc = {
    #     'nickname': 'testuser',
    #     'discovery_type': 'search',
    #     # 'query': '@keywords%20puppy',
    #     'query': '@keywords%20kanto',
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
    requests_session = requests.Session()
    state = {
        'logged_in': False
    }

    def fetch(url, method='get', data=None, expect_status=200, headers=None):
        headers = {'user-agent': user_agent}

        if headers:
            headers.update(headers)

        for try_num in range(5):
            print_('Fetch', url, '...', end='')

            if method == 'get':
                response = requests_session.get(url, headers=headers, timeout=60)
            elif method == 'post':
                response = requests_session.post(url, headers=headers, data=data, timeout=60)
            else:
                raise Exception('Unknown method')

            print_(str(response.status_code))

            ok_text_found = (
                'Page generated in' in response.text or
                'This user cannot be found.' in response.text
            )

            is_404_error_page = (
                'This user cannot be found.' in response.text
            )

            if response.status_code != expect_status and not ok_text_found:
                print_('Problem detected. Sleeping.')
                time.sleep(60)
            elif ok_text_found and not is_404_error_page and state['logged_in'] and '/logout/' not in response.text:
                print_('Problem detected. Not logged in! Sleeping.')
                time.sleep(60)
                raise Exception('Not logged in!')
            elif ok_text_found and not is_404_error_page and state['logged_in'] and 'Toggle to hide Mature and Adult submissions.' not in response.text:
                print_('Problem detected. Cannot view adult material! Sleeping.')
                time.sleep(60)
                raise Exception('Cannot view adult material!')
            else:
                time.sleep(random.uniform(0.5, 1.5))
                return response

        raise Exception('Giving up!')

    discovery_type = arg_doc['discovery_type']
    disco_tracker = arg_doc['disco_tracker']

    def login():
        assert not state['logged_in']

        for try_count in range(10):
            print_('Get login secrets...', end='')
            try:
                response = requests.post(
                    disco_tracker + '/api/get_secrets?v=1',
                    timeout=60
                )
            except requests.exceptions.ConnectionError:
                print_('Connection error.')
                print_('Sleeping...')
                time.sleep(60)
            else:
                print_(response.status_code)

                if response.status_code == 200:
                    break
                else:
                    print_('Sleeping...')
                    time.sleep(60)
        else:
            raise Exception('Could not get secrets!')

        secrets_doc = json.loads(response.text)
        username = secrets_doc['username']
        password = base64.b64decode(secrets_doc['password'].encode('ascii')).decode('ascii')

        fetch(
            'https://www.furaffinity.net/' + 'login/?ref=https://www.furaffinity.net/',
            method='post', expect_status=302,
            headers={
                'origin': 'https://www.furaffinity.net',
                'pragma': 'no-cache',
                'referer': 'https://www.furaffinity.net/' + 'login/',
            },
            data={
                'action': 'login',
                'retard_protection': '1',
                'name': username,
                'pass': password,
                'login': codecs.encode('Ybtva gb SheNssvavgl', 'rot_13'),
            }
        )

        state['logged_in'] = True

        fetch('https://www.furaffinity.net/')

    def logout():
        assert state['logged_in']
        state['logged_in'] = False
        fetch('https://www.furaffinity.net/logout/', expect_status=302)

    if discovery_type == 'usernames':
        results = discover_usernames(arg_doc['usernames'], fetch)
        upload_username_results(results, disco_tracker)
    elif discovery_type == 'private_usernames':
        login()
        results = discover_usernames(arg_doc['usernames'], fetch)
        logout()

        # Ensure it is empty since we are already logged in and we don't want
        # to categorize any profiles as not private
        results.pop('username_private_map', None)

        upload_username_results(results, disco_tracker, scraped_from_private=True)
    elif discovery_type == 'search':
        results = discover_usernames_by_search(arg_doc['query'], fetch)
        upload_username_results(results, disco_tracker)
    else:
        raise Exception('Unknown discovery type')

    print_('Done!')


def upload_username_results(results, tracker_url, scraped_from_private=False):
    if scraped_from_private:
        url = tracker_url + '/api/user_private_discovery'
    else:
        url = tracker_url + '/api/user_discovery'

    for try_count in range(10):
        print_('Uploading results...', end='')
        try:
            response = requests.post(
                url,
                data=json.dumps(results).encode('ascii'),
                timeout=60
            )
        except requests.exceptions.ConnectionError:
            print_('Connection error.')
            print_('Sleeping...')
            time.sleep(60)
        else:
            print_(response.status_code)

            if response.status_code == 200:
                return
            else:
                print_('Sleeping...')
                time.sleep(60)

    raise Exception('Failed to upload.')


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


def discover_usernames_by_search(query, fetch):
    usernames = set()

    for page in range(1, 30):
        url = 'https://www.furaffinity.net/search/{query}?page={page}&perpage=60'.format(query=query, page=page)
        response = fetch(url)
        scraped_results = tuple(scrape_usernames(response.text))
        usernames.update(scraped_results)
        print_('(Found', len(scraped_results), ')')

        if 'class="button" type="submit" name="next_page"' not in response.text:
            break

    return {
        'discovered_usernames': tuple(usernames),
        'username_private_map': {},
        'username_disabled_map': {}
    }


def scrape_usernames(text):
    for match in re.finditer(r'href="/user/([^"]+)"', text):
        username = match.group(1)
        username = username.strip('/')
        yield username


if __name__ == '__main__':
    main()
