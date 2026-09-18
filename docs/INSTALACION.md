# Guía de instalación — Agro Asistente (Fase 1)

## Requisitos

- Python 3.11 o superior
- Node.js 18 o superior
- MySQL 8 (motor objetivo del curso)
- Git
- PowerShell en Windows

## 1. Clonar o copiar el proyecto

```powershell
cd "D:\Taller de proyectos\agro-asistente"
```

## 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Editar `.env` con las credenciales locales de MySQL. **Nunca** colocar API keys en el código fuente.

Levantar el API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Comprobar:

```powershell
curl http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "agro-asistente",
  "phase": "1",
  "architecture": "hexagonal"
}
```

El campo `mysql` indica si el backend pudo conectar a la base configurada (`connected` o `disconnected`). En Fase 1 el endpoint `/health` permanece operativo aunque MySQL no esté disponible.

## 3. Base de datos

Crear la base y las tablas con el esquema reproducible:

```powershell
mysql -u root -p < ..\database\schema.sql
```

En entornos XAMPP, el cliente suele estar en `C:\xampp\mysql\bin\mysql.exe` y el usuario `root` puede no tener contraseña:

```powershell
& "C:\xampp\mysql\bin\mysql.exe" -u root < ..\database\schema.sql
```

El esquema es compatible con MySQL 8. Si se usa MariaDB localmente para desarrollo, se emplea collation `utf8mb4_unicode_ci`.

## 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abrir [http://localhost:5173](http://localhost:5173). La página inicial consulta `GET /health` del backend.

