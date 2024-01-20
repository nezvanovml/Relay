from backend.application import create_app
from celery import Celery
import os

config = os.environ.get("CONFIG", "master")

def make_celery(app):
    celery = Celery(
        app.import_name
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = create_app(config)
celery = make_celery(app)
