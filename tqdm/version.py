"""`tqdm` version detector. Precedence: installed dist, git, 'UNKNOWN'."""
import os.path
import re
from importlib.metadata import PackageNotFoundError, version


def _git_version():
    """`git describe` as PEP 440 (e.g. `4.70.1.post2+ge15fafa`), else `None`"""
    from subprocess import DEVNULL, PIPE, CalledProcessError, run
    try:
        described = run(['git', 'describe', '--tags', '--long'],
                        cwd=os.path.dirname(os.path.dirname(__file__)),
                        stdout=PIPE, stderr=DEVNULL, text=True,
                        check=True).stdout.strip()
        tag, distance, commit = described.lstrip('v').rsplit('-', 2)
    except (CalledProcessError, OSError, ValueError):  # no git/repo/tags/garbage
        return None
    if not (re.match(r'\d+\.\d+\.\d+', tag) and distance.isdigit()
            and commit.startswith('g')):
        return None  # unparseable tag
    return f"{tag}.post{distance}+{commit}" if int(distance) else tag


try:
    __version__ = version('tqdm')
except PackageNotFoundError:
    __version__ = _git_version() or "UNKNOWN"
