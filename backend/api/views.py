import datetime
import random
import json
import re
import os
import uuid
import locale
from marshmallow import ValidationError
import requests
import redis
from flask import Blueprint, jsonify, make_response, abort, request, send_file, current_app as app
from backend.extensions import db, socket
from backend.utils import format_datetime, format_date, parse_date, leave_keys, delete_keys, commit, add_and_commit, \
    delete_and_commit
from sqlalchemy import or_, and_, union_all, union, select, literal_column, column, literal, text, desc, not_
from .models import Devices, Firmwares
import uuid
import time

from .utils import allowed_file, DeviceConnection

DELAY_FOR_ESP_RESPONSE = 5 # Seconds for wait response from device



api = Blueprint('api', __name__)

@api.route('/command/<string:unique_id>/<string:token>', methods=["POST"])
def api_server_command_post(unique_id, token):
    device = DeviceConnection()
    if not device.authorize(unique_id, token, False):
        return make_response(jsonify({'errors': ['Device not found.'], 'data': None}), 404)
    try:
        payload = request.get_json(force=True)
    except Exception as err:
        return make_response(jsonify({'errors': ['Incorrect JSON.']}), 400)
    
    
    time_limit = time.time() + DELAY_FOR_ESP_RESPONSE
    request_uuid = str(uuid.uuid4())
    r = redis.Redis(host=app.config["config"].get("redis_host"), port=app.config["config"].get("redis_port"), db=0)
    subscriber = r.pubsub()
    subscriber.subscribe(f'response_{unique_id}')
    r.publish(f'request_{unique_id}', json.dumps({"command": payload, "uuid": request_uuid}))

    while time.time() < time_limit:
        new_message = subscriber.get_message()
        if new_message:
            if new_message.get("type") != 'message':
                continue
            _data = json.loads(new_message.get('data', None))
            if _data:
                response_uuid = _data.get("uuid", None)
                if response_uuid == request_uuid:
                    return make_response(jsonify({"command": _data.get("command", False)}), 200)
        time.sleep(0.5)

    return make_response(jsonify({"errors": ["No answer from esp"]}), 503)

@api.route('/system_info/<string:unique_id>/<string:token>', methods=["GET"])
def api_server_system_info_get(unique_id, token):
    device = DeviceConnection()
    if not device.authorize(unique_id, token, False):
        return make_response(jsonify({'errors': ['Device not found.'], 'data': None}), 404)
    
    time_limit = time.time() + DELAY_FOR_ESP_RESPONSE
    request_uuid = str(uuid.uuid4())
    r = redis.Redis(host=app.config["config"].get("redis_host"), port=app.config["config"].get("redis_port"), db=0)
    subscriber = r.pubsub()
    subscriber.subscribe(f'response_{unique_id}')
    r.publish(f'request_{unique_id}', json.dumps({"request": "system_info", "uuid": request_uuid}))

    while time.time() < time_limit:
        new_message = subscriber.get_message()
        if new_message:
            if new_message.get("type") != 'message':
                continue
            _data = json.loads(new_message.get('data', None))
            if _data:
                response_uuid = _data.get("uuid", None)
                if response_uuid == request_uuid:
                    return make_response(jsonify(_data.get("system_info", {})), 200)
        time.sleep(0.5)

    return make_response(jsonify({"errors": ["No answer from esp"]}), 503)

@api.route('/status/<string:unique_id>/<string:token>', methods=["GET"])
def api_server_status_get(unique_id, token):
    device = DeviceConnection()
    if not device.authorize(unique_id, token, False):
        return make_response(jsonify({'errors': ['Device not found.'], 'data': None}), 404)
    time_limit = time.time() + DELAY_FOR_ESP_RESPONSE
    request_uuid = str(uuid.uuid4())
    r = redis.Redis(host=app.config["config"].get("redis_host"), port=app.config["config"].get("redis_port"), db=0)
    subscriber = r.pubsub()
    subscriber.subscribe(f'response_{unique_id}')
    r.publish(f'request_{unique_id}', json.dumps({"request": "status", "uuid": request_uuid}))

    while time.time() < time_limit:
        new_message = subscriber.get_message()
        if new_message:
            if new_message.get("type") != 'message':
                continue
            _data = json.loads(new_message.get('data', None))
            if _data:
                response_uuid = _data.get("uuid", None)
                if response_uuid == request_uuid:
                    return make_response(jsonify(_data.get("status", {})), 200)
        time.sleep(0.5)

    return make_response(jsonify({"errors": ["No answer from esp"]}), 503)

