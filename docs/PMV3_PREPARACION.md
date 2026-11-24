# Preparación técnica del PMV3

Esta rama prepara el acceso a MySQL para que las operaciones del backend usen procedimientos almacenados. No implementa todavía las historias HU-13 a HU-17.

## Persistencia MySQL

- Ejecutar `database/schema.sql` y después `database/procedures.sql` en la base de desarrollo.
- Los adaptadores activos llaman los procedimientos mediante `MysqlStoredProcedureGateway` y el método DBAPI `callproc`; el backend no construye consultas CRUD.
- La comprobación de conexión usa el ping del controlador de MySQL.
- No editar los procedimientos como consultas dentro de los repositorios Python. Si cambia el contrato de un procedimiento, actualizar primero el script SQL y luego el adaptador que lo llama.

## Historias que aún bloquean el PMV3

1. **HU-14 — roles y autorización**
   - Agregar el rol de administrador al modelo de identidad.
   - Incluir el rol en la identidad autenticada y verificarlo en las operaciones administrativas del backend.
   - Restringir también las pantallas; ocultar un enlace en React no sustituye la autorización del API.

2. **HU-13 — administración de documentos**
   - Persistir metadatos y estado del documento en la base, en vez de depender solo de archivos laterales.
   - Definir formatos permitidos y validación de tamaño/tipo.
   - Añadir procedimientos para actualizar, deshabilitar y listar documentos activos.
   - Al deshabilitar, retirar el contenido del índice de recuperación sin borrar el historial del documento.

3. **HU-15 — indicadores**
   - Definir eventos que se van a medir y guardar duración, estado de respuesta y fecha de consulta.
   - Crear procedimientos de agregación por periodo y una ruta protegida para el panel administrativo.
   - Comparar valores del panel con registros de origen.

4. **HU-16 — evaluación de IA**
   - Preparar un conjunto de evaluación validado y versionado para clasificación, riesgo y RAG.
   - Ejecutar la evaluación real con Ollama y Chroma disponibles; conservar muestras, resultados, versión del modelo y tiempos.
   - Tratar las métricas de conjuntos sintéticos o preliminares como experimentales, no como desempeño validado en campo.

5. **HU-17 — usabilidad**
   - Probar los flujos principales con participantes representativos si están disponibles.
   - Registrar problemas de móvil, claridad, errores y tareas completadas; vincular la evidencia a las correcciones.

## Orden recomendado para iniciar el desarrollo

1. Instalar los procedimientos en la base de desarrollo y comprobar que el API existente funciona con el nuevo contrato.
2. Cerrar HU-14 y desplegar la autorización por rol en backend.
3. Completar HU-13 sobre los procedimientos y el almacenamiento de documentos.
4. Diseñar la instrumentación de HU-15 junto con el formato de resultados de HU-16.
5. Ejecutar HU-16 y luego cerrar HU-17 contra el flujo integrado.

No declarar una historia terminada hasta adjuntar evidencia y actualizar su tarjeta de Trello.
