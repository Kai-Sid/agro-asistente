# Evaluación de la calidad arquitectónica (Fase 6, Prompt 10)

## Alcance y método

- **Fuentes:** `evidencias/analisis/arquitectura_real.md`, `dominio.md`, `modulos.md`, `hallazgos.md`, el código de `backend/app` y `frontend/src`, y la corrida de `backend/tests`.
- **Commit base del código:** `eaac3da`.
- **Escala:** 1 (muy deficiente) a 5 (excelente).
- **Regla:** cada calificación se apoya en evidencia citada. Los números `H-xx` remiten a `hallazgos.md`.
- **Corrida de pruebas (entorno de análisis, Linux, Python 3.12.3):** 225 pruebas recolectadas; 184 pasaron, 39 fallaron y 2 se omitieron. De los fallos, 27 fueron por conexión rechazada a MySQL y los otros 12 por archivos de datos o modelos que no estaban en el paquete analizado, o por `ragas` no instalado en ese entorno. No es una corrida del entorno oficial del proyecto.

## 1. Resumen

| Criterio | Calificación |
|---|---|
| Cohesión | 4 |
| Acoplamiento | 4 |
| Escalabilidad | 2 |
| Mantenibilidad | 3 |
| Testabilidad | 4 |
| Seguridad | 2 |
| **Promedio** | **3.2** |

## 2. Cohesión: 4/5

**A favor**
- Cada caso de uso es una clase con una sola operación (`ejecutar`) y un puerto de entrada propio.
- Las entidades validan sus propios datos en fábricas (`registrar`, `crear`); los objetos de valor encapsulan reglas simples (correo, cultivo, región, texto de consulta, hash).
- Los módulos funcionales (autenticación, contextos, consulta, conocimiento, clasificación, riesgo, clima) tienen su propio controlador, caso de uso y adaptadores.

**En contra**
- `RegistrarConsulta` coordina cinco colaboradores y 11 pasos; es el punto más denso, aunque cada paso delega.
- `RepositorioDocumentoConocimientoMysql` mezcla base de datos y sistema de archivos (H-05).
- 26 % del código son módulos duplicados sin uso (H-07).

## 3. Acoplamiento: 4/5

**A favor**
- El análisis de imports no encontró ninguna violación de capa. `domain` y `application` importan solo la biblioteca estándar.
- `test_architecture.py` hace cumplir estas reglas, y `bcrypt`, `jwt`, `sqlalchemy` y `httpx` quedan dentro de sus adaptadores.
- Todo el cableado vive en `composition.py`, y el proveedor de embeddings y el de generación se eligen por configuración.

**En contra**
- Los controladores reciben el contenedor completo en vez de los puertos que necesitan (localizador de servicios).
- El arranque resuelve rutas en `backend/clasificacion/experimentos`, y el adaptador de riesgo modifica `sys.path` (H-15).
- Los modelos `.joblib` dependen de la versión de scikit-learn instalada (H-14).

## 4. Escalabilidad: 2/5

**A favor**
- La autenticación es sin estado (JWT), lo que permite varias instancias del backend.
- El motor de base de datos usa `pool_pre_ping`, y los modelos se cargan una sola vez con un candado.

**En contra**
- Chroma guarda sus vectores en una carpeta local del proceso, y el conocimiento en archivos locales: no se pueden compartir entre instancias (H-05).
- El modelo de lenguaje es un único servidor Ollama; el timeout de generación es de 90 s y las rutas de la API son síncronas.
- `/health` crea un motor de base de datos nuevo en cada llamada (H-22).
- El despliegue propuesto usa el plan gratuito de Render, sin MySQL, disco ni Ollama (H-17).
- No se midió rendimiento ni carga: No evidenciado.

## 5. Mantenibilidad: 3/5

**A favor**
- Estructura de carpetas clara y consistente con la documentación de capas.
- 33 archivos de prueba y un `README.md` y `ARQUITECTURA.md` que explican las historias HU-01 a HU-06.
- Los comentarios del código documentan limitaciones (embeddings léxicos, filtro de suficiencia).

