from app.modules.notas import repository
from app.modules.notas.models import Nota
from app.modules.notas.schemas import Periodo
from tests.factories import make_aluno, make_turma


def test_empty_year_turma_filter_does_not_leak_other_year_grades(db):
    aluno, turma = make_aluno(db), make_turma(db)
    db.add(
        Nota(
            aluno_id=aluno.id,
            turma_id=turma.id,
            disciplina="Artes",
            periodo=Periodo.BIMESTRE_1,
            valor=8,
            lancado_por_user_id=1,
        )
    )
    db.flush()
    assert repository.list_notas_aluno(db, aluno.id, []) == []
