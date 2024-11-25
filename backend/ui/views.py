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
from flask import Blueprint, jsonify, make_response, abort, request, send_file, current_app as app, render_template, \
    flash, redirect, url_for
from backend.extensions import db, socket
from backend.utils import format_datetime, format_date, parse_date, leave_keys, delete_keys, commit, add_and_commit, \
    delete_and_commit
from sqlalchemy import or_, and_, union_all, union, select, literal_column, column, literal, text, desc, not_
from backend.api.models import Devices, Firmwares
from backend.api.utils import allowed_file

ui = Blueprint('ui', __name__, template_folder='templates')


@ui.route('/', methods=["GET"])
def ui_get():
    unique_id = request.args.get("unique_id", "")
    token = request.args.get("token", "")
    context = {"form": {"unique_id": unique_id, "token": token}, "device": {"found": False}}
    return render_template('main.html', context=context)


@ui.route('/system_info', methods=["GET"])
def ui_system_info_get():
    unique_id = request.args.get("unique_id", "")
    token = request.args.get("token", "")
    context = {"form": {"unique_id": unique_id, "token": token}, "device": {"found": False}}
    if len(token) and len(unique_id):
        device = Devices.query.filter(Devices.unique_id == unique_id, Devices.token == token).first()
    else:
        device = None

    if not device:
        flash("Device not found. Check your Unique ID/Token", "danger")
    else:
        context["device"]["found"] = True
    return render_template('system_info.html', context=context)


@ui.route('/firmware', methods=["GET", "POST"])
def ui_firmware_get():
    unique_id = request.args.get("unique_id", "")
    token = request.args.get("token", "")
    if len(token) and len(unique_id):
        device = Devices.query.filter(Devices.unique_id == unique_id, Devices.token == token).first()
    else:
        device = None

    if request.method == "POST":
        if not device:
            flash("Device not found. Check your Unique ID/Token", "danger")
            return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)
        UPLOAD_FOLDER = app.config.get('firmware_root')
        print(request.args.to_dict())
        if 'file' not in request.files:
            flash("Firmware file not provided", "danger")
            return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)
        file = request.files['file']
        if file.filename == '':
            flash("Firmware file not provided", "danger")
            return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)

        version = request.form.get('version', None)
        try:
            version = int(version)
        except Exception:
            flash("Firmware version must be an integer", "danger")
            return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)
        firmware = Firmwares.query.filter(Firmwares.device == device,
                                          Firmwares.version >= version).first()
        if firmware:
            flash("You must increment your firmware version.", "danger")
            return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)
        if file and allowed_file(file.filename):
            id = uuid.uuid4()
            filename = f'{str(id)}.bin'
            file.save(os.path.join(app.config['config']['firmware_root'], filename))
            firmware = Firmwares(id=id, version=version, device_id=device.id, date=datetime.datetime.utcnow())
            if not add_and_commit(firmware):
                flash("Firmware upload error", "danger")
                return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)
            flash("Firmware upload successfully", "success")
            return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)

        flash("Firmware file must be of type .bin.", "danger")
        return redirect(url_for('ui.ui_firmware_get', unique_id=unique_id, token=token, _method="GET"), 302)

    else:

        context = {"form": {"unique_id": unique_id, "token": token}, "device": {"found": False, "firmwares": [],
                                                                                "firmware_titles": ["Version",
                                                                                                    "Created",
                                                                                                    "Number of downloads"]}}
        if not device:
            flash("Device not found. Check your Unique ID/Token", "danger")
        else:
            context["device"]["found"] = True
            firmwares = Firmwares.query.filter(Firmwares.device == device).order_by(Firmwares.version.desc()).all()
            for firmware in firmwares:
                context["device"]["firmwares"].append(
                    {"version": firmware.version, "date": format_datetime(firmware.date),
                     "num_of_downloads": firmware.num_of_downloads})
        return render_template('firmware.html', context=context)
