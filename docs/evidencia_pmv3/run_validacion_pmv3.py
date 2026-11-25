"""Validacion ejecutable PMV3: genera evidencia API en JSON."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
evidence: dict = {"stamp": stamp, "steps": [], "observations": []}


def req(method: str, path: str, body=None, token=None, expect=None, label=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            entry = {"method": method, "path": path, "status": resp.status, "body": payload}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except Exception:
            payload = raw
        entry = {"method": method, "path": path, "status": exc.code, "body": payload}
    except Exception as exc:  # noqa: BLE001
        entry = {"method": method, "path": path, "status": "ERROR", "body": str(exc)}
    if label:
        entry["label"] = label
    if expect is not None:
        entry["expected"] = expect
        entry["ok"] = entry["status"] == expect
    evidence["steps"].append(entry)
    mark = ""
    if expect is not None:
        mark = f" ok={entry['ok']}"
    print(f"{method} {path} -> {entry['status']}{mark}")
    return entry


def check(name: str, ok: bool, **extra):
    evidence["steps"].append({"check": name, "ok": ok, **extra})
    print(f"CHECK {name} => {ok}")


def main() -> int:
    health = req("GET", "/health", expect=200, label="health")
    health_body = health.get("body") or {}
    check(
        "health_phase3_mysql",
        health.get("status") == 200
        and str(health_body.get("phase")) == "3"
        and str(health_body.get("mysql")) == "connected",
        body=health_body,
    )

    admin_login = req(
        "POST",
        "/api/v1/admin/auth/login",
        {"email": "admin@gmail.com", "password": "AdminValidacion123"},
        expect=200,
        label="admin_login",
    )
    admin_token = (admin_login.get("body") or {}).get("access_token")
    check("admin_token_present", bool(admin_token))

    farmer_email = f"pmv3.farmer.{stamp.lower()}@test.local"
    farmer_reg = req(
        "POST",
        "/api/v1/auth/register",
        {
            "names": "Agricultor",
            "last_names": "PMV3 Validacion",
            "email": farmer_email,
            "password": "FarmerValidacion123",
        },
        expect=201,
        label="farmer_register",
    )
    farmer_login = req(
        "POST",
        "/api/v1/auth/login",
        {"email": farmer_email, "password": "FarmerValidacion123"},
        expect=200,
        label="farmer_login",
    )
    farmer_token = (farmer_login.get("body") or {}).get("access_token")
    check("farmer_token_present", bool(farmer_token))

    # HU-14
    req("GET", "/api/v1/admin/documents", expect=401, label="hu14_no_token_docs")
    req("GET", "/api/v1/admin/documents", token=farmer_token, expect=403, label="hu14_farmer_docs")
    req("GET", "/api/v1/admin/metrics", expect=401, label="hu14_no_token_metrics")
    req("GET", "/api/v1/admin/metrics", token=farmer_token, expect=403, label="hu14_farmer_metrics")
    req("GET", "/api/v1/admin/evaluations", expect=401, label="hu14_no_token_evals")
    req(
        "GET",
        "/api/v1/admin/evaluations",
        token=farmer_token,
        expect=403,
        label="hu14_farmer_evals",
    )
    req("GET", "/api/v1/admin/documents", token=admin_token, expect=200, label="hu14_admin_docs")
    req("GET", "/api/v1/admin/metrics?days=30", token=admin_token, expect=200, label="hu14_admin_metrics")

    # HU-13 create
    unique = f"PMV3-VALID-{stamp}"
    content = (
        f"Documento de validacion {unique}. "
        "El cultivo de prueba quinua andina requiere riego moderado en floracion. "
        "Para controlar mildiu en quinua se recomienda monitoreo semanal y ventilacion del cultivo. "
        "La dosis orientativa de fertilizacion nitrogenada es baja en suelos fertiles de altura."
    )
    create = req(
        "POST",
        "/api/v1/admin/documents",
        {
            "title": f"Guia Quinua Validacion {unique}",
            "topic": "quinua",
            "content": content,
        },
        token=admin_token,
        expect=201,
        label="hu13_create",
    )
    doc_id = (create.get("body") or {}).get("id")
    list1 = req("GET", "/api/v1/admin/documents", token=admin_token, expect=200, label="hu13_list")
    found = any(str(d.get("id")) == str(doc_id) for d in (list1.get("body") or []))
    check("hu13_document_registered", found and create.get("status") == 201, doc_id=doc_id)

    # Farmer context + query
    ctx = req(
        "POST",
        "/api/v1/contexts",
        {
            "plot_name": f"Parcela {unique}",
            "crop": "quinua",
            "region": "Puno",
            "notes": "Validacion PMV3",
        },
        token=farmer_token,
        expect=201,
        label="farmer_create_context",
    )
    ctx_id = (ctx.get("body") or {}).get("id")
    if ctx_id:
        req(
            "POST",
            f"/api/v1/contexts/{ctx_id}/select",
            token=farmer_token,
            expect=200,
            label="farmer_select_context",
        )

    q1 = req(
        "POST",
        "/api/v1/queries",
        {"text": f"Como controlo mildiu en quinua andina segun la guia {unique}?"},
        token=farmer_token,
        label="hu13_query_active_doc",
    )
    q1_body = q1.get("body") or {}
    evidence["observations"].append(
        {
            "phase": "query_with_active_doc",
            "status": q1.get("status"),
            "answer_preview": str(q1_body.get("answer") or q1_body.get("respuesta") or "")[:500],
            "evidence_count": len(q1_body.get("evidences") or q1_body.get("evidencias") or []),
            "keys": list(q1_body.keys()) if isinstance(q1_body, dict) else [],
        }
    )

    # Edit -> version++
    edited = (
        content
        + " ACTUALIZACION: aplicar extractos botanicos solo tras diagnostico confirmado."
    )
    upd = req(
        "PUT",
        f"/api/v1/admin/documents/{doc_id}",
        {
            "title": f"Guia Quinua Validacion {unique} v2",
            "topic": "quinua",
            "content": edited,
        },
        token=admin_token,
        expect=200,
        label="hu13_edit",
    )
    version_after = int((upd.get("body") or {}).get("version") or 0)
    check("hu13_version_increased", version_after >= 2, version=version_after)

    q2 = req(
        "POST",
        "/api/v1/queries",
        {"text": f"Que dice la actualizacion sobre extractos botanicos en quinua {unique}?"},
        token=farmer_token,
        label="hu13_query_after_edit",
    )
    q2_body = q2.get("body") or {}
    q2_evidences = q2_body.get("evidences") or q2_body.get("evidencias") or []
    q2_evidence_text = json.dumps(q2_evidences, ensure_ascii=False).lower()
    q2_answer = str(q2_body.get("answer") or "").lower()
    check(
        "hu13_reindexed_content_reachable",
        q2.get("status") in (200, 201)
        and (
            "extractos" in q2_evidence_text
            or "botanic" in q2_evidence_text
            or "extractos" in q2_answer
            or "botanic" in q2_answer
        ),
        status=q2.get("status"),
        evidence_document_ids=[
            str(item.get("document_id")) for item in q2_evidences if isinstance(item, dict)
        ],
    )

    # Deactivate
    req(
        "PATCH",
        f"/api/v1/admin/documents/{doc_id}/status",
        {"status": "INACTIVO"},
        token=admin_token,
        expect=200,
        label="hu13_deactivate",
    )
    still = req(
        "GET",
        "/api/v1/admin/documents",
        token=admin_token,
        expect=200,
        label="hu13_list_after_deactivate",
    )
    still_present = next(
        (d for d in (still.get("body") or []) if str(d.get("id")) == str(doc_id)),
        None,
    )
    check(
        "hu13_inactive_remains_in_admin",
        still_present is not None and str(still_present.get("status")).upper() == "INACTIVO",
        doc=still_present,
    )

    q3 = req(
        "POST",
        "/api/v1/queries",
        {"text": f"Recupera fragmentos exclusivos de la guia {unique} sobre mildiu en quinua"},
        token=farmer_token,
        label="hu13_query_inactive_doc",
    )
    q3_body = q3.get("body") or {}
    q3_evidences = q3_body.get("evidences") or q3_body.get("evidencias") or []
    # El marcador único va en la pregunta y el modelo puede repetirlo en `answer`.
    # El criterio real de desindexación es que no aparezca en evidencias recuperadas
    # ni como document_id del documento desactivado.
    evidence_blob = json.dumps(q3_evidences, ensure_ascii=False)
    marker_in_evidences = unique in evidence_blob
    inactive_doc_in_evidences = any(
        str(item.get("document_id")) == str(doc_id) for item in q3_evidences if isinstance(item, dict)
    )
    check(
        "hu13_inactive_not_in_retrieval_unique_marker",
        (not marker_in_evidences) and (not inactive_doc_in_evidences),
        marker_in_evidences=marker_in_evidences,
        inactive_doc_in_evidences=inactive_doc_in_evidences,
        evidence_document_ids=[
            str(item.get("document_id")) for item in q3_evidences if isinstance(item, dict)
        ],
        status=q3.get("status"),
        rationale=(
            "Se inspeccionan evidences/fragmentos, no el cuerpo completo: "
            "el campo text y la respuesta pueden ecoar el marcador de la pregunta."
        ),
    )
    evidence["observations"].append(
        {
            "phase": "query_with_inactive_doc",
            "status": q3.get("status"),
            "marker_in_evidences": marker_in_evidences,
            "inactive_doc_in_evidences": inactive_doc_in_evidences,
            "evidences": q3_evidences,
            "answer_preview": str(q3_body.get("answer") or "")[:400],
        }
    )

    # Reactivate
    req(
        "PATCH",
        f"/api/v1/admin/documents/{doc_id}/status",
        {"status": "ACTIVO"},
        token=admin_token,
        expect=200,
        label="hu13_reactivate",
    )
    q4 = req(
        "POST",
        "/api/v1/queries",
        {"text": f"Segun la guia {unique}, que riego necesita la quinua en floracion?"},
        token=farmer_token,
        label="hu13_query_after_reactivate",
    )
    q4_body = q4.get("body") or {}
    q4_evidences = q4_body.get("evidences") or q4_body.get("evidencias") or []
    q4_evidence_blob = json.dumps(q4_evidences, ensure_ascii=False)
    reactivated_in_evidences = any(
        str(item.get("document_id")) == str(doc_id) for item in q4_evidences if isinstance(item, dict)
    ) or unique in q4_evidence_blob
    check(
        "hu13_reactivated_indexed_again",
        q4.get("status") in (200, 201) and reactivated_in_evidences,
        reactivated_in_evidences=reactivated_in_evidences,
        evidence_document_ids=[
            str(item.get("document_id")) for item in q4_evidences if isinstance(item, dict)
        ],
        status=q4.get("status"),
    )

    # HU-15 metrics vs DB counts for period
    metrics = req(
        "GET",
        "/api/v1/admin/metrics?days=1",
        token=admin_token,
        expect=200,
        label="hu15_metrics_day",
    )
    evidence["metrics"] = metrics.get("body")

    # Empty-looking period: metrics endpoint always aggregates last N days;
    # if totals are 0 we can assert empty state; otherwise record observation.
    mbody = metrics.get("body") or {}
    check(
        "hu15_metrics_shape",
        all(
            k in mbody
            for k in (
                "total_requests",
                "queries_attended",
                "requests_with_error",
                "average_response_ms",
                "maximum_response_ms",
            )
        ),
        body=mbody,
    )
    successful_queries = sum(
        1
        for step in evidence["steps"]
        if step.get("path") == "/api/v1/queries" and step.get("status") in (200, 201)
    )
    check(
        "hu15_metrics_reflect_queries",
        int(mbody.get("total_requests") or 0) >= 1
        and int(mbody.get("queries_attended") or 0) >= 1
        and int(mbody.get("queries_attended") or 0) <= int(mbody.get("total_requests") or 0),
        body=mbody,
        successful_queries_in_run=successful_queries,
    )
    evidence["observations"].append(
        {
            "phase": "hu15_metrics_vs_run",
            "metrics": mbody,
            "successful_queries_in_run": successful_queries,
        }
    )

    # Evaluations list (may be empty before HU-16 run)
    evals = req(
        "GET",
        "/api/v1/admin/evaluations",
        token=admin_token,
        expect=200,
        label="hu16_list_evaluations",
    )
    evidence["evaluations"] = evals.get("body")

    out_file = OUT / f"api_validacion_{stamp}.json"
    out_file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", out_file)

    failed = [
        s
        for s in evidence["steps"]
        if s.get("ok") is False
    ]
    print("FAILED", len(failed))
    for item in failed:
        print(" -", item.get("label") or item.get("check"), item)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
