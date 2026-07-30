import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from examples.travel_agent.travel_agent_sut import TravelAgentSUT
from src.adapters.llm.gemini import GeminiProvider
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.domain.entities import (
    BenchmarkConfig,
    GoldenDataset,
    GoldenTestCase,
    RetryPolicy,
)
from src.use_cases.datasets.registry import DatasetRegistry
from src.use_cases.datasets.validator import DatasetValidator
from src.use_cases.experiments.engine import ExperimentEngine
from src.use_cases.metrics.registry import create_default_registry
from src.use_cases.reporting.markdown import MarkdownReportGenerator
from src.use_cases.runners.benchmark_runner import BenchmarkRunner

logger = logging.getLogger("evaluation.api")

app = FastAPI(
    title="EvalForge Evaluation Platform",
    description="REST API for AI Agent Evaluation Engine",
    version="1.0.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup database path and repository
db_path = "evalforge_platform.db"
repo = SqliteEvaluationRepository(db_path=db_path)
dataset_registry = DatasetRegistry()
experiment_engine = ExperimentEngine(repo)

# Initialize standard provider, metric registry, and benchmark runner
default_provider = GeminiProvider(mock_mode=True)
metric_registry = create_default_registry(default_provider)
runner = BenchmarkRunner(repository=repo, registry=metric_registry)


class TestCaseSchema(BaseModel):
    case_id: str
    input_query: str
    expected_output: str | None = None
    expected_tool_calls: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    ground_truth_context: List[str] = Field(default_factory=list)


class DatasetCreateSchema(BaseModel):
    dataset_id: str
    name: str
    version: str
    test_cases: List[TestCaseSchema]


class ExperimentCreateSchema(BaseModel):
    experiment_id: str
    name: str
    description: str | None = None


class RunBenchmarkRequestSchema(BaseModel):
    dataset_id: str
    version: str
    sut_name: str = "travel_agent"
    run_id: str | None = None
    concurrency: int = 3
    max_retries: int = 0
    experiment_id: str | None = None


SUTS = {"travel_agent": TravelAgentSUT()}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/datasets")
async def list_datasets():
    datasets = await repo.list_datasets()
    return [
        {
            "dataset_id": d.dataset_id,
            "name": d.name,
            "version": d.version,
            "cases_count": len(d.test_cases),
        }
        for d in datasets
    ]


@app.post("/api/datasets")
async def register_dataset(schema: DatasetCreateSchema):
    test_cases = [
        GoldenTestCase(
            case_id=c.case_id,
            input_query=c.input_query,
            expected_output=c.expected_output,
            expected_tool_calls=c.expected_tool_calls,
            constraints=c.constraints,
            ground_truth_context=c.ground_truth_context,
        )
        for c in schema.test_cases
    ]
    dataset = GoldenDataset(
        dataset_id=schema.dataset_id,
        name=schema.name,
        version=schema.version,
        test_cases=test_cases,
    )

    validator = DatasetValidator()
    try:
        validator.validate(dataset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {e}")

    await repo.save_dataset(dataset)
    return {
        "status": "registered",
        "dataset_id": dataset.dataset_id,
        "version": dataset.version,
    }


@app.get("/api/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    datasets = await repo.list_datasets()
    matching = [d for d in datasets if d.dataset_id == dataset_id]
    if not matching:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    latest = sorted(matching, key=lambda d: d.version, reverse=True)[0]
    return latest


@app.get("/api/datasets/{dataset_id}/versions/{version}")
async def get_dataset_version(dataset_id: str, version: str):
    datasets = await repo.list_datasets()
    for d in datasets:
        if d.dataset_id == dataset_id and d.version == version:
            return d
    raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} (v{version}) not found")


@app.get("/api/experiments")
async def list_experiments():
    experiments = await repo.list_experiments()
    return [
        {
            "experiment_id": e.experiment_id,
            "name": e.name,
            "description": e.description,
            "runs_count": len(e.runs),
        }
        for e in experiments
    ]


@app.post("/api/experiments")
async def create_experiment(schema: ExperimentCreateSchema):
    try:
        experiment = await experiment_engine.create_experiment(
            experiment_id=schema.experiment_id,
            name=schema.name,
            description=schema.description or "",
        )
        return {"status": "created", "experiment_id": experiment.experiment_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    experiment = await repo.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")

    report = experiment_engine.generate_summary(experiment)
    return {
        "experiment_id": experiment.experiment_id,
        "name": experiment.name,
        "description": experiment.description,
        "runs": [
            {
                "run_id": r.run_id,
                "sut_version": r.sut_version,
                "dataset_id": r.dataset_id,
                "dataset_version": r.dataset_version,
                "summary": r.summary,
            }
            for r in experiment.runs
        ],
        "report_markdown": report,
    }


@app.post("/api/experiments/{experiment_id}/runs/{run_id}")
async def add_run_to_experiment(experiment_id: str, run_id: str):
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found")
    try:
        await experiment_engine.add_run_to_experiment(experiment_id, run)
        return {"status": "added", "experiment_id": experiment_id, "run_id": run_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/runs")
async def list_runs():
    runs = await repo.list_runs()
    return [
        {
            "run_id": r.run_id,
            "dataset_id": r.dataset_id,
            "dataset_version": r.dataset_version,
            "sut_version": r.sut_version,
            "timestamp": r.timestamp.isoformat(),
            "summary": r.summary,
        }
        for r in runs
    ]


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@app.get("/api/runs/{run_id}/report")
async def get_run_report(run_id: str):
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    datasets = await repo.list_datasets()
    dataset = next(
        (
            d
            for d in datasets
            if d.dataset_id == run.dataset_id and d.version == run.dataset_version
        ),
        None,
    )
    report = MarkdownReportGenerator.generate_run_report(run, dataset)
    return {"run_id": run_id, "report_markdown": report}


async def _run_benchmark_task(
    run_id: str,
    dataset: GoldenDataset,
    sut: Any,
    concurrency: int,
    max_retries: int,
    experiment_id: str | None,
):
    evaluators = list(metric_registry.list_evaluators())
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Mock Mode)",
        evaluators=evaluators,
        concurrency=concurrency,
        retry_policy=RetryPolicy(max_retries=max_retries),
        execution_parameters={"experiment_id": experiment_id or "none"},
    )

    try:
        run = await runner.run_benchmark(run_id=run_id, config=config, sut=sut)
        if experiment_id:
            try:
                await experiment_engine.add_run_to_experiment(experiment_id, run)
            except Exception as e:
                logger.error(f"Failed to add run {run_id} to experiment {experiment_id}: {e}")
    except Exception as e:
        logger.error(f"Benchmark execution {run_id} failed: {e}")


@app.post("/api/benchmarks/run")
async def run_benchmark(request: RunBenchmarkRequestSchema, background_tasks: BackgroundTasks):
    sut_name = request.sut_name
    if sut_name not in SUTS:
        raise HTTPException(status_code=400, detail=f"SUT '{sut_name}' is not registered.")
    sut = SUTS[sut_name]

    datasets = await repo.list_datasets()
    matching_dataset = None
    for d in datasets:
        if d.dataset_id == request.dataset_id and d.version == request.version:
            matching_dataset = d
            break

    if not matching_dataset:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{request.dataset_id}' (v{request.version}) not found.",
        )

    run_id = request.run_id or f"run-{uuid.uuid4().hex[:8]}"

    background_tasks.add_task(
        _run_benchmark_task,
        run_id=run_id,
        dataset=matching_dataset,
        sut=sut,
        concurrency=request.concurrency,
        max_retries=request.max_retries,
        experiment_id=request.experiment_id,
    )

    return {"status": "running", "run_id": run_id}
