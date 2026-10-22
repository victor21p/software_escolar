from app.core.roles import Role
from app.modules.matricula import permissions
from app.modules.matricula.schemas import StatusMatricula


def test_families_cannot_approve_or_cancel_after_analysis():
    assert Role.RESPONSAVEL not in permissions.CAN_REVIEW
    assert StatusMatricula.EM_ANALISE not in permissions.RESPONSAVEL_CAN_CANCEL_FROM
    assert not permissions.is_staff(Role.ALUNO)
