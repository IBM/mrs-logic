import logging
import sys

from . import UKB

logging.basicConfig(level=logging.INFO)

if len(sys.argv) < 2 or sys.argv[1] not in {'start', 'stop'}:
    print(f'usage: {__package__} [start|stop]')
    sys.exit(1)
if sys.argv[1] == 'start':
    UKB._server_start()
else:
    UKB._server_stop()
