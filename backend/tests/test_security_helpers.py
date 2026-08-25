from app.security import csrf_matches


def test_csrf_requires_both_values():
    assert csrf_matches("abc", "abc") is True
    assert csrf_matches("abc", "def") is False
    assert csrf_matches(None, "abc") is False
