import datetime
import random
import json
import re
import os
import uuid
import locale
from marshmallow import ValidationError
import requests
from flask import Blueprint, jsonify, make_response, abort, request, current_app as app
from backend.extensions import db
from backend.utils import format_datetime, format_date, parse_date, leave_keys, delete_keys, commit, add_and_commit, \
    delete_and_commit
from sqlalchemy import or_, and_, union_all, union, select, literal_column, column, literal, text, desc, not_
from .models import Devices, Messages

api = Blueprint('api', __name__)




@api.route('/device/<string:unique_id>/<string:token>', methods=["PUT"])
def api_device_put(unique_id, token):
    print(request.data)
    device = Devices.query.filter(Devices.unique_id == unique_id).first()
    if not device:
        device = Devices(unique_id=unique_id, token=token, last_connection=datetime.datetime.utcnow())
        if not add_and_commit(device):
            return make_response(jsonify({'errors': ['Unable to add device.'], 'data': None}), 500)
    elif device.token != token:
        return make_response(jsonify({'errors': ['Incorrect token.'], 'data': None}), 401)
    device.last_connection = datetime.datetime.utcnow()
    commit()
    data = None
    message = Messages.query.filter(Messages.device_id == device.id, Messages.from_device == False).order_by(Messages.date.desc()).first()
    if message:
        data = message.json
        print(message.id)
        Messages.query.filter(Messages.device_id == device.id, Messages.from_device == False, Messages.date <= message.date).delete()
        commit()
    return make_response(jsonify({'errors': None, 'data': data}), 200)
    

@api.route('/server/<string:unique_id>/<string:token>', methods=["PUT"])
def api_server_put(unique_id, token):
    device = Devices.query.filter(Devices.unique_id == unique_id).first()
    if not device:
        return make_response(jsonify({'errors': ['Device not found.'], 'data': None}), 404)
    elif device.token != token:
        return make_response(jsonify({'errors': ['Incorrect token.'], 'data': None}), 401)
    try:
        json = request.get_json()
    except Exception as err:
        return make_response(jsonify({'errors': ['Incorrect JSON.'], 'data': None}), 400)
    print(json)
    message = Messages(from_device=False, device_id=device.id, date=datetime.datetime.utcnow(), json=json)
    if not add_and_commit(message):
        return make_response(jsonify({'errors': ['Unable to add message.'], 'data': None}), 500)
    return make_response(jsonify({'errors': None, 'data': {}}), 200)
    