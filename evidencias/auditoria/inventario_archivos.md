# Inventario de archivos del proyecto

## Alcance y método

Este inventario se construye únicamente a partir de `git ls-files` y del listado entregado por el repositorio. Por ello, excluye archivos ignorados y carpetas no versionadas. No se infieren comportamientos que no estén respaldados por nombres de archivos o rutas observables.

## Carpetas de primer nivel y archivos sueltos

| Carpeta o archivo raíz | Propósito | Evidencia (archivos que lo demuestran) | Confianza |
|---|---|---|---|
| `auditoria_etiquetas_dataset_trabajo/` | Auditoría y revisión de etiquetas del dataset de trabajo, con casos dudosos documentados. | `auditoria_etiquetas_dataset_trabajo/INFORME_AUDITORIA_ETIQUETAS.md`; `auditoria_etiquetas_dataset_trabajo/lista_casos_dudosos.jsonl` | Alta |
| `auditoria_hu07_v2/` | Preparación, ejecución independiente y cierre humano de una auditoría del piloto HU07 v2. | `auditoria_hu07_v2/INFORME_AUDITORIA_PILOTO_HU07.md`; `auditoria_hu07_v2/revision_independiente/`; `auditoria_hu07_v2/cierre_revision_humana/` | Alta |
| `backend/` | Implementación principal del backend, organizada por aplicación, dominio e infraestructura, con pruebas y experimentos. | `backend/app/`; `backend/tests/`; `backend/evaluation/`; `backend/clasificacion/` | Alta |
| `cierre_observaciones_entrenamiento_hu07/` | Evidencias de cierre de observaciones del entrenamiento HU07 y de su experimento asociado. | `cierre_observaciones_entrenamiento_hu07/INFORME_CIERRE_OBSERVACIONES.md`; `cierre_observaciones_entrenamiento_hu07/diseno_estados.json`; `cierre_observaciones_entrenamiento_hu07/experimento/` | Alta |
| `database/` | Recursos versionados de modelado y definición de la base de datos. | `database/agro.mwb`; `database/schema.sql` | Alta |
| `docs/` | Documentación técnica del proyecto sobre arquitectura, instalación y criterios o variables documentadas. | `docs/ARQUITECTURA.md`; `docs/INSTALACION.md`; `docs/HU08_*.md` | Alta |
| `evidencias/` | Carpeta de evidencias organizadas por auditoría, configuración, dependencias y ejecución. | `evidencias/auditoria/`; `evidencias/configuracion/`; `evidencias/dependencias/`; `evidencias/ejecucion/` | Alta |
| `frontend/` | Aplicación de interfaz de usuario y su configuración de construcción. | `frontend/package.json`; `frontend/vite.config.js`; `frontend/src/`; `frontend/index.html` | Alta |
| `knowledge/` | Documentos de conocimiento y metadatos versionados usados por el proyecto. | `knowledge/*.md`; `knowledge/*.meta.json` | Media |
| `piloto_hu07_v2/` | Artefactos del piloto HU07 v2, incluyendo registros aceptados, rechazados, fuentes y manifiesto. | `piloto_hu07_v2/aceptadas_v2.jsonl`; `piloto_hu07_v2/rechazadas_v2.jsonl`; `piloto_hu07_v2/fuentes_v2.json`; `piloto_hu07_v2/manifiesto_v2.json` | Alta |
| `.gitignore` | Define reglas de exclusión de Git. | `.gitignore` | Alta |
| `README.md` | Documento principal de presentación o indicaciones del proyecto. | `README.md` | Media |
| `insertar_datos.py` | Script cuyo nombre indica inserción de datos; el propósito específico no puede determinarse sin revisar su contenido. | `insertar_datos.py` | Media |
| `package-lock.json` | Archivo de bloqueo de dependencias asociado a npm. | `package-lock.json` | Alta |
| `render.yaml` | Archivo de configuración cuyo nombre indica despliegue o configuración de Render; sus detalles no fueron revisados. | `render.yaml` | Media |

## Conteo por extensión

Se contabilizan los **364 archivos versionados** devueltos por `git ls-files`.

