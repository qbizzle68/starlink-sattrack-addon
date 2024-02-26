# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2024-02-25

### Fixed

- Fixed poor dictionary updating mechanisms, reverting to Python's default `dict.update()` method.

## [0.1.4] - 2024-02-25

### Added

- Added Sattrack as an install dependency.
- Check if dependencies are importable during initialization and raise an `ImportError` if not.
- The configuration now contains the `PASS_BUFFER` value in the `defaults` section. This is used
to extend the set time of the previous satellite, to ensure a given satellite is still computed
within the satellite pass.

### Fixed

- Fixed an error that didn't properly set the 'defaults' table during re-configuration while using
the `updateConfig()` function.
- Fixed an issue where a train may still be split into two or more groups based on rise/set times of
each satellite's pass times. The new `PASS_BUFFER` configuration value is used to ensure individual
consecutive passes that aren't consecutively above the horizon are still considered in a single
satellite pass.

## [0.1.3] - 2024-02-12

### Added

- `MINIMUM_TRAIN_LENGTH` value (which defaults to 2) added to the `defaults` section of the
`starlinkConfig` dict.

### Fixed

- Issue when only a portion of a `StarlinkTrain`'s satellites are in the next pass. This occurs
at low altitude passes and the portion that don't rise are ignored for the current pass computations.
- Resolved a bug that would include all `StarlinkSatellites` in the first `GroupPlane` list of a 
`StarlinkBatch` that would also propagate to the first `StarlinkTrain` of the list.

## [0.1.2] - 2024-02-11

### Added

- `StarlinkPassFinder.computePassList()` function now implemented.

### Fixed

- `StarlinkBatch` objects now properly set their `satellites` attribute to a single list of
`StarlinkSatellite` objects, instead of a nested list of lists.

## [0.1.1] - 2024-02-10

### Added

- Added the `starlinkConfig` dict to the public API.
- Added ability to update the `starlinkConfig` dict with the `updateConfig()` function.
- Added the `getConfig()` function to reference the correct configuration.

### Removed

- Auto-importing of a `starlink-config.toml` configuration if present in the current
working directory.

## [0.1.0] - 2024-01-29

### Added

- Added `StarlinkBatch`, `GroupPlane`, and `StarlinkTrain` classes.

[Unreleased]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/qbizzle68/starlink-sattrack-extension/releases/tag/v0.1.0
