from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from flask_sock import Sock



db = SQLAlchemy()
migrate = Migrate()
socket = Sock()

