import datetime
from backend.utils import commit, add_and_commit, format_date, format_datetime
from .models import Devices, Firmwares
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
    
    def get_firmware(self):  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        _firmware = None
        firmware = Firmwares.query.filter(Firmwares.device == self.__device).order_by(Firmwares.version.desc()).first()
        if firmware:
            _firmware = {'ver': firmware.version}
        return _firmware
    
    @property
    def id(self) -> int:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        return self.__device.id
    
    @property
    def unique_id(self) -> str:  
        if not self.is_authorized:
            raise Exception("UNAUTHORIZED REQUEST")
        return self.__device.unique_id
    