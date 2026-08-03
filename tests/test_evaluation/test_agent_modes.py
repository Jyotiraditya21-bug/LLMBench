from unittest.mock import patch

import pytest

from agents.rca_agent import AgentEvaluationError as RCAError
from agents.rca_agent import analyze_run_failures
from agents.red_team_agent import AgentEvaluationError as RedTeamError
from agents.red_team_agent import generate_adversarial_cases


FAILURES = [
    {
        "question": "Question",
        "ground_truth": "Answer",
        "output": "Wrong",
        "reason": "Incorrect",
    }
]


@pytest.mark.asyncio
async def test_rca_does_not_return_mock_output_in_real_mode() -> None:
    with patch("agents.rca_agent.settings") as agent_settings:
        agent_settings.ANTHROPIC_API_KEY = None
        agent_settings.OPENAI_API_KEY = None
        agent_settings.GEMINI_API_KEY = None
        agent_settings.DEMO_MODE = False

        with pytest.raises(RCAError, match="No configured provider"):
            await analyze_run_failures(FAILURES)


@pytest.mark.asyncio
async def test_rca_labels_demo_output() -> None:
    with patch("agents.rca_agent.settings") as agent_settings:
        agent_settings.ANTHROPIC_API_KEY = None
        agent_settings.OPENAI_API_KEY = None
        agent_settings.GEMINI_API_KEY = None
        agent_settings.DEMO_MODE = True

        report = await analyze_run_failures(FAILURES)

    assert report.startswith("*(DEMO AGENT OUTPUT)*")


@pytest.mark.asyncio
async def test_redteam_does_not_return_mock_cases_in_real_mode() -> None:
    with patch("agents.red_team_agent.settings") as agent_settings:
        agent_settings.ANTHROPIC_API_KEY = None
        agent_settings.OPENAI_API_KEY = None
        agent_settings.GEMINI_API_KEY = None
        agent_settings.DEMO_MODE = False

        with pytest.raises(RedTeamError, match="No configured provider"):
            await generate_adversarial_cases(
                [{"question": "Question", "ground_truth": "Answer"}]
            )
