import liblo
import logging
from .zeroconf import discover_touchosc

class TouchOSC(object):
    def __init__(self, dm, ip='zeroconf', port=9000):
        self.log = logging.getLogger(__name__)
        self.name = 'touchosc'
        self.c = None
        self.dm = dm
        self.ip = ip
        self.port = port
        self.is_ready = False

        self.n_tracks = 12
        self.tracks_per_page = 4
        self.pages = ['/oscar_page_1','/oscar_page_2','/oscar_page_3']

        # We manage the state ourselves, because we do not get feedback from
        # Ardour for play, stop, and recordglobal; obviously, this only
        # works as long as the user does not use the Ardour GUI
        self.state = {'playing': False, 'recording': False, 'removing': False}

    def sendosc(self, pagenumber, path, *args):
        if self.c is None:
            return
        if pagenumber is None:
            return
        page = self.pages[pagenumber]
        liblo.send(self.c, page + path, *args)

    def pagenumber(self, tracknumber):
        i = tracknumber
        if i<1 or i>self.n_tracks:
            return None
        return (i-1) // self.tracks_per_page

    def handle_osc(self, path, args):
        if not path.startswith('/oscar_page'):
           return
        segments = path.strip(' /').split('/')
        if len(segments) != 2:
            return

        subsegments = segments[1].split('_')
        if len(subsegments) < 1:
            return
        control = subsegments[0]
        try:
            control_args = [int(s) for s in subsegments[1:]]
        except ValueError:
            return

        i = 0
        j = 0
        v = 0.0
        if len(control_args)>0:
            i = control_args[0]
        if len(control_args)>1:
            j = control_args[1]
        if len(args) > 0:
            v = float(args[0])

        if control == 'vol':
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
        elif control == 'pan':
            self.log.debug('got {} {} {}'.format('pan', i, v))
            self.dm.pan(i, v, ignore=self.name)
        elif control == 'send':
            self.log.debug('got {} {} {} {:.2f}'.format('send', i, j, v))
            self.dm.send(i, j, v, ignore=self.name)
        elif control == 'play' and v == 1.0:
            self.log.debug('got play')
            self.dm.play(ignore=self.name)
            self.state['playing'] = True
            self.sendosc('/play', 1.0)
        elif control == 'stop' and v == 1.0:
            self.log.debug('got stop')
            self.dm.stop(ignore=self.name)
            self.state['playing'] = False
            if self.state['recording']:
                self.state['recording'] = False
            self.sendosc('/play', 0.0)
            self.sendosc('/recordglobal', float(self.state['recording']))
        elif control == 'recordglobal' and v == 1.0:
            self.log.debug('got recordglobal')
            self.dm.recordglobal(ignore=self.name)
            self.state['recording'] = not self.state['recording']
            self.sendosc('/recordglobal', float(self.state['recording']))
        elif control == 'rewind' and v == 1.0:
            self.log.debug('got rewind')
            self.dm.rewind(ignore=self.name)
        elif control == 'forward' and v == 1.0:
            self.log.debug('got forward')
            self.dm.forward(ignore=self.name)
        elif control == 'addmarker' and v == 1.0:
            self.log.debug('got addmarker')
            self.dm.addmarker(ignore=self.name)
        elif control == 'undo' and v == 1.0:
            self.log.debug('got undo')
            self.dm.undo(ignore=self.name)
        elif control == 'redo' and v == 1.0:
            self.log.debug('got redo')
            self.dm.redo(ignore=self.name)
        elif control == 'removeglobal':
            self.log.debug('got {} {}'.format('removeglobal', v))
            if v == 1.0:
                self.state['removing'] = True
            elif v == 0.0:
                self.state['removing'] = False
        elif control == 'remove' and v == 1.0:
            self.log.debug('got {} {}'.format('remove', i))
            if self.state['removing']:
                self.dm.remove_all_regions_on_track(i)

    def start(self):
        self.is_ready = False
        if self.ip=='zeroconf':
            ip_,port_ = discover_touchosc()
            if ip_ is not None and port_ is not None:
                self.ip = ip_
                self.port = port_
            else:
                self.log.error('Could not discover TouchOSC on the network '
                               'with Zeroconf. Please make sure TouchOSC is '
                               'running. Alternatively, explicitely provide '
                               'TouchOSC\'s IP address.')
                return
        try:
            self.c = liblo.Address(self.ip, self.port)
        except liblo.AddressError, e:
            self.log.error('Could not connect to TouchOSC.')
            return
        self.is_ready = True

    def stop(self):
        self.is_ready = False
        self.c = None

    def ready(self):
        # For TouchOSC, is_ready only says whether we managed to open the network
        # connection. It seems there is no way to know whether TouchOSC is
        # actually there or not. Hence we assume it is always ready. (There is
        # the ping option, which sends a /ping message, but only every 60
        # seconds which is too long to wait to start up oscar.)
        return self.is_ready

    def vol(self, i, v):
        self.sendosc(self.pagenumber(i), '/vol_{}'.format(i), v)

    def mute(self, i, v):
        self.sendosc(self.pagenumber(i), '/mute_{}'.format(i), v)

    def solo(self, i, v):
        self.sendosc(self.pagenumber(i), '/solo_{}'.format(i), v)

    def record(self, i, v):
        self.sendosc(self.pagenumber(i), '/rec_{}'.format(i), v)

    def pan(self, i, v):
        self.sendosc(self.pagenumber(i), '/pan_{}'.format(i), v)

    def send(self, i, j, v):
        self.sendosc(self.pagenumber(i), '/send_{}_{}'.format(i, j), v)
