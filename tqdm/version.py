"""`tqdm` version detector. Precedence: installed dist, git, 'UNKNOWN'.

`git` is only invoked when no installed dist is found (i.e. a source
checkout), and only once per process: `__version__` is computed at import
and thereafter served from memory.
"""
import os.path
import re
from importlib.metadata import PackageNotFoundError, version


def _git_version():
    """`git describe` as PEP 440 (e.g. `4.70.1.post2+ge15fafa`), else `None`"""
    from subprocess import DEVNULL, PIPE, CalledProcessError, TimeoutExpired, run
    try:
        described = run(['git', 'describe', '--tags', '--long'],
                        cwd=os.path.dirname(os.path.dirname(__file__)),
                        stdout=PIPE, stderr=DEVNULL, text=True,
                        check=True, timeout=5).stdout.strip()
        tag, distance, commit = described.lstrip('v').rsplit('-', 2)
    except (CalledProcessError, OSError, TimeoutExpired, ValueError):
        # no git/not on PATH/not a repo/no tags/garbage output/slow/hung
        return None
    if not (re.fullmatch(r'\d+\.\d+\.\d+', tag) and distance.isdigit()
            and commit.startswith('g')):
        return None  # unparseable or non-PEP 440 tag
    return f"{tag}.post{distance}+{commit}" if int(distance) else tag


try:
    __version__ = version('tqdm')
except PackageNotFoundError:
    __version__ = _git_version() or "UNKNOWN"
