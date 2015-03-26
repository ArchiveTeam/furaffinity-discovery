import argparse
import logging

from tornado.ioloop import IOLoop

from fadisco.app import App
from fadisco.database import Database
from fadisco.model import Model


def main():
    logging.basicConfig(level=logging.INFO)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('database')
    arg_parser.add_argument('--prefix', default='')
    arg_parser.add_argument('--port', default=8058, type=int)
    arg_parser.add_argument('--xheaders', action='store_true')

    args = arg_parser.parse_args()

    database = Database(args.database)
    model = Model(database)

    app = App(model, prefix=args.prefix)
    app.listen(args.port, address='localhost', xheaders=args.xheaders)
    IOLoop.current().start()


if __name__ == '__main__':
    main()
