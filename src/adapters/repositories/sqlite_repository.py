import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timezone

from src.domain.entities import EvaluationRun, GoldenDataset, GoldenTestCase, TestCaseEvaluation
from src.domain.interfaces.repository import EvaluationRepository

logger = logging.getLogger("evaluation.adapters.repositories.sqlite_repository")


class SqliteEvaluationRepository(EvaluationRepository):
    """SQLite implementation of EvaluationRepository."""

    def __init__(self, db_path: str = "evalforge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Synchronously initializes database tables and indices."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Golden Datasets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS golden_datasets (
                    dataset_id TEXT,
                    version TEXT,
                    name TEXT,
                    description TEXT,
                    test_cases TEXT,
                    metadata TEXT,
                    PRIMARY KEY (dataset_id, version)
                )
                """)
            # Evaluation Runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    run_id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    dataset_version TEXT,
                    sut_version TEXT,
                    timestamp TEXT,
                    cases TEXT,
                    parameters TEXT,
                    summary TEXT,
                    metadata TEXT
                )
                """)
            # Create indices for faster lookups
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_datasets_id ON golden_datasets (dataset_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_runs_dataset ON evaluation_runs (dataset_id)"
            )
            conn.commit()
        logger.info(f"Initialized SQLite database at {self.db_path}")

    async def save_dataset(self, dataset: GoldenDataset) -> None:
        """Saves a golden dataset to the SQLite database."""

        def _save():
            # Convert nested models to JSON string
            test_cases_json = json.dumps([c.model_dump() for c in dataset.test_cases])
            metadata_json = json.dumps(dataset.metadata)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO golden_datasets
                    (dataset_id, version, name, description, test_cases, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dataset.dataset_id,
                        dataset.version,
                        dataset.name,
                        dataset.description,
                        test_cases_json,
                        metadata_json,
                    ),
                )
                conn.commit()

        await asyncio.to_thread(_save)

    async def get_dataset(
        self, dataset_id: str, version: str | None = None
    ) -> GoldenDataset | None:
        """Retrieves a specific golden dataset version from the SQLite database."""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if version is not None:
                    cursor.execute(
                        """
                        SELECT dataset_id, version, name, description, test_cases, metadata
                        FROM golden_datasets
                        WHERE dataset_id = ? AND version = ?
                        """,
                        (dataset_id, version),
                    )
                    row = cursor.fetchone()
                else:
                    cursor.execute(
                        """
                        SELECT dataset_id, version, name, description, test_cases, metadata
                        FROM golden_datasets
                        WHERE dataset_id = ?
                        ORDER BY version DESC LIMIT 1
                        """,
                        (dataset_id,),
                    )
                    row = cursor.fetchone()

                if not row:
                    return None

                # De-serialize
                test_cases_data = json.loads(row["test_cases"])
                metadata = json.loads(row["metadata"])

                test_cases = [GoldenTestCase.model_validate(c) for c in test_cases_data]

                return GoldenDataset(
                    dataset_id=row["dataset_id"],
                    name=row["name"],
                    description=row["description"],
                    version=row["version"],
                    test_cases=test_cases,
                    metadata=metadata,
                )

        return await asyncio.to_thread(_get)

    async def list_datasets(self) -> list[GoldenDataset]:
        """Lists all golden datasets stored in the SQLite database."""

        def _list():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dataset_id, version, name, description, test_cases, metadata
                    FROM golden_datasets
                    """)
                rows = cursor.fetchall()

                datasets = []
                for row in rows:
                    test_cases_data = json.loads(row["test_cases"])
                    metadata = json.loads(row["metadata"])
                    test_cases = [GoldenTestCase.model_validate(c) for c in test_cases_data]

                    datasets.append(
                        GoldenDataset(
                            dataset_id=row["dataset_id"],
                            name=row["name"],
                            description=row["description"],
                            version=row["version"],
                            test_cases=test_cases,
                            metadata=metadata,
                        )
                    )
                return datasets

        return await asyncio.to_thread(_list)

    async def save_run(self, run: EvaluationRun) -> None:
        """Saves an evaluation run's trajectory data and computed metrics to SQLite."""

        def _save():
            cases_json = json.dumps([c.model_dump(mode="json") for c in run.cases])
            parameters_json = json.dumps(run.parameters)
            summary_json = json.dumps(run.summary)
            metadata_json = json.dumps(run.metadata)
            timestamp_str = run.timestamp.isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO evaluation_runs
                    (run_id, dataset_id, dataset_version, sut_version,
                     timestamp, cases, parameters, summary, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        run.dataset_id,
                        run.dataset_version,
                        run.sut_version,
                        timestamp_str,
                        cases_json,
                        parameters_json,
                        summary_json,
                        metadata_json,
                    ),
                )
                conn.commit()

        await asyncio.to_thread(_save)

    async def get_run(self, run_id: str) -> EvaluationRun | None:
        """Retrieves a past evaluation run by its ID from the SQLite database."""

        def _get():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT run_id, dataset_id, dataset_version, sut_version,
                           timestamp, cases, parameters, summary, metadata
                    FROM evaluation_runs
                    WHERE run_id = ?
                    """,
                    (run_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                # De-serialize
                cases_data = json.loads(row["cases"])
                parameters = json.loads(row["parameters"])
                summary = json.loads(row["summary"])
                metadata = json.loads(row["metadata"])

                cases = [TestCaseEvaluation.model_validate(c) for c in cases_data]

                # Parse timestamp safely
                try:
                    timestamp = datetime.fromisoformat(row["timestamp"])
                except Exception:
                    timestamp = datetime.now(timezone.utc)

                run = EvaluationRun(
                    run_id=row["run_id"],
                    dataset_id=row["dataset_id"],
                    dataset_version=row["dataset_version"],
                    sut_version=row["sut_version"],
                    timestamp=timestamp,
                    cases=cases,
                    parameters=parameters,
                    summary=summary,
                    metadata=metadata,
                )
                return run

        return await asyncio.to_thread(_get)

    async def list_runs(self, dataset_id: str | None = None) -> list[EvaluationRun]:
        """Lists past evaluation runs, optionally filtered by dataset ID, from SQLite."""

        def _list():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if dataset_id is not None:
                    cursor.execute(
                        """
                        SELECT run_id, dataset_id, dataset_version, sut_version,
                               timestamp, cases, parameters, summary, metadata
                        FROM evaluation_runs
                        WHERE dataset_id = ?
                        """,
                        (dataset_id,),
                    )
                else:
                    cursor.execute("""
                        SELECT run_id, dataset_id, dataset_version, sut_version,
                               timestamp, cases, parameters, summary, metadata
                        FROM evaluation_runs
                        """)

                rows = cursor.fetchall()

                runs = []
                for row in rows:
                    cases_data = json.loads(row["cases"])
                    parameters = json.loads(row["parameters"])
                    summary = json.loads(row["summary"])
                    metadata = json.loads(row["metadata"])

                    cases = [TestCaseEvaluation.model_validate(c) for c in cases_data]

                    try:
                        timestamp = datetime.fromisoformat(row["timestamp"])
                    except Exception:
                        timestamp = datetime.now(timezone.utc)

                    runs.append(
                        EvaluationRun(
                            run_id=row["run_id"],
                            dataset_id=row["dataset_id"],
                            dataset_version=row["dataset_version"],
                            sut_version=row["sut_version"],
                            timestamp=timestamp,
                            cases=cases,
                            parameters=parameters,
                            summary=summary,
                            metadata=metadata,
                        )
                    )
                return runs

        return await asyncio.to_thread(_list)
