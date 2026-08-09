import asyncio
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

from src.domain.entities import (
    EvaluationRun,
    Experiment,
    GoldenDataset,
    GoldenTestCase,
    TestCaseEvaluation,
)
from src.domain.interfaces.repository import EvaluationRepository

logger = logging.getLogger("evaluation.adapters.repositories.postgres_repository")


class PostgresEvaluationRepository(EvaluationRepository):
    """PostgreSQL implementation of EvaluationRepository using thread-safe connection pooling."""

    def __init__(self, database_url: str):
        # Render and Heroku inject postgres:// scheme but psycopg2 requires postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        self.database_url = database_url
        logger.info("Initializing ThreadedConnectionPool for PostgreSQL...")
        self.pool = ThreadedConnectionPool(1, 20, dsn=database_url)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager to acquire a connection from the pool and yield it."""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def _init_db(self) -> None:
        """Synchronously initializes database tables and indices."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
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
                # Experiments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS experiments (
                        experiment_id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        run_ids TEXT,
                        metadata TEXT,
                        created_at TEXT
                    )
                """)
                # Create indices for faster lookups
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_datasets_id ON golden_datasets (dataset_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_runs_dataset ON evaluation_runs (dataset_id)"
                )
        logger.info("Initialized PostgreSQL database tables and indices.")

    async def save_dataset(self, dataset: GoldenDataset) -> None:
        """Saves a golden dataset to the PostgreSQL database."""

        def _save():
            test_cases_json = json.dumps([c.model_dump() for c in dataset.test_cases])
            metadata_json = json.dumps(dataset.metadata)

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO golden_datasets
                        (dataset_id, version, name, description, test_cases, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (dataset_id, version) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            test_cases = EXCLUDED.test_cases,
                            metadata = EXCLUDED.metadata
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

        await asyncio.to_thread(_save)

    async def get_dataset(
        self, dataset_id: str, version: str | None = None
    ) -> GoldenDataset | None:
        """Retrieves a specific golden dataset version from the PostgreSQL database."""

        def _get():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if version is not None:
                        cursor.execute(
                            """
                            SELECT dataset_id, version, name, description, test_cases, metadata
                            FROM golden_datasets
                            WHERE dataset_id = %s AND version = %s
                            """,
                            (dataset_id, version),
                        )
                        row = cursor.fetchone()
                    else:
                        cursor.execute(
                            """
                            SELECT dataset_id, version, name, description, test_cases, metadata
                            FROM golden_datasets
                            WHERE dataset_id = %s
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
        """Lists all golden datasets stored in the PostgreSQL database."""

        def _list():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
        """Saves an evaluation run's trajectory data and computed metrics to PostgreSQL."""

        def _save():
            cases_json = json.dumps([c.model_dump(mode="json") for c in run.cases])
            parameters_json = json.dumps(run.parameters)
            summary_json = json.dumps(run.summary)
            metadata_json = json.dumps(run.metadata)
            timestamp_str = run.timestamp.isoformat()

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO evaluation_runs
                        (run_id, dataset_id, dataset_version, sut_version,
                         timestamp, cases, parameters, summary, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (run_id) DO UPDATE SET
                            dataset_id = EXCLUDED.dataset_id,
                            dataset_version = EXCLUDED.dataset_version,
                            sut_version = EXCLUDED.sut_version,
                            timestamp = EXCLUDED.timestamp,
                            cases = EXCLUDED.cases,
                            parameters = EXCLUDED.parameters,
                            summary = EXCLUDED.summary,
                            metadata = EXCLUDED.metadata
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

        await asyncio.to_thread(_save)

    async def get_run(self, run_id: str) -> EvaluationRun | None:
        """Retrieves a past evaluation run by its ID from the PostgreSQL database."""

        def _get():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT run_id, dataset_id, dataset_version, sut_version,
                               timestamp, cases, parameters, summary, metadata
                        FROM evaluation_runs
                        WHERE run_id = %s
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
        """Lists past evaluation runs, optionally filtered by dataset ID, from PostgreSQL."""

        def _list():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if dataset_id is not None:
                        cursor.execute(
                            """
                            SELECT run_id, dataset_id, dataset_version, sut_version,
                                   timestamp, cases, parameters, summary, metadata
                            FROM evaluation_runs
                            WHERE dataset_id = %s
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

    async def save_experiment(self, experiment: Experiment) -> None:
        """Saves an experiment to the PostgreSQL database."""

        def _save():
            run_ids_json = json.dumps([r.run_id for r in experiment.runs])
            metadata_json = json.dumps(experiment.metadata)
            created_at_str = experiment.created_at.isoformat()

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO experiments
                        (experiment_id, name, description, run_ids, metadata, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (experiment_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            run_ids = EXCLUDED.run_ids,
                            metadata = EXCLUDED.metadata,
                            created_at = EXCLUDED.created_at
                        """,
                        (
                            experiment.experiment_id,
                            experiment.name,
                            experiment.description,
                            run_ids_json,
                            metadata_json,
                            created_at_str,
                        ),
                    )

        await asyncio.to_thread(_save)

    async def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Retrieves an experiment from the PostgreSQL database."""

        def _get():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT experiment_id, name, description, run_ids, metadata, created_at
                        FROM experiments
                        WHERE experiment_id = %s
                        """,
                        (experiment_id,),
                    )
                    row = cursor.fetchone()

                    if not row:
                        return None

                    run_ids = json.loads(row["run_ids"])
                    metadata = json.loads(row["metadata"])
                    try:
                        created_at = datetime.fromisoformat(row["created_at"])
                    except Exception:
                        created_at = datetime.now(timezone.utc)

                    return row["name"], row["description"], run_ids, metadata, created_at

        res = await asyncio.to_thread(_get)
        if not res:
            return None

        name, description, run_ids, metadata, created_at = res

        # Load runs from evaluation_runs table
        runs = []
        for run_id in run_ids:
            run = await self.get_run(run_id)
            if run:
                runs.append(run)

        return Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            runs=runs,
            metadata=metadata,
            created_at=created_at,
        )

    async def list_experiments(self) -> list[Experiment]:
        """Lists all experiments stored in the PostgreSQL database."""

        def _list():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT experiment_id, name, description, run_ids, metadata, created_at
                        FROM experiments
                    """)
                    rows = cursor.fetchall()

                    experiments_data = []
                    for row in rows:
                        run_ids = json.loads(row["run_ids"])
                        metadata = json.loads(row["metadata"])
                        try:
                            created_at = datetime.fromisoformat(row["created_at"])
                        except Exception:
                            created_at = datetime.now(timezone.utc)
                        experiments_data.append(
                            (
                                row["experiment_id"],
                                row["name"],
                                row["description"],
                                run_ids,
                                metadata,
                                created_at,
                            )
                        )
                    return experiments_data

        exps_data = await asyncio.to_thread(_list)
        experiments = []
        for exp_id, name, description, run_ids, metadata, created_at in exps_data:
            runs = []
            for run_id in run_ids:
                run = await self.get_run(run_id)
                if run:
                    runs.append(run)
            experiments.append(
                Experiment(
                    experiment_id=exp_id,
                    name=name,
                    description=description,
                    runs=runs,
                    metadata=metadata,
                    created_at=created_at,
                )
            )
        return experiments
