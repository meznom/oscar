import logging
import subprocess
import time

def discover_touchosc():
    log = logging.getLogger(__name__)
    try:
        p = subprocess.Popen(['avahi-browse',
                              '--ignore-local',
                              '--parsable',
                              '--resolve',
                              '--terminate',
                              '_osc._udp'],
                             stdout=subprocess.PIPE)
    except OSError:
        log.warning('Could not execute avahi-browse: is it installed?')
        return (None,None)

    timeout = 10
    t = 0
    while p.poll() is None:
        time.sleep(1)
        t += 1
        log.debug('Waiting for avahi-browse to finish')
        if t>timeout:
            log.warning('avahi-browse did not terminate within {} seconds: '
                        'aborting'.format(timeout))
            p.terminate()
            p.wait()
            return (None,None)
    if p.poll() != 0:
        log.warning('avahi-browse returned a non-zero exit code: aborting')
        return (None,None)

    stdout,stderr = p.communicate()
    fs = [s.split(';') for s in stdout.splitlines()]
    fs = filter(lambda l: l[0]=='=' and l[2]=='IPv4' and l[4]=='_osc._udp' and
                       l[3].count('TouchOSC')==1, fs)
    # f[7] and f[8] are ip and port
    rs = [(f[7],f[8]) for f in fs]
    if len(rs)==0:
        log.info('Could not find TouchOSC on the network via Zeroconf')
        return (None,None)
    if len(rs)>1:
        log.info('Found multiple TouchOSC on the network, will only use the '
                 'first one')
    log.info('Found TouchOSC on the network with ip {} and port '
             '{}'.format(*rs[0]))
    return rs[0]

class OscarService(object):
    def __init__(self, port=8000):
        self.log = logging.getLogger(__name__)
        self.port = port
        self.process = None

    def __del__(self):
        self.unpublish()

    def publish(self):
        try:
            self.process = subprocess.Popen(['avahi-publish',
                                             '--service',
                                             'oscar',
                                             '_osc._udp',
                                             str(self.port)])
            self.log.info('Announcing oscar via Zerconf on the network')
        except OSError:
            self.log.warning('Could not execute avahi-publish: is it installed?')

    def unpublish(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.process = None
