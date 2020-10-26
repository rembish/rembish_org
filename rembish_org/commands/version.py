from datetime import date
from json import load as json_load, dump as json_dump

from click import command, option, Choice, echo

from ..version import __version__ as current_version


@command()
@option("-i", "--increment", type=Choice(["patch", "minor", "major"]), help="Increment to next version")
def version(increment):
    """
        Project version manipulations.
        Returns back current version if increment wasn't sent.
    """
    # Those packages don't be available on production.
    from semver import VersionInfo
    from toml import load as toml_load, dump as toml_dump

    if not increment:
        return echo(current_version)

    previous = VersionInfo.parse(current_version)
    new = getattr(previous, f"bump_{increment}")()

    with open("rembish_org/version.py", "w") as fd:
       fd.write(f"__version__ = '{new}'")

    pyproject = toml_load("pyproject.toml")
    pyproject["tool"]["poetry"]["version"] = str(new)
    with open("pyproject.toml", "w") as fd:
       toml_dump(pyproject, fd)

    with open("package.json", "r") as fd:
        data = json_load(fd)
        data["version"] = str(new)

    with open("package.json", "w") as fd:
        json_dump(data, fd, indent=2)

    with open("CHANGELOG.md", "r") as fd:
        changelog = fd.read()

    today = date.today().strftime("%Y-%m-%d")
    changelog = changelog.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{new}] - {today}")
    changelog = changelog.replace(
        f"[Unreleased]: https://github.com/rembish/rembish_org/compare/v{previous}",
        f"[Unreleased]: https://github.com/rembish/rembish_org/compare/v{new}")
    changelog = changelog.replace(
        "...HEAD",
        f"...HEAD\n[{new}]: https://github.com/rembish/rembish_org/compare/v{previous}...v{new}")

    with open("CHANGELOG.md", "w") as fd:
        fd.write(changelog)

    return echo(new)
