import os

_dependencies = ('sattrack', 'pyevspace', 'requests')
_missingImports = []
for _package in _dependencies:
    try:
        __import__(_package)
    except ImportError as e:
        _missingImports.append(f'{_package}: {e}')

if _missingImports:
    error = 'Unable to import dependencies:\n' + '\n'.join(_missingImports)
    raise ImportError(error)

del _dependencies, _missingImports, _package

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
