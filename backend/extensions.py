from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask_sock import Sock



db = SQLAlchemy()
migrate = Migrate()
socket = Sock()

# Create an APISpec
spec = APISpec(
    title="Ваш инвестор: взыскание",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)