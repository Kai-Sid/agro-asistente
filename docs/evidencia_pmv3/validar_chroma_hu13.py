"""Valida en Chroma que desactivar retira fragmentos y reactivar los reindexa."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.infrastructure.composition import build_container  # noqa: E402
from app.infrastructure.adapters.output.mysql.procedures import (  # noqa: E402
    MysqlStoredProcedureGateway,
)

OUT = Path(__file__).resolve().parent
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    container = build_container()
    store = container.puerto_almacen_vectores
    procedures = MysqlStoredProcedureGateway(container.session_factory)
    docs = procedures.call("sp_admin_documentos_listar")
    if not docs:
        print("No hay documentos para validar Chroma")
        return 1
    doc = docs[0]
    doc_id = str(doc["id"])
    report = {"stamp": stamp, "document_id": doc_id, "steps": []}

    def count_for_doc() -> int:
        # Chroma get by metadata filter
        raw = store._collection.get(where={"document_id": doc_id}, include=["documents", "metadatas"])
        return len(raw.get("ids") or [])

    before_status = str(doc.get("estado"))
    # Ensure active and indexed
    if before_status.upper() != "ACTIVO":
        procedures.call("sp_admin_documento_estado_actualizar", (int(doc_id), "ACTIVO"))
        container.puerto_indexar_conocimiento.ejecutar()
    else:
        container.puerto_indexar_conocimiento.ejecutar()

    active_count = count_for_doc()
    report["steps"].append({"phase": "activo", "chunks": active_count})

    # Deactivate + delete from index (same as API)
    procedures.call("sp_admin_documento_estado_actualizar", (int(doc_id), "INACTIVO"))
    store.delete_by_document(doc_id)
    inactive_count = count_for_doc()
    report["steps"].append({"phase": "inactivo", "chunks": inactive_count})

    # Reactivate + reindex
    procedures.call("sp_admin_documento_estado_actualizar", (int(doc_id), "ACTIVO"))
    indexed = container.puerto_indexar_conocimiento.ejecutar()
    reactivated_count = count_for_doc()
    report["steps"].append(
        {
            "phase": "reactivado",
            "chunks": reactivated_count,
            "indexed_total_fragments": indexed.total_fragmentos,
        }
    )

    report["ok"] = active_count > 0 and inactive_count == 0 and reactivated_count > 0
    out = OUT / f"chroma_hu13_{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("WROTE", out)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
