import sqlite3


class Database(object):
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    private INTEGER
                )
            ''')

    def add_users(self, usernames):
        with self.conn:
            self.conn.executemany(
                'INSERT OR IGNORE INTO users(username) VALUES (?)',
                [(username,) for username in usernames]
            )

    def update_private_users(self, user_infos):
        values = [
            (user_info['private'], user_info['username'])
            for user_info in user_infos
        ]
        with self.conn:
            self.conn.executemany(
                'UPDATE users SET private = ? WHERE username = ?',
                values
            )
