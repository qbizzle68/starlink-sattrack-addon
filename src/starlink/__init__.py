import os

from pathlib import Path

from .models.satellites import *
from .models.starlink import *
from .importers.tleimporter import *
from .passes import *
import starlink.config
from starlink.config import *


starlinkConfig = starlink.config.configImport.starlinkConfig
_currentWorkingDirectory = os.getcwd()
starlinkResource = Path(_currentWorkingDirectory).joinpath('starlink.tle')
if starlinkResource.exists():
    DefaultImporter = TLEFileImporter(starlinkResource)
else:
    DefaultImporter = None
