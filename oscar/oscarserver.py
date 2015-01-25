import liblo
import logging
import threading
from .devicemanager import DeviceManager
from .ardour import Ardour
from .persiststate import PersistState
from .touchosc import TouchOSC
from .zeroconf import OscarService

# TODO: It might be nice to interactively re-broadcast the current state
#       (e.g. for the case when TouchOSC is restarted or started late).

class OscarServer(liblo.ServerThread):
    def __init__(self, oscar_port=8000,
                 ardour_ip='127.0.0.1', ardour_port='3819',
                 touchosc_ip='127.0.0.1', touchosc_port='9000',
                 persist_state=True, state_file='oscar.state',
                 autosave=True, autosave_interval=60):
        liblo.ServerThread.__init__(self, oscar_port)
        self.log = logging.getLogger(__name__)
        self.os = OscarService(oscar_port)

        # Set up all devices: Ardour, PersistState and TouchOSC
        self.dm = DeviceManager()
        self.ardour = Ardour(self.dm, ardour_ip, ardour_port)
        self.dm.add_device(self.ardour)
        self.persist = PersistState(self.dm, state_file)
        self.dm.add_device(self.persist)
        self.touchosc = TouchOSC(self.dm, touchosc_ip, touchosc_port)
        self.dm.add_device(self.touchosc)

        # Set up the saver thread
        self.persist_state = persist_state
        self.autosave = persist_state and autosave
        self.saver_thread = None
        self.exit_saver_thread = None
        if self.autosave:
            self.saver_thread = threading.Thread(target=self.saver_thread_run,
                                                 args=(autosave_interval,))
            self.exit_saver_thread = threading.Event()

    def start(self):
        # While the saver_thread is running, self.persist.save must only be
        # called from the saver_thread.
        # Calling self.persist.save from a different thread (the saver_thread)
        # also assumes that updates to PersistState.state are atomic --- which
        # right now should be true (plus there's the global interpreter lock);
        # otherwise we might store an inconsistent state.
        self.os.publish()
        liblo.ServerThread.start(self)
        self.touchosc.start()
        self.ardour.start()
        if self.touchosc.ready() and self.ardour.ready():
            self.persist.restore()
        else:
            self.persist_state = False
            self.autosave = False
            self.log.warning('Ardour and TouchOSC are not ready: Not restoring '
                             'or saving state')
        if self.autosave:
            self.saver_thread.start()

    def stop(self):
        self.os.unpublish()
        liblo.ServerThread.stop(self)
        self.ardour.stop()
        self.touchosc.stop()
        if self.autosave:
            self.exit_saver_thread.set()
            self.saver_thread.join()
        if self.persist_state:
            self.persist.save()

    def saver_thread_run(self, autosave_interval):
        # Save every autosave_interval seconds, until we get the exit event
        while self.persist_state and not self.exit_saver_thread.wait(autosave_interval):
            self.persist.save()

    @liblo.make_method(None, None)
    def got_message(self, path, args):
        self.log.debug('Got message "{}" with arguments {}'.format(path, args))
        if path.startswith('/route/') or path.startswith('#reply'):
            self.ardour.handle_osc(path, args)
        elif path.startswith('/oscar_page'):
            self.touchosc.handle_osc(path, args)
