# Auditoría de infraestructura y dependencias

## Alcance y método

Se revisaron únicamente los artefactos de infraestructura versionados disponibles: `render.yaml`, `database/schema.sql`, `insertar_datos.py`, `backend/.env.example`, `backend/app/infrastructure/config/settings.py` y `backend/app/main.py`. No se encontraron Dockerfiles, archivos Docker Compose ni pipelines CI/CD en el listado versionado.

## 1. Inventario de servicios desplegados

| Servicio | Tipo | Runtime/Imagen | Comando de build | Comando de inicio | Evidencia |
|---|---|---|---|---|---|
| `agro-asistente-api` | Web | `python` en Render | `pip install -r requirements.txt` | `python -m app.main` | `render.yaml` |
| `agro-asistente-web` | Estático | `static` en Render | `npm install && npm run build` | No aplica; se publica `frontend/dist` | `render.yaml` |
| Base de datos relacional | Base de datos | No evidenciado como servicio administrado en el Blueprint | No evidenciado | No evidenciado | `render.yaml` declara explícitamente que no crea MySQL; `database/schema.sql` define MySQL/TiDB-compatible SQL |
| Ollama / generación | Servicio externo | No evidenciado | No evidenciado | No evidenciado | `render.yaml` no publica Ollama; `OLLAMA_BASE_URL` se configura como variable externa |

Notas:

- `agro-asistente-api` usa `rootDir: backend` y un plan `free` declarado en `render.yaml`.
- El backend lee el puerto mediante `PORT`, con `8000` como respaldo local según `backend/app/main.py` y `backend/.env.example`.
- El servicio web tiene una ruta rewrite de `/*` a `/index.html`.

## 2. Herramientas DevOps detectadas

| Herramienta/capacidad | Evidencia | Estado |
|---|---|---|
| Render Blueprint | `render.yaml` | Detectado para dos servicios web/estáticos: API y frontend |
| npm | `frontend/package.json`; `render.yaml` | Detectado como sistema de dependencias y construcción del frontend |
| pip / requirements.txt | `backend/requirements.txt`; `render.yaml` | Detectado para instalación de dependencias Python |
| Uvicorn | `backend/requirements.txt`; `backend/app/main.py` | Detectado como servidor ASGI del backend |
| Docker o Docker Compose | No evidenciado | No se encontró Dockerfile ni archivo Compose en el listado versionado |
| CI/CD | No evidenciado | No se encontró pipeline ni directorio de configuración versionado |

## 3. Base de datos

| Campo | Resultado | Evidencia |
|---|---|---|
| Motor | MySQL; el esquema declara compatibilidad con MariaDB de desarrollo y el script de datos usa TiDB Cloud | `database/schema.sql`; `insertar_datos.py` |
| Versión declarada | `MySQL 8` y `MariaDB` son mencionados en comentarios, pero no se declara una versión exacta de producción. | `database/schema.sql` |
| Servicio desplegado por Render | No | `render.yaml` declara: “no crea MySQL” |
| Creación del esquema | `CREATE DATABASE IF NOT EXISTS`; `USE`; creación de siete tablas con claves primarias, claves foráneas y motor InnoDB | `database/schema.sql` |
| Tablas principales | `agricultores`, `contextos_agricolas`, `consultas`, `respuestas`, `documentos_conocimiento`, `evidencias` | `database/schema.sql` |
| Migración/ajuste incremental | `evidencias.titulo_documento` se agrega dinámicamente con SQL si no existe | `database/schema.sql` |
| Datos iniciales | No hay script SQL de seed. `insertar_datos.py` elimina datos de prueba y carga 500 agricultores, 500 contextos y 500 consultas | `insertar_datos.py` |
| Aplicación del esquema | No evidenciado: no hay comando, migrador, pipeline o tarea documentada que aplique `database/schema.sql` | No evidenciado |
| Aplicación de datos iniciales | El script se ejecuta manualmente con Python, según su propio contenido; no hay integración de despliegue evidenciada | `insertar_datos.py` |

Nota: el archivo `agro.mwb` es un modelo de MySQL Workbench, pero el listado no evidencia cómo se exporta o aplica.

## 4. Almacenamiento, volúmenes o discos persistentes

| Elemento | Estado declarado | Evidencia |
|---|---|---|
| Disco persistente de Render | No evidenciado; el Blueprint no declara volúmenes ni discos | `render.yaml` |
| Chroma | Usa `CHROMA_PERSIST_DIR=./chroma_data` local/configurable | `backend/.env.example`; `backend/app/infrastructure/config/settings.py` |
| Persistencia de Chroma en despliegue | No evidenciado; no existe disco persistente asociado ni mecanismo de backup/versionado declarado | `render.yaml`; `backend/.env.example` |
| Archivos de conocimiento | `KNOWLEDGE_DIR=../knowledge` | `backend/.env.example`; `backend/app/infrastructure/config/settings.py` |
| Base de datos | Se espera una base externa; no se declara proveedor, volumen ni persistencia en el Blueprint | `render.yaml`; `database/schema.sql` |

## 5. Variables de entorno declaradas en la infraestructura

### API según `render.yaml`

