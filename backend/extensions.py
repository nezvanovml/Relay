from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin


db = SQLAlchemy()
migrate = Migrate()

# Create an APISpec
spec = APISpec(
    title="Ваш инвестор: взыскание",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)