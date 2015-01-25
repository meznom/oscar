import liblo
import logging
import time

# At least at the moment, with Ardour 3.5.403, controlling plugin parameters via
# OSC seems to crash Ardour. E.g.
# s.ardour.sendosc('/ardour/routes/plugin/parameter/print', 5, 1, 1)
# or
# s.ardour.sendosc('/ardour/routes/plugin/parameter', 5, 1, 1, 0.1)

class Ardour(object):
    def __init__(self, dm, ip='127.0.0.1', port=3819):
        self.log = logging.getLogger(__name__)
        self.name = 'ardour'
        self.master_id = 318
        self.n_tracks = 12
        # The Ardour bus ids. This is hardcoded for now. 318 is the master bus.
        self.ids = range(1,self.n_tracks+1) + [self.master_id]
        self.dm = dm
        self.ip = ip
        self.port = port
        self.c = None
        self.is_ready = False

    def __del__(self):
        self.stop_listening_to_feedback()

    def sendosc(self, path, *args):
        if self.c is not None:
            liblo.send(self.c, path, *args)

    def handle_osc(self, path, args):
        if path.startswith('#reply'):
            self.is_ready = True
            return
        if not path.startswith('/route/'):
            return
        segments = path.strip(' /').split('/')
        if len(segments) != 2:
            return
        control = segments[1]

        if len(args) != 2:
            return
        i = int(args[0])
        v = float(args[1])

        i = self._convert_from_ardour_id(i)

        if control == 'gain':
            self.log.debug('got {} {} {:.2f}'.format('gain', i, v))
            self.dm.vol(i, v, ignore=self.name)
        elif control == 'mute':
            self.log.debug('got {} {} {}'.format('mute', i, v))
            self.dm.mute(i, v, ignore=self.name)
        elif control == 'solo':
            self.log.debug('got {} {} {}'.format('solo', i, v))
            self.dm.solo(i, v, ignore=self.name)
        elif control == 'rec':
            self.log.debug('got {} {} {}'.format('rec', i, v))
            self.dm.record(i, v, ignore=self.name)
        # Note: I do not know how to get feedback for changes in ardour to sends
        # and pan; so this only works in one direction (TouchOSC -> Ardour) for
        # now

    def start(self):
        self.is_ready = False
        try:
            self.c = liblo.Address(self.ip, self.port)
        except liblo.AddressError, e:
            self.log.error('Could not connect to Ardour.')
            return

        timeout = 60
        t = 0
        while not self.is_ready:
            self.sendosc('/routes/listen', *self.ids)
            self.log.info('Waiting for feedback from Ardour')
            time.sleep(1)
            t += 1
            if t>timeout:
                self.log.error('I did not hear back from Ardour for {} '
                               'seconds, giving up'.format(timeout))
                return
        self.log.info('Ardour is ready')

    def stop(self):
        self.sendosc('/routes/ignore', *self.ids)
        self.is_ready = False
        self.c = None

    def ready(self):
        return self.is_ready

    def vol(self, i, v):
        i = self._convert_to_ardour_id(i)
        self.sendosc('/ardour/routes/gainabs', i, v)

    def mute(self, i, v):
        i = self._convert_to_ardour_id(i)
        self.sendosc('/ardour/routes/mute', i, v)

    def solo(self, i, v):
        i = self._convert_to_ardour_id(i)
        self.sendosc('/ardour/routes/solo', i, v)

    def record(self, i, v):
        i = self._convert_to_ardour_id(i)
        self.sendosc('/ardour/routes/recenable', i, v)

    def pan(self, i, v):
        i = self._convert_to_ardour_id(i)
        self.sendosc('/ardour/routes/pan_stereo_position', i, v)

    def send(self, i, j, v):
        i = self._convert_to_ardour_id(i)
        self.sendosc('/ardour/routes/send/gainabs', i, j, v)

    def play(self):
        self.sendosc('/ardour/transport_play')

    def stop(self):
        self.sendosc('/ardour/transport_stop')

    def recordglobal(self):
        self.sendosc('/ardour/rec_enable_toggle')

    def rewind(self):
        self.sendosc('/ardour/prev_marker')

    def forward(self):
        self.sendosc('/ardour/next_marker')

    def addmarker(self):
        self.sendosc('/ardour/add_marker')

    def undo(self):
        self.sendosc('/ardour/undo')

    def redo(self):
        self.sendosc('/ardour/redo')

    def remove_all_regions_on_track(self, i):
        # This might be pretty fragile and at any rate is very tightly coupled
        # to the Ardour template / layout of tracks
        if i<1 or i>self.n_tracks:
            return
        self.sendosc('/ardour/access_action', 'Editor/deselect-all')
        for j in range(i+1):
            self.sendosc('/ardour/access_action', 'Editor/select-next-route')
        self.sendosc('/ardour/access_action', 'Editor/select-all')
        self.sendosc('/ardour/access_action', 'Region/remove-region')
        self.sendosc('/ardour/access_action', 'Editor/deselect-all')

    def _convert_to_ardour_id(self, i):
        if i==0:
            return self.master_id
        else:
            return i

    def _convert_from_ardour_id(self, i):
        if i==self.master_id:
            return 0
        else:
            return i
