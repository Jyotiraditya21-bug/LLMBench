from backend.app.core.snapshots import (
    build_evaluation_snapshot,
    snapshots_are_compatible,
)
from backend.app.models.dataset import Dataset, TestCase as CaseModel
from backend.app.models.prompt import Prompt


def _dataset(question: str = "What is 2+2?") -> Dataset:
    return Dataset(
        id=1,
        name="Math",
        version="1.0.0",
        category="reasoning",
        test_cases=[
            CaseModel(
                id=2,
                dataset_id=1,
                question=question,
                ground_truth="4",
                category="reasoning",
                meta_data={"difficulty": "easy"},
            )
        ],
    )


def test_snapshot_is_deterministic_and_records_versions() -> None:
    prompt = Prompt(
        id=3,
        name="Answer",
        version="2.0.0",
        system_prompt="Be concise",
        user_template="{{question}}",
    )

    first = build_evaluation_snapshot(
        _dataset(),
        prompt,
        ["gpt-4o", "claude-3-haiku"],
    )
    second = build_evaluation_snapshot(
        _dataset(),
        prompt,
        ["claude-3-haiku", "gpt-4o"],
    )

    assert first == second
    assert first["dataset"]["test_cases"][0]["question"] == "What is 2+2?"
    assert first["prompt"]["version"] == "2.0.0"
    assert first["pricing_version"]
    assert first["judge_version"]


def test_compatibility_rejects_changed_dataset_or_models() -> None:
    baseline = build_evaluation_snapshot(_dataset(), None, ["gpt-4o"])
    changed_dataset = build_evaluation_snapshot(
        _dataset("What is 3+3?"),
        None,
        ["gpt-4o"],
    )
    changed_models = build_evaluation_snapshot(
        _dataset(),
        None,
        ["claude-3-haiku"],
    )

    assert snapshots_are_compatible(baseline, baseline)
    assert not snapshots_are_compatible(baseline, changed_dataset)
    assert not snapshots_are_compatible(baseline, changed_models)
