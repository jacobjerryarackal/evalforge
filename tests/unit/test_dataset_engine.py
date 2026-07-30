import json

import pytest

from src.domain.entities.dataset import GoldenDataset, GoldenTestCase
from src.use_cases.datasets.loader import DatasetLoader
from src.use_cases.datasets.registry import DatasetRegistry
from src.use_cases.datasets.validator import DatasetValidationError, DatasetValidator


def test_dataset_registry_operations():
    registry = DatasetRegistry()

    case1 = GoldenTestCase(case_id="tc-1", input_query="Hello")
    ds1_v1 = GoldenDataset(dataset_id="ds-1", name="DS 1", version="1.0.0", test_cases=[case1])
    ds1_v2 = GoldenDataset(dataset_id="ds-1", name="DS 1", version="2.0.0", test_cases=[case1])
    ds2_v1 = GoldenDataset(dataset_id="ds-2", name="DS 2", version="1.0.0", test_cases=[case1])

    # Test registration
    registry.register(ds1_v1)
    registry.register(ds1_v2)
    registry.register(ds2_v1)

    # Validate uniqueness duplicate checks
    with pytest.raises(ValueError, match="already registered"):
        registry.register(ds1_v1)

    # Test retrieval
    assert registry.get("ds-1", "1.0.0") == ds1_v1
    assert registry.get("ds-1", "2.0.0") == ds1_v2

    # Test latest version resolution
    assert registry.get("ds-1") == ds1_v2

    # Test non-existent retrieval
    with pytest.raises(ValueError, match="not registered"):
        registry.get("ds-3")
    with pytest.raises(ValueError, match="not registered"):
        registry.get("ds-1", "3.0.0")

    # Test list discovery
    datasets = registry.list_datasets()
    assert len(datasets) == 3
    assert ds1_v1 in datasets
    assert ds1_v2 in datasets
    assert ds2_v1 in datasets


def test_dataset_validator_semantics():
    validator = DatasetValidator()

    # 1. Successful validation
    case = GoldenTestCase(
        case_id="tc-1",
        input_query="Search Flights",
        constraints={"max_price": 500, "token_budget": 100},
    )
    valid_ds = GoldenDataset(
        dataset_id="ds-1",
        name="Valid DS",
        version="1.2.3-beta.1",
        test_cases=[case],
    )
    validator.validate(valid_ds)  # Should not raise

    # 2. Missing required fields in dataset
    invalid_ds1 = GoldenDataset(dataset_id=" ", name="Valid DS", version="1.0.0", test_cases=[])
    with pytest.raises(DatasetValidationError, match="dataset_id"):
        validator.validate(invalid_ds1)

    # 3. Invalid SemVer format
    invalid_ds2 = GoldenDataset(dataset_id="ds-1", name="Valid DS", version="1.0", test_cases=[])
    with pytest.raises(DatasetValidationError, match="semantic versioning"):
        validator.validate(invalid_ds2)

    # 4. Duplicate case_id
    case1 = GoldenTestCase(case_id="tc-1", input_query="Q1")
    case2 = GoldenTestCase(case_id="tc-1", input_query="Q2")
    invalid_ds3 = GoldenDataset(
        dataset_id="ds-1", name="Valid DS", version="1.0.0", test_cases=[case1, case2]
    )
    with pytest.raises(DatasetValidationError, match="Duplicate 'case_id'"):
        validator.validate(invalid_ds3)

    # 5. Invalid constraints format/types
    case_invalid_const = GoldenTestCase(
        case_id="tc-1",
        input_query="Q1",
        constraints={"max_price": "five hundred"},  # must be numeric
    )
    invalid_ds4 = GoldenDataset(
        dataset_id="ds-1", name="Valid DS", version="1.0.0", test_cases=[case_invalid_const]
    )
    with pytest.raises(DatasetValidationError, match="constraint 'max_price' must be numeric"):
        validator.validate(invalid_ds4)

    case_invalid_scalar = GoldenTestCase(
        case_id="tc-1",
        input_query="Q1",
        constraints={"complex_key": [1, 2, 3]},  # list not allowed
    )
    invalid_ds5 = GoldenDataset(
        dataset_id="ds-1", name="Valid DS", version="1.0.0", test_cases=[case_invalid_scalar]
    )
    with pytest.raises(DatasetValidationError, match="invalid type"):
        validator.validate(invalid_ds5)


