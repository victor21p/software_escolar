from datetime import date

from app.modules.frequencia import repository


def test_unknown_student_has_empty_attendance_history(db):
    assert repository.list_by_aluno_periodo(db, 999999, date.today(), date.today()) == []
