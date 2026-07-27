import pytest
from unittest.mock import patch

from backend.app.workers.evaluator import (
    ProviderConfigurationError,
    call_target_llm,
)


@pytest.mark.asyncio
async def test_target_provider_fails_without_key_in_real_mode() -> None:
    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        mock_settings.DEMO_MODE = False

        with pytest.raises(ProviderConfigurationError, match="OpenAI is not configured"):
            await call_target_llm("gpt-4o", None, "Hello")


@pytest.mark.asyncio
async def test_target_provider_labels_output_in_explicit_demo_mode() -> None:
    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        mock_settings.DEMO_MODE = True

        result = await call_target_llm("gpt-4o", None, "Hello")

        assert result["is_mock"] is True
        assert result["output"].startswith("[MOCK OPENAI")
