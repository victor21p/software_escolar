from app.modules.assistente import service


def test_tool_results_are_bounded_before_sending_to_model():
    result = service._texto_resultado({"texto": "a" * 10000})
    assert len(result) < 6100
    assert "truncado" in result
