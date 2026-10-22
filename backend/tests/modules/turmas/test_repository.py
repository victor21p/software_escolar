from app.modules.turmas import repository
from tests.factories import make_turma


def test_empty_teacher_turma_filter_does_not_return_every_turma(db):
    make_turma(db)
    assert repository.list_turmas(db, turma_ids=[]) == []
