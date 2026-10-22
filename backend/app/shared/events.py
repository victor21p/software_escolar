"""Eventos imutáveis trocados entre matrícula e financeiro."""

from dataclasses import dataclass

from app.shared.serie import Serie


@dataclass(frozen=True)
class MatriculaAprovada:
    matricula_id: int
    aluno_id: int
    serie: Serie
    ano_letivo: int


@dataclass(frozen=True)
class CobrancaPaga:
    cobranca_id: int
    aluno_id: int
    matricula_id: int | None = None
    tipo: str = ""
