# Runbook — Backup y restauración (MySQL + Chroma)

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente |
| Objetivo FURPS | M02 Reliability |
| RTO orientativo (piloto) | ≤ 4 h en laboratorio académico |
| RPO orientativo (piloto) | Último backup exitoso (diario recomendado) |

---

## Alcance

| Activo | Ubicación típica | Crítico |
|---|---|---|
| MySQL/MariaDB `agro_asistente` | Servidor DB local o managed | Sí |
| Archivos Markdown knowledge | `knowledge/` | Sí |
| Índice vectorial Chroma | `backend/chroma_data/` (o `CHROMA_PERSIST_DIR`) | Sí (reconstruible con `/knowledge/index`) |
| Modelos `.joblib` | rutas en repo / `CLASIFICADOR_MODELO_RUTA` | Sí (versionados en Git si aplica) |
| `.env` / secretos | fuera de Git | Sí (no versionar) |

Chroma es **reconstruible** desde documentos + `POST /api/v1/knowledge/index`. Priorizar dump MySQL + `knowledge/`.

---

## Script automatizado (Windows)

Desde la raíz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\database\scripts\backup.ps1
```

Genera dumps en `./backups/`.

## Backup MySQL

### Windows (PowerShell) — mysqldump

```powershell
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
$out = ".\backups\mysql-agro_asistente-$fecha.sql"
New-Item -ItemType Directory -Force -Path .\backups | Out-Null
# Ajusta usuario/host/puerto. Ejemplo XAMPP:
& "C:\xampp\mysql\bin\mysqldump.exe" -u root --databases agro_asistente --routines --triggers -r $out
```

Con contraseña:

```powershell
& "C:\xampp\mysql\bin\mysqldump.exe" -u root -p --databases agro_asistente -r $out
```

### Verificar

```powershell
Get-Item $out | Select-Object FullName, Length, LastWriteTime
# El archivo debe ser > 0 bytes y contener CREATE TABLE
Select-String -Path $out -Pattern "CREATE TABLE" | Select-Object -First 3
```

---

## Backup knowledge + Chroma

```powershell
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
Compress-Archive -Path .\knowledge -DestinationPath ".\backups\knowledge-$fecha.zip" -Force
if (Test-Path .\backend\chroma_data) {
  Compress-Archive -Path .\backend\chroma_data -DestinationPath ".\backups\chroma-$fecha.zip" -Force
}
```

---

## Restauración MySQL (lab)

**Advertencia:** destruye datos actuales de la base restaurada.

```powershell
# 1) Detener el API (uvicorn) para evitar escrituras concurrentes.
# 2) Restaurar:
& "C:\xampp\mysql\bin\mysql.exe" -u root < .\backups\mysql-agro_asistente-YYYYMMDD-HHMMSS.sql
# 3) Arrancar API y comprobar:
curl http://127.0.0.1:8000/health
```

Checklist post-restore:

1. `GET /health` → `status=ok` (y MySQL `connected` si health detallado).
2. Login de un agricultor de prueba.
3. `GET /api/v1/contexts` con JWT.
4. `GET /api/v1/knowledge/documents`.

---

## Restauración knowledge / Chroma

```powershell
Expand-Archive -Path .\backups\knowledge-YYYYMMDD-HHMMSS.zip -DestinationPath . -Force
# Chroma: restaurar zip O reindexar:
# POST /api/v1/knowledge/index (JWT; rol curator si KNOWLEDGE_MUTATION_POLICY=curators_only)
```

---

## Ensayo dry-run (evidencia M02)

| Paso | Resultado esperado | Fecha / operador |
|---|---|---|
| Crear carpeta `backups/` | OK | |
| `mysqldump` genera `.sql` > 0 B | OK / SKIP si MySQL no disponible | |
| Zip `knowledge/` | OK | |
| (Opcional) restore en instancia lab | Login + list contexts | |

Si MySQL no está disponible en el entorno de auditoría, dejar constancia **SKIP** — no inventar restore exitoso.

---

## Frecuencia recomendada (piloto)

- Diario: dump MySQL + zip `knowledge/`.
- Antes de cambios de schema o remediaciones mayores: backup manual adicional.
- Retención mínima piloto: 7 copias diarias.
