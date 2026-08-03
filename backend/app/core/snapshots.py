import hashlib
import json
from typing import Any, Dict, Iterable, Optional

from backend.app.models.dataset import Dataset
from backend.app.models.prompt import Prompt


SNAPSHOT_SCHEMA_VERSION = "1"
PRICING_VERSION = "2026-07-28"
JUDGE_VERSION = "multi-provider-v1"


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_evaluation_snapshot(
    dataset: Dataset,
    prompt: Optional[Prompt],
    models: Iterable[str],
) -> Dict[str, Any]:
    test_cases = [
        {
            "id": test_case.id,
            "question": test_case.question,
            "ground_truth": test_case.ground_truth,
            "category": test_case.category,
            "meta_data": test_case.meta_data or {},
        }
        for test_case in sorted(dataset.test_cases, key=lambda item: item.id)
    ]
    dataset_payload = {
        "id": dataset.id,
        "name": dataset.name,
        "version": dataset.version,
        "category": dataset.category,
        "test_cases": test_cases,
    }
    prompt_payload = (
        {
            "id": prompt.id,
            "name": prompt.name,
            "version": prompt.version,
            "system_prompt": prompt.system_prompt,
            "user_template": prompt.user_template,
        }
        if prompt
        else None
    )
    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "dataset": dataset_payload,
        "dataset_fingerprint": _fingerprint(dataset_payload),
        "prompt": prompt_payload,
        "prompt_fingerprint": _fingerprint(prompt_payload),
        "models": sorted(models),
        "pricing_version": PRICING_VERSION,
        "judge_version": JUDGE_VERSION,
    }
    snapshot["fingerprint"] = _fingerprint(snapshot)
    return snapshot


def snapshots_are_compatible(
    baseline: Dict[str, Any],
    comparison: Dict[str, Any],
) -> bool:
    return bool(
        baseline
        and comparison
        and baseline.get("dataset_fingerprint")
        == comparison.get("dataset_fingerprint")
        and baseline.get("models") == comparison.get("models")
        and baseline.get("judge_version") == comparison.get("judge_version")
    )
