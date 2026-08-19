import pytest

pytestmark = pytest.mark.ui_heavy


def test_minimo_app(app):
    assert app is not None
