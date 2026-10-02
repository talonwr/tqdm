import gc

from pytest import raises

from tqdm.notebook import tqdm as tqdm_notebook


def test_notebook_disabled_description():
    """Test that set_description works for disabled tqdm_notebook"""
    with tqdm_notebook(1, disable=True) as t:
        t.set_description("description")


def test_notebook_del_after_failed_init(monkeypatch):
    """`__del__` must not raise when `__init__` died before setting `disp`"""
    saved = []

    def status_printer(self, *_args, **_kwargs):
        saved.append(self)  # keep the half-built instance alive
        raise ImportError("IProgress not found")

    monkeypatch.setattr(tqdm_notebook, 'status_printer', status_printer)
    with raises(ImportError):
        tqdm_notebook(total=10, display=False)

    # `status_printer` runs unconditionally in `__init__`, so the instance exists
    assert len(saved) == 1
    saved[0].__del__()  # was: AttributeError ... has no attribute 'disp'
    del saved[:]
    gc.collect()  # and again at shutdown, now silently


def test_notebook_close_after_failed_init(monkeypatch):
    """`close()` must not raise when `__init__` died before setting `disp`"""
    def status_printer(self, *_args, **_kwargs):
        raise ImportError("IProgress not found")

    monkeypatch.setattr(tqdm_notebook, 'status_printer', status_printer)
    try:
        t = tqdm_notebook(total=10, display=False)
    except ImportError:
        t = next(obj for obj in gc.get_objects() if isinstance(obj, tqdm_notebook))
        t.close()  # was: AttributeError ... has no attribute 'disp'
    else:
        t.close()
