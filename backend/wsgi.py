import backend.application as application
import os

config = os.environ.get("CONFIG", "master")
app = application.create_app(config)
