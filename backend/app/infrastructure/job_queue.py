"""Cola en memoria para trabajos largos (indexación / consultas).

Diseño PMV1: sin Redis/Celery. Persistencia de estado solo en proceso.
Rollback: desactivar endpoints async y usar rutas síncronas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock, Thread
from typing import Any, Callable
from uuid import uuid4


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass
class Job:
    id: str
    job_type: str
    status: JobStatus = JobStatus.queued
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    )
    farmer_id: str = ""


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def enqueue(
        self,
        job_type: str,
        worker: Callable[[], dict[str, Any]],
        *,
        farmer_id: str = "",
    ) -> Job:
        job_id = str(uuid4())
        job = Job(id=job_id, job_type=job_type, farmer_id=farmer_id)
        with self._lock:
            self._jobs[job_id] = job

        def _run() -> None:
            self._update(job_id, status=JobStatus.running)
            try:
                result = worker()
                self._update(job_id, status=JobStatus.completed, result=result)
            except Exception as error:  # noqa: BLE001 — frontera de job
                self._update(job_id, status=JobStatus.failed, error=str(error))

        Thread(target=_run, name=f"job-{job_type}-{job_id[:8]}", daemon=True).start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _update(
        self,
        job_id: str,
        *,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.status = status
            job.updated_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error


cola_trabajos = JobQueue()
