import liblo
import logging
from .devicemanager import DeviceManager
from .ardour import Ardour
from .persiststate import PersistState
from .touchosc import TouchOSC

class OscarServer(liblo.ServerThread):
    def __init__(self, oscar_port=8000,
                 ardour_ip='127.0.0.1', ardour_port='3819',
                 touchosc_ip='127.0.0.1', touchosc_port='9000'):
        liblo.ServerThread.__init__(self, oscar_port)
        self.log = logging.getLogger(__name__)
        self.dm = DeviceManager()

        self.ardour = Ardour(self.dm, ardour_ip, ardour_port)
        self.dm.add_device(self.ardour)

        self.persist = PersistState()
        self.dm.add_device(self.persist)

        self.touchosc = TouchOSC(self.dm, touchosc_ip, touchosc_port)
        self.dm.add_device(self.touchosc)

        self.start()

    @liblo.make_method(None, None)
    def got_message(self, path, args):
        self.log.debug('Got message "{}" with arguments {}'.format(path, args))
        if path.startswith('/route/'):
            self.ardour.handle_osc(path, args)
        elif path.startswith('/oscar_page'):
            self.touchosc.handle_osc(path, args)
