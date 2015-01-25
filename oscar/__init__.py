__version__ = 'unknown'

try:
    from ._version import __version__
except ImportError:
    pass

from .oscarserver import OscarServer
from .__main__ import main
