"""Cola en memoria para trabajos largos."""

import time

from app.infrastructure.job_queue import JobQueue, JobStatus


def test_enqueue_completa_con_resultado() -> None:
    cola = JobQueue()

    def worker() -> dict:
        return {"ok": True, "n": 1}

    job = cola.enqueue("demo", worker, farmer_id="f1")
    assert job.status in {JobStatus.queued, JobStatus.running, JobStatus.completed}
    deadline = time.time() + 2.0
    while time.time() < deadline:
        actual = cola.get(job.id)
        assert actual is not None
        if actual.status in {JobStatus.completed, JobStatus.failed}:
            break
        time.sleep(0.05)
    final = cola.get(job.id)
    assert final is not None
    assert final.status == JobStatus.completed
    assert final.result == {"ok": True, "n": 1}
    assert final.farmer_id == "f1"


def test_enqueue_marca_failed_si_worker_falla() -> None:
    cola = JobQueue()

    def worker() -> dict:
        raise RuntimeError("boom")

    job = cola.enqueue("fail", worker)
    deadline = time.time() + 2.0
    while time.time() < deadline:
        actual = cola.get(job.id)
        assert actual is not None
        if actual.status in {JobStatus.completed, JobStatus.failed}:
            break
        time.sleep(0.05)
    final = cola.get(job.id)
    assert final is not None
    assert final.status == JobStatus.failed
    assert "boom" in (final.error or "")
