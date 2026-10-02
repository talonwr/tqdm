from ast import literal_eval
from collections import defaultdict
from typing import Union  # py<3.10

from pytest import mark, warns

from tqdm.utils import envwrap


def test_envwrap_deprecated(monkeypatch):
    monkeypatch.setenv('FUNC_A', "42")
    monkeypatch.setenv('FUNC_TyPe_HiNt', "1337")
    monkeypatch.setenv('FUNC_Unused', "x")

    with warns(DeprecationWarning, match="Trailing underscore in `name` is automatic"):
        @envwrap("FUNC_")
        def func(a=1, b=2, type_hint: int = None):
            return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap(monkeypatch):
    monkeypatch.setenv('NAME_FUNC_A', "42")
    monkeypatch.setenv('NAME_TyPe_HiNt', "1337")
    monkeypatch.setenv('NAME_unused', "x")

    @envwrap("name", "func")
    def func(a=1, b=2, type_hint: int = None):
        return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap_types(monkeypatch):
    monkeypatch.setenv('FUNC_notype', "3.14159")

    @envwrap("func", types=defaultdict(lambda: literal_eval))
    def func(notype=None):
        return notype

    assert 3.14159 == func()

    monkeypatch.setenv('FUNC_number', "1")
    monkeypatch.setenv('FUNC_string', "1")

    @envwrap("func", types={'number': int})
    def nofallback(number=None, string=None):
        return number, string

    assert 1, "1" == nofallback()


def test_envwrap_annotations(monkeypatch):
    monkeypatch.setenv('FUNC_number', "1.1")
    monkeypatch.setenv('FUNC_string', "1.1")

    @envwrap("func")
    def annotated(number: Union[int, float] = None, string: int = None):
        return number, string

    assert 1.1, "1.1" == annotated()


def test_envwrap_unparsable(monkeypatch):
    """unparsable values should be ignored, not raise (#2)"""
    monkeypatch.setenv('FUNC_number', "abc")
    monkeypatch.setenv('FUNC_default', "abc")

    @envwrap("func", types={'number': int})
    def func(number=None, default=1.0):
        return number, default

    assert (None, 1.0) == func()


@mark.parametrize("val,expected", [
    ("true", True), ("True", True), ("1", True), ("yes", True), ("on", True),
    ("false", False), ("False", False), ("0", False), ("no", False), ("off", False),
    ("", False)])
def test_envwrap_bool(monkeypatch, val, expected):
    """`bool('False')` is True, so booleans must be parsed as words (#12)"""
    monkeypatch.setenv('FUNC_enabled', val)
    monkeypatch.setenv('FUNC_left', val)

    @envwrap("func")
    def func(enabled=False, left=True):
        return enabled, left

    assert (expected, expected) == func()


def test_envwrap_bool_unparsable(monkeypatch):
    """unparsable booleans fall back to the default, like any other type (#12)"""
    monkeypatch.setenv('FUNC_enabled', "banana")

    @envwrap("func")
    def func(enabled=False):
        return enabled

    assert func() is False


def test_envwrap_bool_or_str(monkeypatch):
    """boolean words are parsed, anything else stays a `str` (`ascii` charset) (#12)"""
    from tqdm.utils import _env_bool_or_str

    monkeypatch.setenv('FUNC_charset', "False")
    monkeypatch.setenv('FUNC_custom', " .oO0")

    @envwrap("func", types={'charset': _env_bool_or_str, 'custom': _env_bool_or_str})
    def func(charset=None, custom=None):
        return charset, custom

    assert (False, " .oO0") == func()
