import pytest

from evaluation.datasets.schema import DatasetError, GoldenCase, load_dataset

_VALID_LINE = (
    '{"id": "q01", "question": "What is metamorphic testing?", '
    '"expected_behavior": "answer"}'
)


def test_schema_minimal_case_applies_defaults() -> None:
    """A case with only id + question validates and fills defaults."""
    case = GoldenCase.model_validate({"id": "x", "question": "q?"})
    assert case.version == 2
    assert case.expected_behavior == "answer"
    assert case.difficulty == "medium"
    assert case.tags == []
    assert case.expected_answer is None


def test_schema_rejects_unknown_field() -> None:
    """extra='forbid' turns typos into validation errors."""
    with pytest.raises(Exception):
        GoldenCase.model_validate({"id": "x", "question": "q?", "questoin": "typo"})


def test_schema_rejects_invalid_expected_behavior() -> None:
    with pytest.raises(Exception):
        GoldenCase.model_validate(
            {"id": "x", "question": "q?", "expected_behavior": "maybe"}
        )


def test_load_dataset_parses_valid_jsonl(tmp_path) -> None:
    path = tmp_path / "golden.jsonl"
    path.write_text(_VALID_LINE + "\n\n")
    cases = load_dataset(path)
    assert len(cases) == 1
    assert cases[0].id == "q01"


def test_load_dataset_raises_on_invalid_json_with_line_number(tmp_path) -> None:
    path = tmp_path / "golden.jsonl"
    path.write_text(_VALID_LINE + "\nnot json\n")
    with pytest.raises(DatasetError, match=":2"):
        load_dataset(path)


def test_load_dataset_raises_on_duplicate_ids(tmp_path) -> None:
    path = tmp_path / "golden.jsonl"
    path.write_text(_VALID_LINE + "\n" + _VALID_LINE + "\n")
    with pytest.raises(DatasetError, match="duplicate case id 'q01'"):
        load_dataset(path)


def test_load_dataset_raises_on_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "nope.jsonl")


def test_committed_seed_dataset_is_valid() -> None:
    """The checked-in golden_v2.jsonl must always pass its own schema."""
    from pathlib import Path

    repo_root = Path(__file__).parent.parent.parent
    cases = load_dataset(repo_root / "evaluation" / "datasets" / "golden_v2.jsonl")
    assert len(cases) >= 1
    assert cases[0].id == "q01"
