from unittest.mock import patch

import pytest

from app.core.config import settings
from app.modules.assistente import llm


def test_missing_api_key_fails_without_network(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    with patch("urllib.request.urlopen") as network:
        with pytest.raises(llm.LLMIndisponivelError):
            llm.build_default_client().chat([], [])
        network.assert_not_called()
