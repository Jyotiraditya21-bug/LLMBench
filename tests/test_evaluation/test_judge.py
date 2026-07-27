import pytest
from unittest.mock import AsyncMock, patch

from backend.app.workers.evaluator import JudgeEvaluationError, evaluate_with_judge


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
            assert result["is_mock"] is False


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
            assert result["is_mock"] is False


@pytest.mark.asyncio
async def test_judge_fails_without_provider_in_real_mode() -> None:
    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = None
        mock_settings.OPENAI_API_KEY = None
        mock_settings.GEMINI_API_KEY = None
        mock_settings.DEMO_MODE = False

        with pytest.raises(JudgeEvaluationError, match="working judge provider"):
            await evaluate_with_judge("Question", "Expected", "Output")


@pytest.mark.asyncio
async def test_judge_labels_mock_result_in_explicit_demo_mode() -> None:
    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = None
        mock_settings.OPENAI_API_KEY = None
        mock_settings.GEMINI_API_KEY = None
        mock_settings.DEMO_MODE = True

        result = await evaluate_with_judge("Question", "Expected", "Output")

        assert result["is_mock"] is True


@pytest.mark.asyncio
async def test_judge_rejects_out_of_range_scores_in_real_mode() -> None:
    invalid_response = """
    {
      "accuracy": 9,
      "completeness": 5,
      "hallucination": 5,
      "tone": 5,
      "reasoning": 5,
      "reason": "Invalid accuracy score."
    }
    """

    with patch("backend.app.workers.evaluator.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.HAS_ANTHROPIC = True
        mock_settings.DEMO_MODE = False

        with patch("backend.app.workers.evaluator.anthropic.AsyncAnthropic") as client_class:
            client = AsyncMock()
            message = AsyncMock()
            content = AsyncMock()
            content.text = invalid_response
            message.content = [content]
            client.messages.create.return_value = message
            client_class.return_value = client

            with pytest.raises(JudgeEvaluationError, match="Failed to parse judge output"):
                await evaluate_with_judge("Question", "Expected", "Output")
