# flake8: noqa
import os
from .settings import *
try:
    from .localsettings import *
except ImportError:
    pass
