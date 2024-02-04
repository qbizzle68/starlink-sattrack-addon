import os
# import tomllib

# from importlib.resources import files
from pathlib import Path

# check the current working directory for a starlink-config.toml file
from .config import _importConfig

_currentWorkingDirectory = os.getcwd()
# _tmpPath = Path(_currentWorkingDirectory).joinpath('config/starlink-config.toml')
_tmpPath = Path(_currentWorkingDirectory).joinpath('starlink-config.toml')
# if _tmpPath.exists():
#     _configPath = _tmpPath
# else:
#     # todo: change this to actual package name when this is installed
#     with files('starlink').joinpath('config/starlink-config.toml') as file:
#         _configPath = file
#
# with open(_configPath, 'rb') as toml:
#     _starlinkConfig = tomllib.load(toml)
_overridePath = _tmpPath if _tmpPath.exists() else None
_starlinkConfig = _importConfig(_overridePath)

# check if the updated time exists in config dict and if they don't match update from server

from .models.satellites import *
from .models.starlink import *
from .importers.tleimporter import *
from .passes import *

starlinkResource = Path(_currentWorkingDirectory).joinpath('starlink.tle')
if starlinkResource.exists():
    DefaultImporter = TLEFileImporter(starlinkResource)
else:
    DefaultImporter = None