**En contra**
- 42 módulos duplicados en inglés sin uso (H-07).
- Idiomas mezclados en rutas, esquemas y puertos (H-21).
- La documentación no cubre clasificación, riesgo ni clima (H-16).
- Dependencias con rangos abiertos y sin archivo de bloqueo (H-14).
- No hay registro de eventos de la aplicación (H-13).

## 6. Testabilidad: 4/5

**A favor**
- Los puertos permiten sustituir adaptadores: el generador de plantilla reemplaza a Ollama en las pruebas (`conftest.py`).
- 217 funciones de prueba en 33 archivos, con 17 pruebas solo para `submit_query` y 16 para el adaptador de Ollama.
- Existen pruebas de arquitectura que vigilan las reglas de capas.

**En contra**
- Las pruebas HTTP usan el contenedor real y una base MySQL real (H-04).
- Los fallos de la corrida de análisis por falta de archivos de datos indican pruebas que dependen de datasets de la carpeta de experimentos.
- El `package.json` del frontend no define un script `test`. Las 18 pruebas de tres archivos corrieron a mano con `node --test` y pasaron (H-26).

## 7. Seguridad: 2/5

**A favor**
- Contraseñas con bcrypt y longitud mínima de 8 caracteres.
- Tokens JWT con vencimiento y algoritmo fijado al verificar.
- Mensaje único «Credenciales inválidas» que no revela si el correo existe.
- CORS con orígenes explícitos y rechazo del comodín `*` con credenciales.
- Secretos por variables de entorno, y `.env` ignorado por Git.

**En contra**
- Credenciales reales de TiDB Cloud en un script que se subió a GitHub (H-01).
- Secreto JWT por defecto sin ninguna protección (H-02).
- Endpoints de ingesta e indexación sin control de roles (H-10).
- Token en `localStorage` (H-11) y endpoint de clima público (H-12).
- Sin limitación de intentos de login ni registro de eventos (H-13).
- 6 vulnerabilidades conocidas en dependencias del frontend (H-06).

## 8. Recomendaciones de mejora

| Prioridad | Acción | Criterio que mejora | Hallazgos |
|---|---|---|---|
| P1 | Rotar la contraseña de TiDB y sacar las credenciales del código | Seguridad | H-01 |
| P1 | Rechazar el arranque con el secreto JWT por defecto en producción | Seguridad | H-02 |
| P1 | Manejar los errores de base de datos con 503 y registrarlos | Seguridad, mantenibilidad | H-03 |
| P2 | Aislar las pruebas HTTP con repositorios en memoria o una base de pruebas | Testabilidad | H-04 |
| P2 | Guardar documentos y vectores en almacenamiento persistente compartido | Escalabilidad | H-05 |
| P2 | Eliminar los 42 módulos duplicados y unificar el idioma | Mantenibilidad, cohesión | H-07, H-21 |
| P2 | Agregar roles, registro de eventos y límite de intentos | Seguridad | H-10, H-13 |
| P2 | Actualizar `react-router-dom` y `vite` en una rama de prueba | Seguridad | H-06 |
| P3 | Hacer transaccional el guardado de la consulta | Cohesión | H-08 |
| P3 | Fijar versiones y separar dependencias de producción, desarrollo y evaluación | Mantenibilidad | H-14 |
| P3 | Mover los modelos y su preprocesamiento a un paquete del producto | Acoplamiento | H-15 |
| P3 | Documentar HU-07, HU-08 y el adaptador de clima | Mantenibilidad | H-16 |
| P3 | Definir despliegue completo (base, disco, Ollama) y CI | Escalabilidad | H-17 |
| P3 | Agregar el script `test` al frontend | Testabilidad | H-26 |
| P3 | Inyectar puertos concretos en los controladores en vez del contenedor completo | Acoplamiento | — |

## 9. No evidenciado

- Rendimiento y comportamiento bajo carga.
- Cobertura de pruebas medida (no se ejecutó una herramienta de cobertura).
- Resultado de la suite en el entorno oficial del equipo.
