# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2024-02-10

### Added

- Added the starlinkConfig dict to the public API.
- Added ability to update the starlinkConfig dict with the updateConfig() function.
- Added the getConfig() function to reference the correct configuration.

### Removed

- Auto-importing of a 'starlink-config.toml' configuration if present in the current
working directory.

## [0.1.0] - 2024-01-29

### Added

- Added StarlinkBatch, GroupPlane, and StarlinkTrain classes.

[Unreleased]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/qbizzle68/starlink-sattrack-extension/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/qbizzle68/starlink-sattrack-extension/releases/tag/v0.1.0