| Extensión o tipo | Cantidad |
|---|---:|
| `.py` | 199 |
| `.md` | 54 |
| `.json` | 43 |
| `.jsx` | 17 |
| `.jsonl` | 16 |
| `.js` | 10 |
| `.txt` | 9 |
| `.joblib` | 3 |
| `.example` | 2 |
| `.gitkeep` | 2 |
| `<sin extensión>` | 1 |
| `.yaml` | 1 |
| `.css` | 1 |
| `.html` | 1 |
| `.ipynb` | 1 |
| `.gitignore` | 1 |
| `.ini` | 1 |
| `.sql` | 1 |
| `.mwb` | 1 |

## Carpetas cuyo propósito no pueda determinarse

Ninguna carpeta de primer nivel quedó sin propósito mínimo, pero algunas requieren revisión de contenido para precisar su función:

| Carpeta | Pregunta pendiente |
|---|---|
| `knowledge/` | ¿Qué formato y función operativa tienen exactamente los documentos de conocimiento y sus metadatos? |
| `evidencias/` | ¿Las evidencias están clasificadas solo por etapa o siguen algún esquema adicional? |

## Detalle de archivos versionados

# Inventario de archivos versionados

## Carpetas principales de la raíz

- `auditoria_etiquetas_dataset_trabajo/`: registra la auditoría del etiquetado de datos de trabajo y reúne los casos dudosos identificados.
- `auditoria_hu07_v2/`: contiene la auditoría del piloto HU07 y el cierre de la revisión humana, separando preparación independiente, casos revisados y estado final.
- `backend/`: alberga la API, el dominio y las adaptadores de infraestructura del asistente agrícola, además de pruebas, evaluación y experimentos de clasificación.
- `cierre_observaciones_entrenamiento_hu07/`: documenta el cierre de observaciones de entrenamiento HU07 y conserva el diseño de estados y el experimento asociado.
- `database/`: contiene el modelo de datos de MySQL Workbench y el esquema SQL de la base de datos.
- `docs/`: reúne documentación técnica de arquitectura, instalación y variables o categorías relacionadas con el proyecto.
- `evidencias/`: centraliza las evidencias de auditoría, configuración, dependencias y ejecución del proyecto.
- `frontend/`: contiene la aplicación web del asistente construida con Vite y React/JavaScript.
- `knowledge/`: almacena los documentos de conocimiento agrícola y sus metadatos utilizados por el sistema RAG.
- `piloto_hu07_v2/`: conserva los datos del piloto v2 de HU07, incluidos registros aceptados, rechazados, fuentes y manifiesto.

## Archivos versionados

