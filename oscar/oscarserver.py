import liblo
from .devicemanager import DeviceManager
from .ardour import Ardour
from .persiststate import PersistState
from .touchosc import TouchOSC

class OscarServer(liblo.ServerThread):
    def __init__(self):
        # port is hardcoded for now
        liblo.ServerThread.__init__(self, 8000)
        self.dm = DeviceManager()

        self.ardour = Ardour(self.dm)
        self.dm.add_device(self.ardour)

        self.persist = PersistState()
        self.dm.add_device(self.persist)

        # IP is hardcoded for now
        self.touchosc = TouchOSC(self.dm, '192.168.137.62')
        self.dm.add_device(self.touchosc)

        self.start()

    @liblo.make_method(None, None)
    def got_message(self, path, args):
        print('Got message "{}" with arguments {}'.format(path, args))
        if path.startswith('/route/'):
            self.ardour.handle_osc(path, args)
        elif path.startswith('/oscar_page'):
            self.touchosc.handle_osc(path, args)
