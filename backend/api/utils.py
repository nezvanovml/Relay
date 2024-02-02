import datetime
from backend.utils import commit, add_and_commit, format_date
from .models import Devices, Messages, Firmwares
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
    
    def get_message_device(self) :  
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
    
    def get_message_server(self) :  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _message = None
        message = Messages.query.filter(Messages.device == self.__device, Messages.from_device == True).order_by(Messages.date.desc()).first()
        if message:
            print(message.json)
            _message = message.json
            Messages.query.filter(Messages.device == self.__device, Messages.from_device == True, Messages.date <= message.date).delete()
            commit()
        return _message
    
    def get_messages_server(self) :  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _messages = []
        messages = Messages.query.filter(Messages.device == self.__device, Messages.from_device == True)
        for message in messages.order_by(Messages.date).all():
            _messages.append({"mes": message.json, "date": format_date(message.date)})
        messages.delete()
        commit()    
        return _messages
    
    def post_message_device(self, message: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        message = Messages(from_device=True, device=self.__device, date=datetime.datetime.utcnow(), json=message)
        if not add_and_commit(message):
            return False
        return True
    
    def post_message_server(self, message: dict) -> bool:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        message = Messages(from_device=False, device=self.__device, date=datetime.datetime.utcnow(), json=message)
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
    
    def get_system_info(self) -> dict:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        return self.__device.system_info
    
    def get_firmware_version(self):  
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
    