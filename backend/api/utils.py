import datetime
from backend.utils import commit, add_and_commit, format_date, format_datetime
from .models import Devices, Messages, Firmwares, Statuses, Commands
ALLOWED_EXTENSIONS = ['bin']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class DeviceConnection:
    def __init__(self):
        self.__device = None
        self.is_authorized = False

        
    def update_last_connection(self):
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        self.__device.last_connection = datetime.datetime.utcnow()
        commit()

    def authorize(self, id:str, token:str, create_if_not_exist = True):  
        if not id or not token or len(id) < 30 or len(token) < 30:
            return False
        device = Devices.query.filter(Devices.unique_id == id).first()
        if not device:
            if create_if_not_exist:
                device = Devices(unique_id=id, token=token, last_connection=datetime.datetime.utcnow())
                if not add_and_commit(device):
                    raise Exception("Unable to create Device.")
            else:
                self.is_authorized = False
                return False
        elif device.token != token:
            self.is_authorized = False
            return False
        self.__device = device
        self.is_authorized = True
        return True
    
    def device_get_command(self) :  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _command = None
        command = Commands.query.filter(Commands.device == self.__device, Commands.from_device == False).order_by(Commands.date.desc()).first()
        if command:
            print(command.json)
            _command = command.json
            Commands.query.filter(Commands.device == self.__device, Commands.from_device == False, Commands.date <= command.date).delete()
            commit()
        return _command
    
    def device_post_status(self, status_json: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        status = Statuses(device=self.__device, date=datetime.datetime.utcnow(), json=status_json)
        if not add_and_commit(status):
            return False
        return True
    
    # def get_message_server(self) :  
    #     if not self.is_authorized:
    #         raise Exception("UNAUTHORIZED REQUEST")
    #     _message = None
    #     message = Messages.query.filter(Messages.device == self.__device, Messages.from_device == True).order_by(Messages.date.desc()).first()
    #     if message:
    #         print(message.json)
    #         _message = message.json
    #         Messages.query.filter(Messages.device == self.__device, Messages.from_device == True, Messages.date <= message.date).delete()
    #         commit()
    #     return _message
    
    # def get_messages_server(self) :  
    #     if not self.is_authorized:
    #         raise Exception("UNAUTHORIZED REQUEST")
    #     _messages = []
    #     messages = Messages.query.filter(Messages.device == self.__device, Messages.from_device == True)
    #     for message in messages.order_by(Messages.date).all():
    #         _messages.append({"mes": message.json, "date": format_datetime(message.date)})
    #     messages.delete()
    #     commit()    
    #     return _messages
    
    def server_get_status(self) :  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _statuses = []
        last_date = None
        statuses = Statuses.query.filter(Statuses.device == self.__device)
        for status in statuses.order_by(Statuses.date).all():
            last_date = status.date if not last_date else status.date if status.date > last_date else last_date
            _statuses.append({"status": status.json, "date": format_datetime(status.date)})
        statuses.filter(Statuses.date < last_date).delete()
        commit()    
        return _statuses
    
    def server_get_activity(self) :  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        status = Statuses.query.filter(Statuses.device == self.__device).order_by(Statuses.date.desc()).first()
        if not status:
            return False
        if status.date > datetime.datetime.utcnow() - datetime.timedelta(seconds=30):
            return True
        return False
    
    def device_post_command(self, command_json: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        command = Commands(from_device=True, device=self.__device, date=datetime.datetime.utcnow(), json=command_json)
        if not add_and_commit(command):
            return False
        return True
    
    def server_post_command(self, command: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _command = Commands(from_device=False, device=self.__device, date=datetime.datetime.utcnow(), json=command)
        if not add_and_commit(_command):
            return False
        return True
    
    def device_post_system_info(self, system_info: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        self.__device.system_info = system_info
        if not commit():
            return False
        return True
    
    def get_system_info(self) -> dict:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        return self.__device.system_info
    
    def device_get_firmware(self):  
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
    