@api.route('/firmware/<string:unique_id>/<string:token>', methods=["POST", "GET"])
def api_firmware_put(unique_id, token):
    device = Devices.query.filter(Devices.unique_id == unique_id).first()
    if not device:
        return make_response(jsonify({'errors': ['Device not found.'], 'data': None}), 404)
    elif device.token != token:
        return make_response(jsonify({'errors': ['Incorrect token.'], 'data': None}), 401)
    if request.method == 'POST':
        UPLOAD_FOLDER = app.config.get('firmware_root')
        

        if 'file' not in request.files:
            return make_response(jsonify({'errors': ['File not provided.'], 'data': None}), 400)
        file = request.files['file']
        if file.filename == '':
            return make_response(jsonify({'errors': ['File not provided.'], 'data': None}), 400)
        
        version = request.form.get('version', None)
        try:
            version = int(version)
        except Exception:
            return make_response(jsonify({'errors': ['version is not of type integer.'], 'data': None}), 400)
        # Проверяем чтобы версия была больше чем ранее загруженная
        firmware = Firmwares.query.filter(Firmwares.device_id==device.id, Firmwares.version >= version).first()
        if firmware:
            return make_response(jsonify({'errors': [f'provide incremented version of firmware.'], 'data': None}), 400)
        if file and allowed_file(file.filename):
            id = uuid.uuid4()
            filename = f'{str(id)}.bin' 
            file.save(os.path.join(app.config['config']['firmware_root'], filename))
            firmware = Firmwares(id=id, version=version, device_id=device.id, date=datetime.datetime.utcnow())
            if not add_and_commit(firmware):
                return make_response(jsonify({'errors': ['Unable to add firmware.'], 'data': None}), 500)
            return make_response(jsonify({'errors': None, 'data': {}}), 201)
        
        
        return make_response(jsonify({'errors': ['File extension must be .bin .'], 'data': None}), 400)
    elif request.method == 'GET':
        firmware = Firmwares.query.filter(Firmwares.device_id == device.id).order_by(Firmwares.version.desc()).first()
        if not firmware:
            return make_response(jsonify({'errors': ['Firmware for device not found.'], 'data': None}), 404)
        else:
            firmware.num_of_downloads += 1
            commit()
            path = os.path.join(app.config['config']['firmware_root'], f'{str(firmware.id)}.bin')
            return send_file(path, as_attachment=False)
        

@socket.route('/ws/device/v1')
def ws_device(ws):
    device = DeviceConnection()
    unauthorized_requests = 0
    r = redis.Redis(host=app.config["config"].get("redis_host"), port=app.config["config"].get("redis_port"), db=0)
    subscriber = r.pubsub()
    while True:
        if device.is_authorized:
            new_message = subscriber.get_message()
            if new_message:
                if new_message.get("type") == 'message':
                    _data = json.loads(new_message.get('data', {}))
                    print(f"Sending request: {_data} to {device.unique_id}")
                    ws.send(json.dumps(_data))

        received_data = ws.receive(timeout=1)
        esp_response = None
        if received_data: 
            try:
                esp_response = json.loads(received_data)
            except Exception:
                ws.send(json.dumps({"err": "BAD_JSON"}))
                continue
        # Запрашиваем авторизацию если она не пройдена
        if not device.is_authorized and not esp_response:
            print("DEVICE", None, device.is_authorized, esp_response)
            unauthorized_requests += 1
        elif not device.is_authorized and esp_response:
            if device.authorize(esp_response.get("id", None), esp_response.get("token", None)):
                ws.send(json.dumps({"info": "authorized"}))
                subscriber.subscribe(f"request_{device.unique_id}")
                firmware = device.get_firmware()
                if firmware:
                    ws.send(json.dumps({'fw': firmware}))
        elif device.is_authorized:
            print("DEVICE", device.id, device.is_authorized, received_data)
            device.update_last_connection()
            if esp_response:
                r.publish(f'response_{device.unique_id}', json.dumps(esp_response))

        # Закрываем сокет если за 5 тактов не проведена авторизация
        if unauthorized_requests >= 5:
            ws.close()




    
    