import logging
import argparse
from oscar import OscarServer

def main():
    # Command line arguments
    p = argparse.ArgumentParser()
    p.add_argument('--debug', help='Print debug output', action='store_true')
    p.add_argument('--touchosc-ip', default='127.0.0.1',
                   help='IP address of TouchOSC (default: 127.0.0.1)')
    p.add_argument('--touchosc-port', default='9000',
                   help='Port of TouchOSC (default: 9000)')
    p.add_argument('--ardour-ip', default='127.0.0.1',
                   help='IP address of Ardour (default: 127.0.0.1)')
    p.add_argument('--ardour-port', default='3819',
                   help='Port of Ardour (default: 3819)')
    p.add_argument('--oscar-port', default='8000',
                   help='Port we are listening on (default: 8000)')
    args = p.parse_args()

    # Configure logging
    log_formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(log_formatter)
    log = logging.getLogger('oscar')
    log.addHandler(log_handler)
    if args.debug:
       log.setLevel(logging.DEBUG)
    else:
       log.setLevel(logging.INFO)

    # Run oscar server
    s = OscarServer(touchosc_ip=args.touchosc_ip,
                    touchosc_port=args.touchosc_port,
                    ardour_ip=args.ardour_ip,
                    ardour_port=args.ardour_port,
                    oscar_port=args.oscar_port)
    s.start()
    while True:
        k = raw_input('Press q to quit.\n')
        if k == 'q':
            break
    s.stop()

if __name__ == '__main__':
    main()
