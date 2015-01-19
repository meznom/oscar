import liblo
import logging

class TouchOSC(object):
    def __init__(self, dm, ip, port=9000):
        self.log = logging.getLogger(__name__)
        self.name = 'touchosc'
        self.dm = dm

        # We manage the state ourselves, because we do not get feedback from
        # Ardour for play, stop, and recordglobal; obviously, this only
        # works as long as the user does not use the Ardour GUI
        self.state = {'playing': False, 'recording': False, 'removing': False}

        try:
            self.c = liblo.Address(ip, port)
        except liblo.AddressError, e:
            self.log.warning('Could not connect to TouchOSC.')
            self.c = None

    def sendosc(self, path, *args):
        pages = ['/oscar_page_1','/oscar_page_2','/oscar_page_3']
        if self.c is not None:
            for p in pages:
                liblo.send(self.c, p + path, *args)

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

    def vol(self, i, v):
        self.sendosc('/vol_{}'.format(i), v)

    def mute(self, i, v):
        self.sendosc('/mute_{}'.format(i), v)

    def solo(self, i, v):
        self.sendosc('/solo_{}'.format(i), v)

    def record(self, i, v):
        self.sendosc('/rec_{}'.format(i), v)

    def pan(self, i, v):
        self.sendosc('/pan_{}'.format(i), v)

    def send(self, i, j, v):
        self.sendosc('/send_{}_{}'.format(i, j), v)
