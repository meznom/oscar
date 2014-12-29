class DeviceManager(object):
    def __init__(self):
        self.ds = {}

    def add_device(self, device):
        self.ds[device.name] = device

    def __getattr__(self, method_name):
        def catchall_method(*args, **kwargs):
            ignore = None
            if kwargs.has_key('ignore'):
                ignore = kwargs['ignore']
                del kwargs['ignore']
            for name,device in self.ds.iteritems():
                if name == ignore:
                    continue
                if hasattr(device, method_name):
                    print('Calling {} for {}'.format(method_name, name))
                    f = getattr(device, method_name)
                    f(*args, **kwargs)
        return catchall_method
