"""Tests for the human readable helpers."""

from importlib import util
from pathlib import Path


def _load_module():
    """Load ``Human_Format`` without importing the package."""

    module_path = Path(__file__).resolve().parents[1] / "tortoolkit" / "functions" / "Human_Format.py"
    spec = util.spec_from_file_location("Human_Format", module_path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hf = _load_module()


def test_human_readable_bytes():
    assert hf.human_readable_bytes(1024) == "1.00KiB"


def test_human_readable_timedelta():
    assert hf.human_readable_timedelta(90061) == "1d1h1m1s"
    assert hf.human_readable_timedelta(3661, precision=2) == "1h1m"


def test_human_readable_speed():
    assert hf.human_readable_speed(1024) == "1.00KiB/s"

