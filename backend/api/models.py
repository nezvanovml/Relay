import datetime
from backend.extensions import db
from sqlalchemy.dialects.postgresql import JSON, JSONB, ENUM as PgEnum, UUID
from enum import Enum
import uuid


class Devices(db.Model):
    __tablename__ = 'api_devices'
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True)
    token = db.Column(db.String(50), nullable=False)
    last_connection = db.Column(db.DateTime, default=datetime.datetime.utcnow(), nullable=False)
    version = db.Column(db.Integer, nullable=True)  

    def __repr__(self):
        return 'Devices %r' % self.id


class Messages(db.Model):
    __tablename__ = 'api_messages'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    json = db.Column(JSON, nullable=True)
    from_device = db.Column(db.Boolean, default=False)
    device_id = db.Column(db.Integer, db.ForeignKey('api_devices.id', ondelete='CASCADE'), nullable=False)
    device = db.relationship('Devices')
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow(), nullable=False)

    def __repr__(self):
        return 'Messages %r' % self.id
    

class Firmwares(db.Model):
    __tablename__ = 'api_firmwares'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = db.Column(db.Integer, nullable=False)  
    device_id = db.Column(db.Integer, db.ForeignKey('api_devices.id', ondelete='CASCADE'), nullable=False)
    device = db.relationship('Devices')
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow(), nullable=False)
    num_of_downloads = db.Column(db.Integer, default=0)

    def __repr__(self):
        return 'Firmwares %r' % self.id
    
    



