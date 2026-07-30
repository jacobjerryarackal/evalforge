import re

from src.domain.entities.dataset import GoldenDataset


class DatasetValidationError(ValueError):
    """Exception raised when a dataset fails structural or semantic validation."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        if self.errors:
            return f"{super().__str__()} Details:\n- " + "\n- ".join(self.errors)
        return super().__str__()


class DatasetValidator:
    """Validator for validating dataset schemas, required fields, versioning, and constraints."""

    # Simple SemVer regex: major.minor.patch[-suffix]
    SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")

    def validate(self, dataset: GoldenDataset) -> None:
        """Validates a GoldenDataset instance. Raises DatasetValidationError if any checks fail."""
        errors: list[str] = []

        # 1. Validate dataset required fields
        if not dataset.dataset_id or not dataset.dataset_id.strip():
            errors.append("Dataset 'dataset_id' is required and cannot be empty.")
        if not dataset.name or not dataset.name.strip():
            errors.append("Dataset 'name' is required and cannot be empty.")
        if not dataset.version or not dataset.version.strip():
            errors.append("Dataset 'version' is required and cannot be empty.")

        # 2. Validate SemVer format
        if dataset.version and not self.SEMVER_PATTERN.match(dataset.version):
            errors.append(
                f"Dataset version '{dataset.version}' does not "
                "conform to semantic versioning (X.Y.Z)."
            )

        # 3. Validate test cases
        case_ids: set[str] = set()
        for idx, case in enumerate(dataset.test_cases):
            # Check required fields
            if not case.case_id or not case.case_id.strip():
                errors.append(f"Test case at index {idx} has an empty 'case_id'.")
            else:
                # Check duplicate case_ids
                if case.case_id in case_ids:
                    errors.append(f"Duplicate 'case_id' found: '{case.case_id}'.")
                case_ids.add(case.case_id)

            if not case.input_query or not case.input_query.strip():
                errors.append(f"Test case '{case.case_id or idx}' has an empty 'input_query'.")

            # Check invalid constraints
            if not isinstance(case.constraints, dict):
                errors.append(f"Test case '{case.case_id}' constraints must be a dictionary.")
            else:
                for k, v in case.constraints.items():
                    # Validate constraint value type (scalar types)
                    if not isinstance(v, (int, float, str, bool)) and v is not None:
                        errors.append(
                            f"Test case '{case.case_id}' constraint '{k}' "
                            f"has an invalid type: {type(v).__name__}. "
                            "Constraints must be simple scalar types "
                            "(int, float, str, bool, null)."
                        )
                    # Specific known constraint type validation
                    if k == "max_price" and not isinstance(v, (int, float)):
                        errors.append(
                            f"Test case '{case.case_id}' constraint 'max_price' must be numeric."
                        )
                    if k == "max_latency" and not isinstance(v, (int, float)):
                        errors.append(
                            f"Test case '{case.case_id}' constraint 'max_latency' must be numeric."
                        )
                    if k == "token_budget" and not isinstance(v, int):
                        errors.append(
                            f"Test case '{case.case_id}' constraint "
                            "'token_budget' must be an integer."
                        )

        if errors:
            raise DatasetValidationError("Dataset validation failed.", errors)
