from src.services import _times_overlap


def test_times_overlap_exact_same():
    assert _times_overlap("10:00", "11:15", "10:00", "11:15") is True


def test_times_overlap_partial_start():
    # 10:30 is between 10:00 and 11:30
    assert _times_overlap("10:00", "11:30", "10:30", "12:00") is True


def test_times_overlap_partial_end():
    # 09:30-10:30 overlaps with 10:00-11:00
    assert _times_overlap("10:00", "11:00", "09:30", "10:30") is True


def test_times_overlap_enclosing():
    # One interval completely inside another
    assert _times_overlap("09:00", "13:00", "10:00", "11:00") is True
    assert _times_overlap("10:00", "11:00", "09:00", "13:00") is True


def test_times_no_overlap_before():
    assert _times_overlap("08:00", "09:00", "10:00", "11:00") is False


def test_times_no_overlap_after():
    assert _times_overlap("11:00", "12:00", "09:00", "10:00") is False


def test_times_no_overlap_adjacent():
    # When one class ends exactly when another begins (10:00), max("09:00", "10:00") is "10:00"
    # min("10:00", "11:00") is "10:00". "10:00" < "10:00" is False -> No overlap.
    assert _times_overlap("09:00", "10:00", "10:00", "11:00") is False