- `GENERATION_PROVIDER`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_DIMENSION`
- `CHROMA_COLLECTION`
- `RAG_TOP_K`
- `RAG_MIN_SIMILARITY`
- `CHUNK_SIZE`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `CLASIFICADOR_MARGEN_MINIMO`
- `MYSQL_PORT`
- `MYSQL_DATABASE`
- `SENAMHI_WIS2_BASE_URL`
- `SENAMHI_WIS2_COLLECTION`
- `SENAMHI_WIS2_TIMEOUT_SECONDS`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `JWT_SECRET`
- `CORS_ORIGINS`
- `OLLAMA_BASE_URL`

Las últimas variables de esta lista están marcadas con `sync: false`, por lo que sus valores deben completarse fuera del repositorio.

### Frontend según `render.yaml`

- `VITE_API_BASE_URL`

Esta variable está marcada con `sync: false`.

### Variables adicionales declaradas en `backend/.env.example`

- `APP_NAME`
- `APP_ENV`
- `API_HOST`
- `API_PORT`
- `PORT`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `KNOWLEDGE_DIR`
- `CHROMA_PERSIST_DIR`
- `CHROMA_COLLECTION`
- `RAG_TOP_K`
- `RAG_MIN_SIMILARITY`
- `CHUNK_SIZE`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_DIMENSION`
- `EMBEDDING_API_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `GENERATION_PROVIDER`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `RUN_OLLAMA_INTEGRATION_TESTS`
- `SENAMHI_WIS2_BASE_URL`
- `SENAMHI_WIS2_COLLECTION`
- `SENAMHI_WIS2_TIMEOUT_SECONDS`
- `CORS_ORIGINS`
- `CLASIFICADOR_MARGEN_MINIMO`
- `CLASIFICADOR_MODELO_RUTA`

## 6. Riesgos potenciales y elementos obsoletos

| Riesgo/elemento | Evidencia | Observación |
|---|---|---|
| Credenciales de base de datos en código versionado | `insertar_datos.py` contiene usuario, contraseña y host de conexión a TiDB Cloud | Riesgo crítico de exposición de secretos; deben rotarse y retirar del repositorio |
| Verificación TLS con `check_hostname: False` | `insertar_datos.py` configura SSL con `check_hostname: False` | Reduce la validación de identidad del certificado; el riesgo no puede cuantificarse sin más configuración, pero es potencial |
| Contraseña JWT por defecto insegura | `backend/app/infrastructure/config/settings.py` usa `change-me-in-local-env-do-not-use-in-production` | Solo debe usarse localmente; Render exige `JWT_SECRET` mediante `sync: false`, pero no demuestra que el valor haya sido configurado |
| Script destructivo de datos | `insertar_datos.py` ejecuta `TRUNCATE` sobre varias tablas antes de insertar datos ficticios | Puede borrar datos reales si se ejecuta contra el entorno equivocado |
| Datos ficticios masivos | `insertar_datos.py` inserta 500 registros con hashes falsos y correos de prueba | No debe ejecutarse como seed de producción |
| Ollama no desplegado por el Blueprint | `render.yaml` declara que no publica Ollama y deja `OLLAMA_BASE_URL` como variable externa | El servicio puede quedar no disponible si no se proporciona una instancia externa |
| Dependencia de rutas locales | `CHROMA_PERSIST_DIR=./chroma_data` y `KNOWLEDGE_DIR=../knowledge` | Sin disco persistente ni estrategia de almacenamiento declarada para Render |
| Obsolescencia: No evidenciado | No se encontró una fecha de revisión, reemplazo o retiro declarado | No se puede afirmar obsolescencia documental sin más evidencia |

## 7. Elementos faltantes o no definidos

- Pruebas automáticas en CI: **No evidenciado**.
- Pipeline CI/CD: **No evidenciado**.
- Docker/Dockerfile/Compose: **No evidenciado**.
- Provisionamiento de MySQL, TiDB o MariaDB en Render: **No evidenciado**; el Blueprint indica que no lo crea.
- Versión exacta de Python en `render.yaml`: **No evidenciado**.
- Versión exacta de Node/npm en `render.yaml` o configuración del frontend: **No evidenciado**.
- Versión exacta de la base de datos desplegada: **No evidenciado**.
- Comando de aplicación de `database/schema.sql`: **No evidenciado**.
- Comando o proceso de migraciones: **No evidenciado**.
- Seed seguro o idempotente para producción: **No evidenciado**.
- Provisión de Ollama en Render: **No evidenciado**.
- Disco o volumen persistente para Chroma: **No evidenciado**.
- Estrategia de backup/restauración: **No evidenciado**.
- Estrategia de secretos distinta de las variables `sync: false`: **No evidenciado**.
- Healthcheck del frontend: **No evidenciado**; el único healthcheck declarado es `/health` del API.
- Healthcheck de la base de datos: **No evidenciado**.
- Healthcheck de Ollama: **No evidenciado**.
- Start command explícito para el servicio estático: **No evidenciado**; utiliza publicación de `frontend/dist`.
- Escaneo automatizado de vulnerabilidades o secretos: **No evidenciado**.
- Política de actualización de dependencias: **No evidenciado**.
