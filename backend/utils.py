import datetime
from flask import request, current_app as app
from backend.extensions import db


def getClientIP(req):
    if req.headers.get('X-Real-IP'):
        return req.headers.get('X-Real-IP')
    elif req.headers.get('X-Forwarded-For'):
        return req.headers.get('X-Forwarded-For')
    else:
        return req.headers.get('REMOTE_ADDR')


# returns datetime if ISO 8601 format
def format_datetime(date, timezone=None):
    if not timezone:
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    if timezone > 0:
        date = date + datetime.timedelta(hours=timezone)
        return date.strftime(f"%Y-%m-%dT%H:%M:%S+{str(timezone).zfill(2)}:00")
    elif timezone < 0:
        date = date - datetime.timedelta(hours=abs(timezone))
        return date.strftime(f"%Y-%m-%dT%H:%M:%S-{str(timezone).zfill(2)}:00")


# returns datetime if ISO 8601 format
def format_date(date, timezone=None):
    if not timezone:
        return date.strftime("%Y-%m-%d")
    if timezone > 0:
        date = date + datetime.timedelta(hours=timezone)
        return date.strftime(f"%Y-%m-%d")
    elif timezone < 0:
        date = date - datetime.timedelta(hours=abs(timezone))
        return date.strftime(f"%Y-%m-%d")


def parse_date(date, timezone=None):
    try:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except Exception:
        return None
    if not timezone:
        return date
    if timezone > 0:
        return (date - datetime.timedelta(hours=timezone))
    elif timezone < 0:
        return (date + datetime.timedelta(hours=abs(timezone)))


def parse_datetime(date, timezone=None):
    try:
        date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    except Exception:
        return None
    if not timezone:
        return date
    if timezone > 0:
        return (date - datetime.timedelta(hours=timezone))
    elif timezone < 0:
        return (date + datetime.timedelta(hours=abs(timezone)))


def delete_keys(data: dict, keys: list) -> None:
    for key in keys:
        if key in data:
            del data[key]


def leave_keys(data: dict, keys: list) -> None:
    droplist = []
    for key, value in data.items():
        if key not in keys:
            droplist.append(key)
    delete_keys(data, droplist)


def analyze_lists(actual: [], new: []):
    '''
    Получает на вход текущий список (актуальный) и новый. Путем сравнения вычисляет что из текущего нужно удалить,
    а что из нового нужно добавить в текущий для приведения списков в соответствие друг другу.

    Возвращает кортеж из двух списков: что нужно добавить, и что удалить
    '''
    for_add = []
    for_remove = []

    for item in actual:
        if item not in new:
            for_remove.append(item)

    for item in new:
        if item not in actual:
            for_add.append(item)

    return for_add, for_remove

def commit() -> bool:
    '''
    Функция для коммита, чтобы не повторяться много раз в коде.
    '''
    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"Error commiting: {error}")
        return False
    return True

def add_and_commit(new_elem: db.Model) -> bool:
    '''
    Функция для добавления элемента и коммита, чтобы не повторяться много раз в коде.
    '''
    try:
        db.session.add(new_elem)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"Error adding and commiting: {error}")
        return False
    return True

def delete_and_commit(elem_for_delete: db.Model) -> bool:
    '''
    Функция для удаления элемента и коммита, чтобы не повторяться много раз в коде.
    '''
    try:
        db.session.delete(elem_for_delete)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        app.logger.error(f"Error deleting and commiting: {error}")
        return False
    return True