def test_dataset_loader_json(tmp_path):
    loader = DatasetLoader()

    # Create temporary JSON dataset file
    dataset_data = {
        "dataset_id": "ds-json",
        "name": "JSON Dataset",
        "version": "1.0.0",
        "test_cases": [
            {
                "case_id": "tc-1",
                "input_query": "Book room",
                "constraints": {"location": "Rome"},
            }
        ],
    }
    json_file = tmp_path / "dataset.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(dataset_data, f)

    loaded = loader.load_json(str(json_file))
    assert loaded.dataset_id == "ds-json"
    assert len(loaded.test_cases) == 1
    assert loaded.test_cases[0].case_id == "tc-1"
    assert loaded.test_cases[0].constraints["location"] == "Rome"

    # Test JSON parse error
    bad_json = tmp_path / "bad.json"
    with open(bad_json, "w", encoding="utf-8") as f:
        f.write("{invalid json")
    with pytest.raises(DatasetValidationError, match="Invalid JSON syntax"):
        loader.load_json(str(bad_json))


def test_dataset_loader_jsonl(tmp_path):
    loader = DatasetLoader()

    # Format 1: First line metadata, followed by test cases
    jsonl_lines = [
        json.dumps({"dataset_id": "ds-jsonl-1", "name": "Metadata JSONL", "version": "1.2.0"}),
        json.dumps({"case_id": "tc-1", "input_query": "Query 1"}),
        json.dumps({"case_id": "tc-2", "input_query": "Query 2"}),
    ]
    jsonl_file1 = tmp_path / "dataset1.jsonl"
    with open(jsonl_file1, "w", encoding="utf-8") as f:
        f.write("\n".join(jsonl_lines))

    loaded1 = loader.load_jsonl(str(jsonl_file1))
    assert loaded1.dataset_id == "ds-jsonl-1"
    assert loaded1.version == "1.2.0"
    assert len(loaded1.test_cases) == 2
    assert loaded1.test_cases[0].case_id == "tc-1"
    assert loaded1.test_cases[1].case_id == "tc-2"

    # Format 2: No metadata line, pure test cases + parameter overrides
    jsonl_lines_no_meta = [
        json.dumps({"case_id": "tc-3", "input_query": "Query 3"}),
        json.dumps({"case_id": "tc-4", "input_query": "Query 4"}),
    ]
    jsonl_file2 = tmp_path / "dataset2.jsonl"
    with open(jsonl_file2, "w", encoding="utf-8") as f:
        f.write("\n".join(jsonl_lines_no_meta))

    # Expect error if overrides not provided
    with pytest.raises(DatasetValidationError, match="dataset_id' is missing"):
        loader.load_jsonl(str(jsonl_file2))

    # Pass overrides
    loaded2 = loader.load_jsonl(
        str(jsonl_file2), dataset_id="ds-jsonl-2", name="Override Name", version="2.1.0"
    )
    assert loaded2.dataset_id == "ds-jsonl-2"
    assert loaded2.name == "Override Name"
    assert loaded2.version == "2.1.0"
    assert len(loaded2.test_cases) == 2
    assert loaded2.test_cases[0].case_id == "tc-3"

    # Test line-numbered error parsing in JSONL
    bad_jsonl_lines = [
        json.dumps({"dataset_id": "ds-bad", "name": "Bad JSONL", "version": "1.0.0"}),
        "{ malformed json line }",
        json.dumps({"case_id": "tc-1"}),  # missing input_query
    ]
    jsonl_file3 = tmp_path / "dataset3.jsonl"
    with open(jsonl_file3, "w", encoding="utf-8") as f:
        f.write("\n".join(bad_jsonl_lines))

    with pytest.raises(DatasetValidationError) as excinfo:
        loader.load_jsonl(str(jsonl_file3))

    err_str = str(excinfo.value)
    assert "Line 2" in err_str
    assert "Line 3" in err_str
