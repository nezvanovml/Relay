import os
from flask import Flask, jsonify, make_response
import yaml
import backend as app_root
from backend.extensions import db, migrate, spec
from logging.config import dictConfig
from flask_swagger_ui import get_swaggerui_blueprint

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))

# logger configuration
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(funcName)s (%(filename)s): %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


def get_config(config):
    path = os.path.join(APP_ROOT_FOLDER, 'config', f'{config}.yaml')
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


def create_app(config='master'):
    app = Flask(__name__)
    # here must be imported & declared all blueprints
    from backend.api.views import api
    app.register_blueprint(api, url_prefix='/api')

    app.config['env'] = config
    app.logger.info(f"Loading setting from: {config}")
    config = get_config(config)
    app.config['config'] = config

    # here must be imported all models
    import backend.api.models

    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", None)

    # DB initialization
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{config.get("postgres_user")}:{os.environ.get("POSTGRES_PASSWORD", "")}@{config.get("postgres_host")}:{config.get("postgres_port")}/{config.get("postgres_database")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Migrate initialization
    migrate.init_app(app, db)

    with app.app_context():
        import backend.middleware

    # Adding swagger interface for docs.
    swaggerui_blueprint = get_swaggerui_blueprint(
        '/docs',  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
        '/spec',
        config={  # Swagger UI config overrides
            'app_name': "Ваш инвестор: взыскание"
        }
    )
    app.register_blueprint(swaggerui_blueprint)

    # Initializing specs.
    spec.components.security_scheme("ApiKeyAuth", {"type": "apiKey", "in": "header", "name": "Authorization"})

    @app.route("/spec")
    def spec_get():
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                spec.path(view=app.view_functions[rule.endpoint])
        return jsonify(spec.to_dict())

    return app
