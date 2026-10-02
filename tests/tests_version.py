import re
from ast import literal_eval
from subprocess import CalledProcessError, TimeoutExpired  # nosec

from pytest import mark, skip

from tqdm import __version__


def test_version():
    version_parts = re.split('[.-]', __version__)
    if __version__ != "UNKNOWN":
        assert 3 <= len(version_parts), "must have at least Major.minor.patch"
        assert all(
            isinstance(literal_eval(i), int) for i in version_parts[:3]
        ), "Version Major.minor.patch must be 3 integers"


@mark.parametrize("described, expected", [
    ("v4.70.1-0-gdeadbee", "4.70.1"),
    ("v4.70.1-2-gdeadbee", "4.70.1.post2+gdeadbee"),
    ("v4.70.1", None),  # no `--long` suffix
    ("release-4.70.1-2-gdeadbee", None),  # unparseable tag
    ("v4.70.0-rc1-2-gdeadbee", None),  # tag prefix is PEP 440, remainder is not
    ("v4.70.0.dev1-2-gdeadbee", None),  # ditto: `4.70.0.dev1.post2` is not PEP 440
    ("nonsense", None),
])
def test_version_git_describe(described, expected):
    """`git describe` output => PEP 440 version (None if unusable)"""
    from unittest.mock import Mock, patch

    from tqdm.version import _git_version

    with patch('subprocess.run', return_value=Mock(stdout=described + '\n')):
        assert _git_version() == expected


def test_version_git_no_repo():
    """`git describe` failure (no git/repo/tags) => fall through to 'UNKNOWN'"""
    from unittest.mock import patch

    from tqdm.version import _git_version

    with patch('subprocess.run', side_effect=CalledProcessError(128, 'git')):
        assert _git_version() is None


@mark.parametrize("exc", [
    FileNotFoundError(2, 'No such file or directory', 'git'),  # git not on PATH
    PermissionError(13, 'Permission denied', 'git'),
    TimeoutExpired('git', 5),  # hung => must not block import
])
def test_version_git_unavailable(exc):
    """git missing/denied/hung => `None` rather than raising at import time"""
    from unittest.mock import patch

    from tqdm.version import _git_version

    with patch('subprocess.run', side_effect=exc):
        assert _git_version() is None


def test_version_git_fallback():
    """uninstalled tqdm in a git checkout => version, not 'UNKNOWN' (issue #5)"""
    from importlib.metadata import PackageNotFoundError, version

    from tqdm.version import _git_version

    git_version = _git_version()
    if git_version is None:  # e.g. no git installed, or no tags
        skip("not a tagged git checkout")
    try:
        assert __version__ == version('tqdm')  # installed dist takes precedence
    except PackageNotFoundError:
        assert __version__ == git_version  # else git, else 'UNKNOWN'
