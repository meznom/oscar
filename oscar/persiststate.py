import logging
import copy
import os
import json

# TODO: save state to state file periodically
# TODO: also "restore" settings when we don't actually load anything from a
#       file? (so that ardour and touchosc are in a consistent state...)

class PersistState(object):
    def __init__(self, dm, state_file='oscar.state'):
        self.log = logging.getLogger(__name__)
        self.name = 'persiststate'
        self.dm = dm
        self.state_file = state_file
        self.n_tracks = 12 # probably should be a global property
        track_state = {'vol': 1.0, 'mute': 0.0, 'solo': 0.0, 'record': 0.0,
                       'pan': 0.5, 'send': [1.0]}
        self.state = [copy.deepcopy(track_state) for i in range(self.n_tracks + 1)]

    def save(self):
        if self.state_file is None:
            return
        with open(self.state_file, 'w') as f:
            # TODO: should save oscar version as well
            d = {'tracks': self.state, '__info__': 'Oscar state file'}
            json.dump(d, f, indent=2)
            self.log.debug('Saved state to file "{}"'.format(self.state_file))

    def restore(self):
        # Open file if it exists and parse json
        if self.state_file is None:
            return
        if not os.path.isfile(self.state_file):
            self.log.info('Oscar state file "{}" does not exist '
                          '--- no settings to restore'.format(self.state_file))
            return
        with open(self.state_file, 'r') as f:
            d = json.load(f)

        # Read contents of file to self.state; basic validity check on the
        # read data structure
        valid = True
        if d.has_key('tracks'):
            for i,t in enumerate(self.state):
                if i<len(d['tracks']):
                    t_ = d['tracks'][i]
                    for k in t.keys():
                        if t_.has_key(k):
                            t[k] = t_[k]
                        else:
                            valid = False
        else:
            valid = False

        if not valid:
            self.log.warning('Could not restore state: Invalid state file '
                             '""'.format(self.state_file))
            return

        # "Broadcast" the read settings to all devices via the device manager,
        # i.e. actually restore the settings to Ardour and TouchOSC
        for i,t in enumerate(self.state):
            for k,v in t.iteritems():
                f = getattr(self.dm, k)
                if k == 'send':
                    f(i,1,v,ignore=self.name)
                else:
                    f(i,v,ignore=self.name)
        self.log.info('Restored settings from file "{}"'.format(self.state_file))

    def __getattr__(self, method_name):
        def wrapper_method(i, v):
            if i>=0 and i<=self.n_tracks and type(v) == float:
                self.state[i][method_name] = v
            else:
                self.log.warning('Invalid arguments for method {}: '
                                 '{} {}'.format(method_name, i, v))
            self.log.debug('State: \n{}'.format(str(self)))
        methods = ['vol', 'mute', 'solo', 'record', 'pan']
        if method_name in methods:
            return wrapper_method

    def send(self, i, j, v):
        if i>=0 and i<=self.n_tracks and j==1 and type(v) == float:
            self.state[i]['send'][0] = v
        self.log.debug('State: \n{}\n'.format(str(self)))

    def __str__(self):
        s = ''
        for i,t in enumerate(self.state):
            ss = ['{}: {:.2f}'.format(k,v) for k,v in t.iteritems() if type(v) == float]
            ss.append('send_1: {:.2f}'.format(t['send'][0]))
            s += 'Track {}. '.format(i) + ' '.join(ss) + '\n'
        return s[:-1]
