import argparse

from tornado.ioloop import IOLoop

from fadisco.app import App
from fadisco.database import Database
from fadisco.model import Model


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('database')
    arg_parser.add_argument('--prefix', default='')
    arg_parser.add_argument('--port', default=8058, type=int)

    args = arg_parser.parse_args()

    database = Database(args.database)
    model = Model(database)

    app = App(model, prefix=args.prefix)
    app.listen(args.port)
    IOLoop.current().start()


if __name__ == '__main__':
    main()