Registro de agricultor (HU-01): [http://localhost:5173/register](http://localhost:5173/register)

Inicio de sesión (HU-02): [http://localhost:5173/login](http://localhost:5173/login)

Contexto agrícola (HU-03): [http://localhost:5173/context](http://localhost:5173/context)

Consulta agrícola (HU-04): [http://localhost:5173/query](http://localhost:5173/query)

Base de conocimiento (HU-05): [http://localhost:5173/knowledge](http://localhost:5173/knowledge)

## 5. Pruebas

Desde `backend/` con el entorno virtual activo:

```powershell
pytest
```

## 6. Probar HU-01 (registro)

Con el backend en marcha:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d "{\"names\":\"Juan\",\"last_names\":\"Pérez\",\"email\":\"juan@example.com\",\"password\":\"Password123!\"}"
```

Respuesta esperada: HTTP 201 con `id`, `names`, `last_names` y `email`. No se devuelve la contraseña.

Un segundo registro con el mismo correo debe responder HTTP 409:

```json
{"detail": "El correo electrónico ya está registrado"}
```

En la tabla `farmers`, `password_hash` debe comenzar por `$2` (bcrypt).

## 7. Probar HU-02 (inicio de sesión)

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"juan@example.com\",\"password\":\"Password123!\"}"
```

Respuesta esperada: HTTP 200 con `access_token`, `token_type: bearer` y el objeto `farmer`. No se devuelve la contraseña.

Contraseña incorrecta o correo inexistente: HTTP 401

```json
{"detail": "Credenciales inválidas"}
```

Configuración JWT en `backend/.env`:

- `JWT_SECRET` — secreto de firma (no versionar el valor real)
- `JWT_ALGORITHM` — `HS256`
- `JWT_EXPIRE_MINUTES` — minutos de validez del token

## 8. Probar HU-03 (contexto agrícola)

Con un token de login:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/contexts `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"plot_name\":\"Parcela 1\",\"crop\":\"papa\",\"region\":\"Huancayo\",\"notes\":\"Campana seca\"}"

curl http://127.0.0.1:8000/api/v1/contexts -H "Authorization: Bearer TOKEN"

curl -X POST http://127.0.0.1:8000/api/v1/contexts/ID/select -H "Authorization: Bearer TOKEN"
```

Sin token o con JWT inválido/expirado: HTTP 401. Un agricultor no puede listar ni seleccionar contextos de otro: el listado queda filtrado y la selección ajena responde HTTP 404.

Pantalla: [http://localhost:5173/context](http://localhost:5173/context)

## 9. Probar HU-04 (consulta agrícola)

Requisitos: agricultor autenticado y un contexto agrícola seleccionado.

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/queries `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"text\":\"¿Qué puedo hacer para mejorar el cultivo de papa?\"}"
```

Respuesta esperada: HTTP 201 con `id`, `text`, `answer`, `generation_method: template`, `created_at` y el `context` utilizado (cultivo, región, predio). No se devuelve contraseña ni el token.

Sin token o con JWT inválido/expirado: HTTP 401. Consulta vacía: HTTP 422. Agricultor sin contexto seleccionado: HTTP 409.

La respuesta es una plantilla de PMV1 construida con las evidencias RAG (HU-06). No hay un modelo de IA externo.

Pantalla: [http://localhost:5173/query](http://localhost:5173/query)

## 10. Probar HU-05 (base de conocimiento)

Con un token de login:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/knowledge/ingest `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"Riego de papa\",\"topic\":\"papa\",\"content\":\"# Material de prueba HU-05\\nRiego frecuente en floración.\"}"

curl http://127.0.0.1:8000/api/v1/knowledge/documents -H "Authorization: Bearer TOKEN"
```

Respuesta esperada de ingesta: HTTP 201 con `id`, `title`, `topic`, `source_path`, `content_hash`, `chunk_count: 0`, `status: registered`.

El mismo contenido otra vez: HTTP 409. Sin token: HTTP 401. Contenido vacío: HTTP 422.

Hay ejemplos en `knowledge/prueba-riego-papa.md` y `knowledge/prueba-heladas-sierra.md`. La ingesta no indexa en Chroma; eso es HU-06.

Pantalla: [http://localhost:5173/knowledge](http://localhost:5173/knowledge)

## 11. Probar HU-06 (RAG básico)

Requisitos: agricultor autenticado, contexto seleccionado y al menos un documento incorporado.

1. Incorporar un documento (HU-05).
2. Indexarlo en Chroma:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/knowledge/index `
  -H "Authorization: Bearer TOKEN"
```

Respuesta esperada: HTTP 200 con `indexed_documents`, `total_chunks`, `collection: agro_knowledge_pmv1` y `chunk_count` actualizado.

3. Consultar con un texto relacionado:

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/queries `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"text\":\"¿Cómo riego la papa en floración?\"}"
```

Respuesta esperada: HTTP 201 con `answer` basada en la base de conocimiento, `evidences` (documento, fragmento, relevancia) y `generation_method: template`.

Sin resultados relevantes: `evidences` vacío y el texto indica que no se encontró información suficiente. No se inventa evidencia.

Sin token: HTTP 401. Consulta vacía: HTTP 422. Sin contexto seleccionado: HTTP 409.

Los embeddings de PMV1 son léxicos locales (hashing de tokens). No hay API externa de IA todavía.

Pantalla: [http://localhost:5173/query](http://localhost:5173/query)

## Variables de entorno

Ver `backend/.env.example`. Las credenciales del futuro proveedor de embeddings (`EMBEDDING_API_KEY`) no deben versionarse. El archivo `.env` está en `.gitignore`.

Configuración relevante de HU-06:

- `CHROMA_PERSIST_DIR` — directorio local de Chroma (`./chroma_data`)
- `CHROMA_COLLECTION` — `agro_knowledge_pmv1`
- `RAG_TOP_K` — cantidad de fragmentos a recuperar (3)
- `RAG_MIN_SIMILARITY` — umbral mínimo de similitud (0.12)
- `CHUNK_SIZE` — tamaño máximo de fragmento en caracteres (500)
- `EMBEDDING_PROVIDER` — `local` (PMV1) o `external` (placeholder de Sesión 3)

## Puertos locales

| Servicio | URL |
|---|---|
| Backend FastAPI | http://127.0.0.1:8000 |
| Documentación OpenAPI | http://127.0.0.1:8000/docs |
| Frontend Vite | http://localhost:5173 |