.gitignore
README.md
auditoria_etiquetas_dataset_trabajo/INFORME_AUDITORIA_ETIQUETAS.md
auditoria_etiquetas_dataset_trabajo/lista_casos_dudosos.jsonl
auditoria_hu07_v2/INFORME_AUDITORIA_PILOTO_HU07.md
auditoria_hu07_v2/cierre_revision_humana/01_tres_casos_dudosos.md
auditoria_hu07_v2/cierre_revision_humana/02_segunda_revision_57.md
auditoria_hu07_v2/cierre_revision_humana/03_acuerdos_desacuerdos_pendientes.md
auditoria_hu07_v2/cierre_revision_humana/04_cambios_propuestos.md
auditoria_hu07_v2/cierre_revision_humana/05_estado_final_piloto.md
auditoria_hu07_v2/revision_independiente/INFORME_PREPARACION.md
auditoria_hu07_v2/revision_independiente/INSTRUCCIONES_REVISOR.md
auditoria_hu07_v2/revision_independiente/casos_3.jsonl
auditoria_hu07_v2/revision_independiente/consultas_57.jsonl
auditoria_hu07_v2/revision_independiente/plantilla_registro.jsonl
auditoria_hu07_v2/revision_independiente/plantilla_registro.md
backend/.env.example
backend/app/__init__.py
backend/app/application/__init__.py
backend/app/application/services/__init__.py
backend/app/application/services/document_chunker.py
backend/app/application/services/fragmentador_documentos.py
backend/app/application/services/rag_retrieval_service.py
backend/app/application/services/referencia_origen.py
backend/app/application/services/servicio_recuperacion_rag.py
backend/app/application/services/suficiencia_contexto.py
backend/app/application/useCases/__init__.py
backend/app/application/useCases/clasificar_consulta.py
backend/app/application/useCases/crear_contexto_agricola.py
backend/app/application/useCases/create_agricultural_context.py
backend/app/application/useCases/incorporar_conocimiento.py
backend/app/application/useCases/index_knowledge.py
backend/app/application/useCases/indexar_conocimiento.py
backend/app/application/useCases/ingest_knowledge.py
backend/app/application/useCases/iniciar_sesion_agricultor.py
backend/app/application/useCases/list_agricultural_contexts.py
backend/app/application/useCases/list_knowledge_documents.py
backend/app/application/useCases/listar_contextos_agricolas.py
backend/app/application/useCases/listar_documentos_conocimiento.py
backend/app/application/useCases/login_farmer.py
backend/app/application/useCases/obtener_observaciones_meteorologicas.py
backend/app/application/useCases/predecir_riesgo.py
backend/app/application/useCases/register_farmer.py
backend/app/application/useCases/registrar_agricultor.py
backend/app/application/useCases/registrar_consulta.py
backend/app/application/useCases/seleccionar_contexto_agricola.py
backend/app/application/useCases/select_agricultural_context.py
backend/app/application/useCases/submit_query.py
backend/app/domain/__init__.py
backend/app/domain/entities/__init__.py
backend/app/domain/entities/agricultor.py
backend/app/domain/entities/agricultural_context.py
backend/app/domain/entities/consulta.py
backend/app/domain/entities/contexto_agricola.py
backend/app/domain/entities/documento_conocimiento.py
backend/app/domain/entities/evidence.py
backend/app/domain/entities/evidencia.py
backend/app/domain/entities/farmer.py
backend/app/domain/entities/knowledge_document.py
backend/app/domain/entities/observacion_meteorologica.py
backend/app/domain/entities/query.py
backend/app/domain/entities/response.py
backend/app/domain/entities/respuesta.py
backend/app/domain/exceptions.py
backend/app/domain/ports/__init__.py
backend/app/domain/ports/input/__init__.py
backend/app/domain/ports/input/clasificar_consulta_port.py
backend/app/domain/ports/input/gestionar_contexto_port.py
backend/app/domain/ports/input/incorporar_conocimiento_port.py
backend/app/domain/ports/input/index_knowledge_port.py
backend/app/domain/ports/input/indexar_conocimiento_port.py
backend/app/domain/ports/input/ingest_knowledge_port.py
backend/app/domain/ports/input/iniciar_sesion_agricultor_port.py
backend/app/domain/ports/input/login_farmer_port.py
backend/app/domain/ports/input/manage_context_port.py
backend/app/domain/ports/input/obtener_observaciones_meteorologicas_port.py
backend/app/domain/ports/input/predecir_riesgo_port.py
backend/app/domain/ports/input/register_farmer_port.py
backend/app/domain/ports/input/registrar_agricultor_port.py
backend/app/domain/ports/input/registrar_consulta_port.py
backend/app/domain/ports/input/submit_query_port.py
backend/app/domain/ports/output/__init__.py
backend/app/domain/ports/output/agricultural_context_repository_port.py
backend/app/domain/ports/output/embedding_port.py
backend/app/domain/ports/output/evidence_repository_port.py
backend/app/domain/ports/output/farmer_repository_port.py
backend/app/domain/ports/output/hasher_contrasena_port.py
backend/app/domain/ports/output/knowledge_document_repository_port.py
backend/app/domain/ports/output/password_hasher_port.py
backend/app/domain/ports/output/puerto_clasificador_consultas.py
backend/app/domain/ports/output/puerto_observaciones_meteorologicas.py
backend/app/domain/ports/output/puerto_predictor_riesgo.py
backend/app/domain/ports/output/query_repository_port.py
backend/app/domain/ports/output/repositorio_agricultor_port.py
backend/app/domain/ports/output/repositorio_consulta_port.py
backend/app/domain/ports/output/repositorio_contexto_agricola_port.py
backend/app/domain/ports/output/repositorio_documento_conocimiento_port.py
backend/app/domain/ports/output/repositorio_evidencia_port.py
backend/app/domain/ports/output/text_generation_port.py
backend/app/domain/ports/output/token_issuer_port.py
backend/app/domain/ports/output/token_verifier_port.py
backend/app/domain/ports/output/vector_store_port.py
backend/app/domain/valueObjects/__init__.py
backend/app/domain/valueObjects/content_hash.py
backend/app/domain/valueObjects/crop.py
backend/app/domain/valueObjects/cultivo.py
backend/app/domain/valueObjects/email.py
backend/app/domain/valueObjects/hash_contenido.py
backend/app/domain/valueObjects/hash_contrasena.py
backend/app/domain/valueObjects/password_hash.py
backend/app/domain/valueObjects/query_text.py
backend/app/domain/valueObjects/region.py
backend/app/domain/valueObjects/texto_consulta.py
backend/app/infrastructure/__init__.py
backend/app/infrastructure/adapters/__init__.py
backend/app/infrastructure/adapters/input/__init__.py
backend/app/infrastructure/adapters/input/http/__init__.py
backend/app/infrastructure/adapters/input/http/auth_controller.py
backend/app/infrastructure/adapters/input/http/clasificacion_controller.py
backend/app/infrastructure/adapters/input/http/context_controller.py
backend/app/infrastructure/adapters/input/http/dependencia_autenticacion.py
backend/app/infrastructure/adapters/input/http/health_controller.py
backend/app/infrastructure/adapters/input/http/knowledge_controller.py
backend/app/infrastructure/adapters/input/http/query_controller.py
backend/app/infrastructure/adapters/input/http/riesgo_controller.py
backend/app/infrastructure/adapters/input/http/weather_controller.py
backend/app/infrastructure/adapters/output/__init__.py
backend/app/infrastructure/adapters/output/chroma/__init__.py
backend/app/infrastructure/adapters/output/chroma/chroma_vector_store_adapter.py
backend/app/infrastructure/adapters/output/clasificacion/__init__.py
backend/app/infrastructure/adapters/output/clasificacion/adaptador_clasificador_tfidf.py
backend/app/infrastructure/adapters/output/embedding/__init__.py
backend/app/infrastructure/adapters/output/embedding/external_embedding_adapter.py
backend/app/infrastructure/adapters/output/embedding/local_lexical_embedding_adapter.py
backend/app/infrastructure/adapters/output/generation/__init__.py
backend/app/infrastructure/adapters/output/generation/adaptador_generacion_ollama.py
backend/app/infrastructure/adapters/output/generation/adaptador_generacion_plantilla.py
backend/app/infrastructure/adapters/output/generation/template_generation_adapter.py
backend/app/infrastructure/adapters/output/mysql/__init__.py
backend/app/infrastructure/adapters/output/mysql/agricultural_context_repository.py
backend/app/infrastructure/adapters/output/mysql/connection.py
backend/app/infrastructure/adapters/output/mysql/evidence_repository.py
backend/app/infrastructure/adapters/output/mysql/farmer_repository.py
backend/app/infrastructure/adapters/output/mysql/knowledge_document_repository.py
backend/app/infrastructure/adapters/output/mysql/query_repository.py
backend/app/infrastructure/adapters/output/mysql/repositorio_agricultor.py
backend/app/infrastructure/adapters/output/mysql/repositorio_consulta.py
backend/app/infrastructure/adapters/output/mysql/repositorio_contexto_agricola.py
backend/app/infrastructure/adapters/output/mysql/repositorio_documento_conocimiento.py
backend/app/infrastructure/adapters/output/mysql/repositorio_evidencia.py
backend/app/infrastructure/adapters/output/riesgo/__init__.py
backend/app/infrastructure/adapters/output/riesgo/adaptador_predictor_riesgo.py
backend/app/infrastructure/adapters/output/security/__init__.py
backend/app/infrastructure/adapters/output/security/bcrypt_password_hasher.py
backend/app/infrastructure/adapters/output/security/emisor_token_jwt.py
backend/app/infrastructure/adapters/output/security/hasher_contrasena_bcrypt.py
backend/app/infrastructure/adapters/output/security/jwt_token_issuer.py
backend/app/infrastructure/adapters/output/security/jwt_token_verifier.py
backend/app/infrastructure/adapters/output/security/verificador_token_jwt.py
backend/app/infrastructure/adapters/output/senamhi/__init__.py
backend/app/infrastructure/adapters/output/senamhi/adaptador_senamhi_wis2.py
backend/app/infrastructure/composition.py
backend/app/infrastructure/config/__init__.py
backend/app/infrastructure/config/cors.py
backend/app/infrastructure/config/settings.py
backend/app/main.py
backend/clasificacion/README.md
backend/clasificacion/REGLAS_ETIQUETADO.md
backend/clasificacion/esquema/esquema_dataset_v1.json
backend/clasificacion/experimentos/hu07_preliminar/dataset_hu07_preliminar_revision.jsonl
backend/clasificacion/experimentos/hu07_preliminar/manifiesto_dataset_hu07_preliminar.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/consultas_inferencia.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/entrenar_clasificador.py
backend/clasificacion/experimentos/hu07_tfidf_preliminar/ids_particiones.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/inferir_clasificador.py
backend/clasificacion/experimentos/hu07_tfidf_preliminar/informe_inferencia.md
backend/clasificacion/experimentos/hu07_tfidf_preliminar/informe_tecnico.md
backend/clasificacion/experimentos/hu07_tfidf_preliminar/manifiesto_experimento.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/matriz_confusion.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/metricas.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/modelo_tfidf_logreg.joblib
backend/clasificacion/experimentos/hu07_tfidf_preliminar/resultados_inferencia.json
backend/clasificacion/experimentos/hu07_tfidf_preliminar/versiones.json
backend/clasificacion/experimentos/hu07_tfidf_v2/INTEGRACION_BACKEND.md
backend/clasificacion/experimentos/hu07_tfidf_v2/entrenar_v2.py
backend/clasificacion/experimentos/hu07_tfidf_v2/ids_particiones.json
backend/clasificacion/experimentos/hu07_tfidf_v2/informe_auditoria_datos.md
backend/clasificacion/experimentos/hu07_tfidf_v2/informe_pruebas_ambiguas_fuera_alcance.md
backend/clasificacion/experimentos/hu07_tfidf_v2/informe_tecnico.md
backend/clasificacion/experimentos/hu07_tfidf_v2/informe_validacion_final_hu07.md
backend/clasificacion/experimentos/hu07_tfidf_v2/manifiesto_experimento.json
backend/clasificacion/experimentos/hu07_tfidf_v2/matriz_confusion.json
backend/clasificacion/experimentos/hu07_tfidf_v2/metricas.json
backend/clasificacion/experimentos/hu07_tfidf_v2/modelo_tfidf_logreg_v2.joblib
backend/clasificacion/experimentos/hu07_tfidf_v2/rejilla_validacion.json
backend/clasificacion/experimentos/hu07_tfidf_v2/sonda_no_usada_para_ajustar.json
backend/clasificacion/experimentos/hu07_tfidf_v2/umbral_abstencion.json
backend/clasificacion/experimentos/hu07_tfidf_v2/versiones.json
backend/clasificacion/experimentos/hu08_riesgo/INTEGRACION_BACKEND.md
backend/clasificacion/experimentos/hu08_riesgo/categorias_riesgo_hu08.md
backend/clasificacion/experimentos/hu08_riesgo/configuracion_seleccionada_hu08.json
backend/clasificacion/experimentos/hu08_riesgo/controles.json
backend/clasificacion/experimentos/hu08_riesgo/dataset_hu08_sintetico.jsonl
backend/clasificacion/experimentos/hu08_riesgo/entrenamiento.jsonl
backend/clasificacion/experimentos/hu08_riesgo/entrenar_modelo_riesgo_hu08.py
backend/clasificacion/experimentos/hu08_riesgo/esquema_registro_hu08.json
backend/clasificacion/experimentos/hu08_riesgo/evaluar_modelo_riesgo_hu08.py
backend/clasificacion/experimentos/hu08_riesgo/generar_dataset_hu08.py
backend/clasificacion/experimentos/hu08_riesgo/ids_particiones.json
backend/clasificacion/experimentos/hu08_riesgo/informe_controles_calidad.md
backend/clasificacion/experimentos/hu08_riesgo/informe_evaluacion_prueba_hu08.md
backend/clasificacion/experimentos/hu08_riesgo/informe_tecnico_hu08.md
backend/clasificacion/experimentos/hu08_riesgo/instrucciones_reproduccion_hu08.md
backend/clasificacion/experimentos/hu08_riesgo/matriz_confusion_prueba_hu08.json
backend/clasificacion/experimentos/hu08_riesgo/metricas_prueba_hu08.json
backend/clasificacion/experimentos/hu08_riesgo/metricas_validacion_cruzada_hu08.json
backend/clasificacion/experimentos/hu08_riesgo/modelo_riesgo_hu08.joblib
backend/clasificacion/experimentos/hu08_riesgo/preprocesamiento_riesgo_hu08.py
backend/clasificacion/experimentos/hu08_riesgo/prueba.jsonl
backend/clasificacion/experimentos/hu08_riesgo/reglas_etiquetado_sintetico.md
backend/clasificacion/experimentos/hu08_riesgo/resumen_distribucion.md
backend/clasificacion/muestras/muestra_ilustrativa_v1.json
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/clima_heladas.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/cola_ambigua.jsonl
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/cosecha_poscosecha.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/enfermedades_cultivos.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/fertilizacion_nutricion.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/fuera_de_alcance.jsonl
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/plagas.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/riego.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/siembra_manejo_cultivo.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/bancos/suelos.txt
backend/clasificacion/preparacion/dataset_trabajo_hu07/cola_ambigua.jsonl
backend/clasificacion/preparacion/dataset_trabajo_hu07/consultas_trabajo.jsonl
backend/clasificacion/preparacion/dataset_trabajo_hu07/controles.json
backend/clasificacion/preparacion/dataset_trabajo_hu07/esquema_registro_trabajo.json
backend/clasificacion/preparacion/dataset_trabajo_hu07/fuera_de_alcance.jsonl
backend/clasificacion/preparacion/dataset_trabajo_hu07/generar_dataset_trabajo.py
backend/clasificacion/preparacion/dataset_trabajo_hu07/guia_revision_humana.md
backend/clasificacion/preparacion/dataset_trabajo_hu07/informe_distribucion.md
backend/clasificacion/preparacion/dataset_trabajo_hu07/informe_duplicados_similitudes.md
backend/clasificacion/preparacion/dataset_trabajo_hu07/manifiesto_dataset_trabajo.json
backend/clasificacion/preparacion/dataset_trabajo_hu07/plan_evaluacion_clasificador.md
backend/clasificacion/preparacion/dataset_trabajo_hu07/tareas_pendientes_aprobacion.md
backend/taxonomia/taxonomia_consultas_v1.json
backend/evaluation/README.md
backend/evaluation/RESULTADOS_PENDIENTES.md
backend/evaluation/__init__.py
backend/evaluation/data/pmv1_baseline.json
backend/evaluation/dataset.py
backend/evaluation/pipeline.py
backend/evaluation/preflight.py
backend/evaluation/ragas_baseline.ipynb
backend/evaluation/ragas_compat.py
backend/evaluation/ragas_runner.py
backend/evaluation/results/README.md
backend/evaluation/run_baseline.py
backend/package-lock.json
backend/pytest.ini
backend/requirements.txt
backend/scripts/.gitkeep
backend/tests/conftest.py
backend/tests/test_adaptador_senamhi_wis2.py
backend/tests/test_agricultural_context.py
backend/tests/test_anexos_ambiguos_fuera_alcance.py
backend/tests/test_architecture.py
backend/tests/test_arranque.py
backend/tests/test_chroma_adapter.py
backend/tests/test_chunking.py
backend/tests/test_clasificacion_en_consulta.py
backend/tests/test_clasificador_consulta.py
backend/tests/test_context_endpoint.py
backend/tests/test_cors.py
backend/tests/test_embedding_port.py
backend/tests/test_evidence.py
backend/tests/test_generacion_ollama.py
backend/tests/test_health.py
backend/tests/test_index_knowledge.py
backend/tests/test_ingest_knowledge.py
backend/tests/test_knowledge_endpoint.py
backend/tests/test_login_endpoint.py
backend/tests/test_login_farmer.py
backend/tests/test_prediccion_riesgo.py
backend/tests/test_query_endpoint.py
backend/tests/test_rag_endpoint.py
backend/tests/test_rag_retrieval.py
backend/tests/test_ragas_baseline.py
backend/tests/test_referencia_origen.py
backend/tests/test_register_endpoint.py
backend/tests/test_register_farmer.py
backend/tests/test_senamhi_wis2_integration.py
backend/tests/test_settings.py
backend/tests/test_submit_query.py
backend/tests/test_suficiencia_contexto.py
backend/tests/test_weather_endpoint.py
cierre_observaciones_entrenamiento_hu07/INFORME_CIERRE_OBSERVACIONES.md
cierre_observaciones_entrenamiento_hu07/diseno_estados.json
cierre_observaciones_entrenamiento_hu07/experimento/consultas_aprobadas.jsonl
cierre_observaciones_entrenamiento_hu07/experimento/manifiesto_experimento.json
database/agro.mwb
database/schema.sql
docs/ARQUITECTURA.md
docs/HU08_CATEGORIAS_Y_CRITERIOS_RIESGO.md
docs/HU08_REVISION_DATOS_RIESGO_AGRICOLA.md
docs/HU08_VARIABLES_RIESGO_AGRICOLA.md
docs/INSTALACION.md
evidencias/auditoria/arquitectura_detectada.md
evidencias/auditoria/stack_tecnologico.md
evidencias/configuracion/instalacion.md
evidencias/dependencias/backend.md
evidencias/dependencias/frontend.md
frontend/.env.example
frontend/index.html
frontend/package-lock.json
frontend/package.json
frontend/public/_redirects
frontend/src/App.jsx
frontend/src/api/baseUrl.js
frontend/src/api/baseUrl.test.js
frontend/src/api/client.js
frontend/src/api/conexion.js
frontend/src/api/conexion.test.js
frontend/src/components/AppHeader.jsx
frontend/src/components/AuthFooter.jsx
frontend/src/components/AuthenticatedShell.jsx
frontend/src/components/BrandMark.jsx
frontend/src/components/ProtectedRoute.jsx
frontend/src/components/PublicHeader.jsx
frontend/src/components/PublicShell.jsx
frontend/src/consulta/presentacion.js
frontend/src/consulta/presentacion.test.js
frontend/src/main.jsx
frontend/src/pages/ContextPage.jsx
frontend/src/pages/DashboardPage.jsx
frontend/src/pages/HomePage.jsx
frontend/src/pages/KnowledgePage.jsx
frontend/src/pages/LoginPage.jsx
frontend/src/pages/QueryPage.jsx
frontend/src/pages/RegisterPage.jsx
frontend/src/pages/RiskPage.jsx
frontend/src/riesgo/presentacion.js
frontend/src/riesgo/presentacion.test.js
frontend/src/styles.css
frontend/vite.config.js
insertar_datos.py
knowledge/.gitkeep
knowledge/22165791-5e66-4bb5-bd53-e72e51afe67c.md
knowledge/22165791-5e66-4bb5-bd53-e72e51afe67c.meta.json
knowledge/6e15b823-a651-4536-bada-87c6a8bee31c.md
knowledge/6e15b823-a651-4536-bada-87c6a8bee31c.meta.json
knowledge/7019602d-f4ac-4153-8cdc-acd18a03fa3a.md
knowledge/7019602d-f4ac-4153-8cdc-acd18a03fa3a.meta.json
knowledge/99d5b3aa-1882-4fa4-b62f-750506fa5b1e.md
knowledge/99d5b3aa-1882-4fa4-b62f-750506fa5b1e.meta.json
knowledge/ad177d66-9bc3-4856-994c-2b16659a704b.md
knowledge/ad177d66-9bc3-4856-994c-2b16659a704b.meta.json
knowledge/prueba-heladas-sierra.md
knowledge/prueba-riego-papa.md
package-lock.json
piloto_hu07_v2/aceptadas_v2.jsonl
piloto_hu07_v2/fuentes_v2.json
piloto_hu07_v2/manifiesto_v2.json
piloto_hu07_v2/rechazadas_v2.jsonl
render.yaml
