from dataclasses import FrozenInstanceError

import pytest

from app.shared.events import MatriculaAprovada
from app.shared.serie import Serie


def test_domain_event_is_immutable():
    event = MatriculaAprovada(1, 2, Serie.ANO_3, 2026)
    field = "aluno_id"
    with pytest.raises(FrozenInstanceError):
        setattr(event, field, 3)
