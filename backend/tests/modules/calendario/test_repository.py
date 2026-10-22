from datetime import date

from app.modules.calendario import repository


def test_unknown_event_is_not_found(db):
    assert repository.get(db, 999999) is None
    assert repository.list_periodo(db, de=date(2020, 1, 1), ate=date(2020, 1, 2)) == []
