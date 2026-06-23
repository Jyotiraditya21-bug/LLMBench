import pytest
from unittest.mock import AsyncMock, patch

from backend.app.workers.evaluator import evaluate_with_judge


@pytest.mark.asyncio
async def test_judge_evaluation_success() -> None:
    """Asserts that evaluate_with_judge successfully requests, cleans, and parses JSON output."""
    mock_claude_response = """
    {
      "accuracy": 5.0,
      "completeness": 5.0,
      "hallucination": 5.0,
      "tone": 4.0,
      "reasoning": 5.0,
      "reason": "Perfect match with ground truth."
    }
    """

    # Mock settings.ANTHROPIC_API_KEY to bypass mock fallback trigger
    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test_anthropic_key"

        # Mock the anthropic AsyncAnthropic client creation
        with patch("backend.app.workers.evaluator.anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock()
            
            # Mock Claude response structure
            mock_message = AsyncMock()
            mock_content_block = AsyncMock()
            mock_content_block.text = mock_claude_response
            mock_message.content = [mock_content_block]
            mock_client.messages.create.return_value = mock_message
            
            mock_client_class.return_value = mock_client

            result = await evaluate_with_judge(
                question="What is 2+2?",
                ground_truth="4",
                model_output="The answer is 4."
            )

            assert result["accuracy"] == 5.0
            assert result["hallucination"] == 5.0
            assert result["reason"] == "Perfect match with ground truth."


@pytest.mark.asyncio
async def test_judge_evaluation_markdown_cleaning() -> None:
    """Asserts that JSON wrapped in markdown code blocks is successfully cleaned and parsed."""
    mock_markdown_response = """```json
    {
      "accuracy": 4.0,
      "completeness": 3.0,
      "hallucination": 5.0,
      "tone": 5.0,
      "reasoning": 4.0,
      "reason": "Correct but slightly incomplete response."
    }
    ```"""

    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test_anthropic_key"

        with patch("backend.app.workers.evaluator.anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock()
            
            mock_message = AsyncMock()
            mock_content_block = AsyncMock()
            mock_content_block.text = mock_markdown_response
            mock_message.content = [mock_content_block]
            mock_client.messages.create.return_value = mock_message
            
            mock_client_class.return_value = mock_client

            result = await evaluate_with_judge(
                question="Ambiguous question",
                ground_truth="Complete answer",
                model_output="Half answer"
            )

            assert result["accuracy"] == 4.0
            assert result["completeness"] == 3.0
            assert "slightly incomplete" in result["reason"]
