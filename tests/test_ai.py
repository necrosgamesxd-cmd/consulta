"""
Tests para funciones AI (utils/ai.py).
Usa mocks para evitar llamadas reales a APIs.
"""

from unittest.mock import patch, MagicMock
import pytest
from utils.ai import verificar_api_key, _acumular_usage, get_model_for_provider


class TestVerificarAPIKey:
    @patch("utils.ai._get_api_key")
    def test_key_valida(self, mock_get_key):
        mock_get_key.return_value = "sk-real-key-12345"
        assert verificar_api_key() is True

    @patch("utils.ai._get_api_key")
    def test_key_vacia(self, mock_get_key):
        mock_get_key.return_value = ""
        assert verificar_api_key() is False

    @patch("utils.ai._get_api_key")
    def test_key_placeholder(self, mock_get_key):
        mock_get_key.return_value = "tu_api_key_aqui"
        assert verificar_api_key() is False


class TestGetModelForProvider:
    def test_groq_super(self):
        with patch("utils.ai.get_active_provider", return_value="groq"):
            model = get_model_for_provider("super")
            assert "70b" in model.lower() or "70" in model

    def test_groq_nano(self):
        with patch("utils.ai.get_active_provider", return_value="groq"):
            model = get_model_for_provider("nano")
            assert "8b" in model.lower() or "8" in model

    def test_fallback_tier_invalido(self):
        with patch("utils.ai.get_active_provider", return_value="groq"):
            model = get_model_for_provider("nonexistent")
            assert model is not None


class TestAcumularUsage:
    def test_acumula_correctamente(self):
        import streamlit as st
        st.session_state["token_usage"] = {"prompt": 10, "completion": 20, "total": 30}

        mock_response = MagicMock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15

        _acumular_usage(mock_response)

        usage = st.session_state["token_usage"]
        assert usage["prompt"] == 15
        assert usage["completion"] == 30
        assert usage["total"] == 45

    def test_sin_usage_no_error(self):
        import streamlit as st
        st.session_state["token_usage"] = {"prompt": 0, "completion": 0, "total": 0}
        mock_response = MagicMock()
        mock_response.usage = None
        _acumular_usage(mock_response)
