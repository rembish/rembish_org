# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## Changed
- Moved back to MySQL, because Digital Ocean provides it as a service

## [0.7.1] - 2020-11-24
### Fixed
- Minor layout tweaks

## [0.7.0] - 2020-11-24
### Changed
- Flights and drones are splat into two different modules
- Moving flight statistics to flight map page

### Added
- Flight map
- Extended flight stats

## [0.6.4] - 2020-11-23
### Fixed
- Problem with flags fixed

## [0.6.3] - 2020-11-23
### Added
- Debugging nginx docker in pipeline :(

## [0.6.2] - 2020-11-23
### Fixing
- More typos in nginx dockerfile

## [0.6.1] - 2020-11-23
### Fixing
- Typo in nginx dockerfile

## [0.6.0] - 2020-11-23
### Added
- Flight log added
- New flight page added
- Complete drone/flights models
- Take-off time helpers
- Countries with flags added

### Changed
- I can obtain user's name and email from Google

## [0.5.2] - 2020-10-26
### Fixing
- Downgrading `node` image, because of https://github.com/nodejs/docker-node/issues/1379.

## [0.5.1] - 2020-10-26
### Fixing
- `flask version` command didn't change URL in Changelog footer
- `npm cache clean --force` added to nginx image

## [0.5.0] - 2020-10-26
### Added
- `flask version` command to work with current app version
- MySQL database added
- Login/logout added

### Fixing
- Table `users_roles` doesn't have PK

## [0.4.0] - 2020-10-21
### Added
- Very early work experience added

### Changed
- Resume replaced by CV
- /contact/email is now /contact/message (it doesn't send any email)
- Download a PDF is highlighted now

### Fixed
- JS console output suspended

## [0.3.2] - 2020-10-20
### Fixed
- Dummy hero photo replaced with actual one

## [0.3.1] - 2020-10-20
### Added
- Standard configuration propagation from ENV variables

### Fixed
- Forgotten SECRET_KEY for production

## [0.3.0] - 2020-10-20
### Added
- Typed on Hero page
- Working contact page form (using Telegram bot)
- Secrets file added (mustn't be committed)

### Fixed
- Empty favicons are replaced with AR icon

## [0.2.0] - 2020-10-20
### Added
- Changelog.md created for further changes tracking
- License added
- Changelog page created

### Changed
- Footer is now showing the relevant information about copyrights and licenses

### Fixed
- Keybase.io auth file was forgotten

## [0.1.0] - 2020-10-19
### Added
- Basic project structure
- Simple containerization
- CD based on GitHub Actions

[Unreleased]: https://github.com/rembish/rembish_org/compare/v0.7.1...HEAD
[0.7.1]: https://github.com/rembish/rembish_org/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/rembish/rembish_org/compare/v0.6.4...v0.7.0
[0.6.4]: https://github.com/rembish/rembish_org/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/rembish/rembish_org/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/rembish/rembish_org/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/rembish/rembish_org/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/rembish/rembish_org/compare/v0.5.2...v0.6.0
[0.5.2]: https://github.com/rembish/rembish_org/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/rembish/rembish_org/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/rembish/rembish_org/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/rembish/rembish_org/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/rembish/rembish_org/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/rembish/rembish_org/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/rembish/rembish_org/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rembish/rembish_org/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rembish/rembish_org/releases/tag/v0.1.0
