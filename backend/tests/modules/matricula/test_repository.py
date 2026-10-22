from app.modules.matricula import repository
from tests.factories import make_aluno, make_matricula, make_turma


def test_empty_family_filter_returns_no_matriculas(db):
    make_matricula(db, make_aluno(db), make_turma(db))
    assert repository.list_matriculas(db, aluno_ids=[])[1] == 0
