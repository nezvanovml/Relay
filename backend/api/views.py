import datetime
import random
import json
import re
import os
import uuid
import locale
from marshmallow import ValidationError
import requests
from flask import Blueprint, jsonify, make_response, abort, request, send_file, current_app as app
from backend.extensions import db, socket
from backend.utils import format_datetime, format_date, parse_date, leave_keys, delete_keys, commit, add_and_commit, \
    delete_and_commit
from sqlalchemy import or_, and_, union_all, union, select, literal_column, column, literal, text, desc, not_
from .models import Devices, Messages, Firmwares
import uuid
from .utils import allowed_file

api = Blueprint('api', __name__)

# @api.route('/device/<string:unique_id>/<string:token>', methods=["PUT"])
# def api_device_put(unique_id, token):
#     device = Devices.query.filter(Devices.unique_id == unique_id).first()
#     if not device:
#         device = Devices(unique_id=unique_id, token=token, last_connection=datetime.datetime.utcnow())
#         if not add_and_commit(device):
#             return make_response('Unable to add device.', 500)
#     elif device.token != token:
#         return make_response('Incorrect token.', 401)
#     device.last_connection = datetime.datetime.utcnow()
#     commit()
#     try:
#         json_data = request.get_json(force=True)
#     except Exception as err:
#         return make_response(jsonify({'errors': ['Incorrect JSON.'], 'data': None}), 400)
#     print(json_data)

#     response = {'message': None, 'firmware': None}
#     message = Messages.query.filter(Messages.device_id == device.id, Messages.from_device == False).order_by(Messages.date.desc()).first()
#     if message:
#         response['message'] = message.json
#         print(message.id)
#         Messages.query.filter(Messages.device_id == device.id, Messages.from_device == False, Messages.date <= message.date).delete()
#         commit()
#     firmware = Firmwares.query.filter(Firmwares.device_id == device.id).order_by(Firmwares.version.desc()).first()
#     if firmware:
#         response['firmware'] = {'version': firmware.version}
#     return make_response(jsonify(response), 200)
    

@api.route('/server/<string:unique_id>/<string:token>', methods=["PUT"])
def api_server_put(unique_id, token):
    device = Devices.query.filter(Devices.unique_id == unique_id).first()
    if not device:
        return make_response(jsonify({'errors': ['Device not found.'], 'data': None}), 404)
    elif device.token != token:
        return make_response(jsonify({'errors': ['Incorrect token.'], 'data': None}), 401)
    try:
        json_data = request.get_json(force=True)
    except Exception as err:
        return make_response(jsonify({'errors': ['Incorrect JSON.'], 'data': None}), 400)
    print(json_data)
    message = Messages(from_device=False, device_id=device.id, date=datetime.datetime.utcnow(), json=json_data)
    if not add_and_commit(message):
        return make_response(jsonify({'errors': ['Unable to add message.'], 'data': None}), 500)
    return make_response(jsonify({'errors': None, 'data': {}}), 200)
    

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
        

class DeviceConnection:
    def __init__(self):
        self.__device = None
        self.is_authorized = False

        
    def update_last_connection(self):
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        self.__device.last_connection = datetime.datetime.utcnow()
        commit()

    def authorize(self, id:str, token:str):  
        if not id or not token or len(id) < 30 or len(token) < 30:
            return False
        device = Devices.query.filter(Devices.unique_id == id).first()
        if not device:
            device = Devices(unique_id=id, token=token, last_connection=datetime.datetime.utcnow())
            if not add_and_commit(device):
                raise Exception("Unable to create Device.")
        elif device.token != token:
            self.is_authorized = False
            return False
        self.__device = device
        self.is_authorized = True
        return True
    
    def get_message(self) -> dict | None:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _message = None
        message = Messages.query.filter(Messages.device == self.__device, Messages.from_device == False).order_by(Messages.date.desc()).first()
        if message:
            print(message.json)
            _message = message.json
            Messages.query.filter(Messages.device == self.__device, Messages.from_device == False, Messages.date <= message.date).delete()
            commit()
        return _message
    
    def post_message(self, message: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        message = Messages(from_device=True, device=self.__device, date=datetime.datetime.utcnow(), json=message)
        if not add_and_commit(message):
            return False
        return True
    
    def post_system_info(self, system_info: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        self.__device.system_info = system_info
        if not commit():
            return False
        return True
    
    def get_firmware_version(self) -> dict | None:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _firmware = None
        firmware = Firmwares.query.filter(Firmwares.device == self.__device).order_by(Firmwares.version.desc()).first()
        if firmware:
            _firmware = {'ver': firmware.version}
        return _firmware
    
    def get_device_id(self) -> int:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _firmware = None
        return self.__device.id

@socket.route('/')
def echo(ws):
    device = DeviceConnection()
    unauthorized_requests = 0
    while True:
        received_data = ws.receive(timeout=1)
        payload = None
        if received_data: 
            try:
                payload = json.loads(received_data)
            except Exception:
                ws.send(json.dumps({"err": "BAD_JSON"}))
                continue
        # Запрашиваем авторизацию если она не пройдена
        if not device.is_authorized and not payload:
            print(None, device.is_authorized, payload)
            unauthorized_requests += 1
        elif not device.is_authorized and payload:
            if device.authorize(payload.get("id", None), payload.get("token", None)):
                ws.send(json.dumps({"info": "AUTHORIZED"}))
                ws.send(json.dumps({"req": "SYSINFO"}))
        elif device.is_authorized:
            print(device.get_device_id(), device.is_authorized, received_data)
            device.update_last_connection()
            _message = device.get_message()
            if _message:
                ws.send(json.dumps({'mes': _message}))

            if payload:
                if 'mes' in payload: # Обрабатываем сообщение
                    device.post_message(payload.get('mes'))
                if 'system_info' in payload: # Обрабатываем системную информацию
                    device.post_system_info(payload.get('system_info', {}))
                if 'req' in payload: # Обрабатываем запрос данных
                    requested_data = payload.get('req')
                    if requested_data == 'fw': # Запрос версии прошивки
                        _firmware = device.get_firmware_version()
                        ws.send(json.dumps({'fw': _firmware}))


        # Закрываем сокет если за 5 тактов не проведена авторизация
        if unauthorized_requests >= 5:
            ws.close()



    