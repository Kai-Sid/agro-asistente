# Preparación y alcance técnico del PMV3

Esta rama implementa la ampliación PMV3 sobre la arquitectura hexagonal existente. La aplicación local todavía necesita actualizar el código y ejecutar la migración PMV3 en MySQL antes de usar las pantallas administrativas.

## Alcance implementado

- **HU-13 — Administración de conocimiento:** listado, alta, edición/versionado y activación/desactivación lógica de documentos. La edición vuelve a indexar el documento; la desactivación retira sus fragmentos del índice sin borrar el registro.
- **HU-14 — Roles y autorización:** login administrativo independiente, rol firmado en JWT y dependencias de autorización en API. Un agricultor no obtiene acceso a endpoints administrativos; el frontend separa rutas de agricultor y administración.
- **HU-15 — Indicadores:** cada POST a `/api/v1/queries` registra código HTTP y duración mediante procedimiento almacenado. El panel resume solicitudes, consultas atendidas, errores y tiempos para un periodo.
- **HU-16 — Evaluación de IA:** dataset PMV3 versionado, pipeline con Ollama + Chroma, mediciones RAGAS y proxies léxicos etiquetados como tales. Las ejecuciones guardan resultados por muestra y resumen en JSON y MySQL.
- **HU-17 — Usabilidad:** estilos adaptables a móvil, mensajes de error y rutas diferenciadas. Falta completar una prueba con participantes reales y adjuntar evidencia; no se inventaron resultados.

## Preparación local en Laragon

Desde la raíz del repositorio, en PowerShell:

```powershell
$mysql = "C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe"
& $mysql -u root -e "source database/schema.sql"
& $mysql -u root -D agro_asistente -e "source database/pmv3_schema.sql"
& $mysql -u root -D agro_asistente -e "source database/procedures.sql"
```

Si root tiene contraseña, añade `-p` después de `-u root` en cada comando.

Orden requerido: esquema base, tablas PMV3, procedimientos almacenados actualizados. No ejecutes solo `procedures.sql` porque sus rutinas nuevas dependen de las tablas PMV3.

Verifica las rutinas con:

```powershell
& $mysql -u root -D agro_asistente -e "SHOW PROCEDURE STATUS WHERE Db = 'agro_asistente';"
```

## Crear el primer administrador

Desde `backend/`, con el entorno virtual y dependencias instaladas:

```powershell
python -m scripts.crear_administrador
```

El script solicita nombre, correo y contraseña de al menos 12 caracteres, aplica bcrypt y guarda el administrador con `sp_administrador_crear`. No se incluye una cuenta ni contraseña por defecto.

## Rutas de la interfaz

- Ingreso agricultor: `/login`
- Ingreso administrador: `/admin/login`
- Panel: `/admin`
- Gestión documental: `/admin/documents`
- Indicadores: `/admin/metrics`
- Evaluaciones: `/admin/evaluations`

Las pantallas privadas requieren un token válido. La API es la autoridad para la autorización; las rutas del navegador no la sustituyen.

## Evaluación reproducible

Desde `backend/`, con Ollama en ejecución, el modelo configurado disponible y Chroma con conocimiento indexado:

```powershell
python -m evaluation.run_baseline
```

La ejecución genera archivos versionados en `backend/evaluation/results/` y registra la ejecución con los procedimientos de evaluación. Si Ollama no está disponible o Chroma está vacío, la evaluación se detiene; no se reemplaza por respuestas de plantilla.

`retrieval_precision_lexical_proxy` y `answer_pertinence_lexical_coverage` son proxies léxicos y no equivalen a evaluación agronómica. `faithfulness` y `context_recall` se reportan solo si la ejecución RAGAS devuelve esos valores.

## Estado pendiente para cierre

1. Actualizar la rama local y ejecutar el SQL en Laragon.
2. Levantar API y frontend; verificar login de ambos roles, operaciones CRUD y que los endpoints respondan 401/403 cuando corresponda.
3. Registrar una ejecución RAGAS real con el modelo y la colección local del equipo.
4. Realizar prueba de usabilidad con agricultores/usuarios representativos, registrar tareas, errores, tiempo y observaciones en `PMV3_USABILIDAD.md`.
5. Revisar las métricas y conclusiones con asesoría agronómica antes de afirmar desempeño técnico en campo.
