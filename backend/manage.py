from backend.application import create_app
from backend.extensions import db, socket
import argparse


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
Supported commands:
    * localserver - run local server with Debug=true
    * wsserver - run WS server
    * db_create - creates all DB models
    * db_init - init migrations
    * db_migrate - create new migrations
    * db_upgrade - apply all migrations 
    * db_downgrade - cancel migration
''')
parser.add_argument("command", help="Command you need to run")
parser.add_argument("-c", "--config", help="Which config you need to load")
args = parser.parse_args()

ALLOWED_COMMANDS = ['db_create', 'db_migrate', 'db_upgrade', 'db_downgrade', 'db_init', 'localserver', 'wsserver']


def localserver(app):
    app.run(host='0.0.0.0', port=80, debug=True)

def wsserver(app):
    socketio.run(app, host='0.0.0.0', port=80, debug=True)
    #app.run(host='0.0.0.0', port=80, debug=True)

def db_create(app):
    with app.app_context():
        db.create_all()


def db_init(app):
    from flask_migrate import init
    with app.app_context():
        init()


def db_migrate(app):
    from flask_migrate import migrate
    with app.app_context():
        migrate()


def db_upgrade(app):
    from flask_migrate import upgrade
    with app.app_context():
        upgrade()


def db_downgrade(app):
    from flask_migrate import downgrade
    with app.app_context():
        downgrade()


if __name__ == '__main__':

    if args.command not in ALLOWED_COMMANDS:
        print(f"Command {args.command} unrecognized.")
        parser.print_help()
    else:
        app = create_app(config=args.config) if args.config else create_app()
        if args.command == 'db_create':
            db_create(app)
        elif args.command == 'db_init':
            db_init(app)
        elif args.command == 'db_migrate':
            db_migrate(app)
        elif args.command == 'db_upgrade':
            db_upgrade(app)
        elif args.command == 'db_downgrade':
            db_downgrade(app)
        elif args.command == 'localserver':
            localserver(app)
        elif args.command == 'wsserver':
            wsserver(app)
