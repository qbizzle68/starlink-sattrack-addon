import tomllib
from importlib.resources import files

RAAN_STDEV_OUTLIER_DEFAULT = 1.25
MAXIMUM_TRAIN_GAP_DEFAULT = 5
MAXIMUM_TRAIN_HEIGHT_DEFAULT = 350


def _importConfig(overridePath=None) -> dict:
    if overridePath:
        configPath = overridePath
    else:
        configPath = files('starlink.config').joinpath('starlink-config.toml')

    with open(configPath, 'rb') as toml:
        starlinkConfig = tomllib.load(toml)

    if starlinkConfig.get('RAAN_STDEV_OUTLIER') is None:
        starlinkConfig['RAAN_STDEV_OUTLIER'] = RAAN_STDEV_OUTLIER_DEFAULT
    if starlinkConfig.get('MAXIMUM_TRAIN_GAP') is None:
        starlinkConfig['MAXIMUM_TRAIN_GAP'] = MAXIMUM_TRAIN_GAP_DEFAULT
    if starlinkConfig.get('MAXIMUM_TRAIN_HEIGHT') is None:
        starlinkConfig['MAXIMUM_TRAIN_HEIGHT'] = MAXIMUM_TRAIN_HEIGHT_DEFAULT

    return starlinkConfig
