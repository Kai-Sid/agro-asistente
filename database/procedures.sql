-- Agro Asistente: procedimientos para operaciones MySQL del backend.
-- Ejecutar después de database/schema.sql. El backend debe usar CALL mediante callproc;
-- no mantener SELECT/INSERT/UPDATE del dominio dentro de adaptadores Python.
USE agro_asistente;
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_agricultor_existe_por_correo$$
CREATE PROCEDURE sp_agricultor_existe_por_correo(IN p_correo VARCHAR(150))
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM agricultores WHERE correo = p_correo
  ) AS existe;
END$$

DROP PROCEDURE IF EXISTS sp_agricultor_buscar_por_correo$$
CREATE PROCEDURE sp_agricultor_buscar_por_correo(IN p_correo VARCHAR(150))
BEGIN
  SELECT id, nombre_completo, correo, contrasena_hash, fecha_creacion
  FROM agricultores
  WHERE correo = p_correo
  LIMIT 1;
END$$

DROP PROCEDURE IF EXISTS sp_agricultor_guardar$$
CREATE PROCEDURE sp_agricultor_guardar(
  IN p_nombre_completo VARCHAR(150),
  IN p_correo VARCHAR(150),
  IN p_contrasena_hash VARCHAR(255),
  IN p_fecha_creacion DATETIME
)
BEGIN
  INSERT INTO agricultores (nombre_completo, correo, contrasena_hash, fecha_creacion)
  VALUES (p_nombre_completo, p_correo, p_contrasena_hash, p_fecha_creacion);
  SELECT id, nombre_completo, correo, contrasena_hash, fecha_creacion
  FROM agricultores WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_contexto_agricola_guardar$$
CREATE PROCEDURE sp_contexto_agricola_guardar(
  IN p_agricultor_id INT,
  IN p_nombre_parcela VARCHAR(150),
  IN p_cultivo VARCHAR(100),
  IN p_region VARCHAR(100),
  IN p_observaciones TEXT,
  IN p_esta_seleccionado TINYINT,
  IN p_fecha_creacion DATETIME
)
BEGIN
  INSERT INTO contextos_agricolas
    (agricultor_id, nombre_parcela, cultivo, region, observaciones, esta_seleccionado, fecha_creacion)
  VALUES
    (p_agricultor_id, p_nombre_parcela, p_cultivo, p_region, p_observaciones, p_esta_seleccionado, p_fecha_creacion);
  SELECT id, agricultor_id, nombre_parcela, cultivo, region, observaciones, esta_seleccionado, fecha_creacion
  FROM contextos_agricolas WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_contextos_agricolas_listar_por_agricultor$$
CREATE PROCEDURE sp_contextos_agricolas_listar_por_agricultor(IN p_agricultor_id INT)
BEGIN
  SELECT id, agricultor_id, nombre_parcela, cultivo, region, observaciones, esta_seleccionado, fecha_creacion
  FROM contextos_agricolas
  WHERE agricultor_id = p_agricultor_id
  ORDER BY fecha_creacion DESC, id DESC;
END$$

DROP PROCEDURE IF EXISTS sp_contexto_agricola_buscar_por_id_para_agricultor$$
CREATE PROCEDURE sp_contexto_agricola_buscar_por_id_para_agricultor(
  IN p_contexto_id INT,
  IN p_agricultor_id INT
)
BEGIN
  SELECT id, agricultor_id, nombre_parcela, cultivo, region, observaciones, esta_seleccionado, fecha_creacion
  FROM contextos_agricolas
  WHERE id = p_contexto_id AND agricultor_id = p_agricultor_id
  LIMIT 1;
END$$

DROP PROCEDURE IF EXISTS sp_contexto_agricola_seleccionar_para_agricultor$$
CREATE PROCEDURE sp_contexto_agricola_seleccionar_para_agricultor(
  IN p_contexto_id INT,
  IN p_agricultor_id INT
)
BEGIN
  IF EXISTS (
    SELECT 1
    FROM contextos_agricolas
    WHERE id = p_contexto_id AND agricultor_id = p_agricultor_id
  ) THEN
    UPDATE contextos_agricolas
    SET esta_seleccionado = CASE WHEN id = p_contexto_id THEN 1 ELSE 0 END
    WHERE agricultor_id = p_agricultor_id;
  END IF;
  SELECT id, agricultor_id, nombre_parcela, cultivo, region, observaciones, esta_seleccionado, fecha_creacion
  FROM contextos_agricolas
  WHERE id = p_contexto_id AND agricultor_id = p_agricultor_id
  LIMIT 1;
END$$

DROP PROCEDURE IF EXISTS sp_contexto_agricola_buscar_seleccionado$$
CREATE PROCEDURE sp_contexto_agricola_buscar_seleccionado(IN p_agricultor_id INT)
BEGIN
  SELECT id, agricultor_id, nombre_parcela, cultivo, region, observaciones, esta_seleccionado, fecha_creacion
  FROM contextos_agricolas
  WHERE agricultor_id = p_agricultor_id AND esta_seleccionado = 1
  ORDER BY id DESC
  LIMIT 1;
END$$

DROP PROCEDURE IF EXISTS sp_consulta_guardar$$
CREATE PROCEDURE sp_consulta_guardar(
  IN p_agricultor_id INT,
  IN p_contexto_id INT,
  IN p_pregunta TEXT,
  IN p_fecha_creacion DATETIME
)
BEGIN
  INSERT INTO consultas (agricultor_id, contexto_id, pregunta, fecha_creacion)
  VALUES (p_agricultor_id, p_contexto_id, p_pregunta, p_fecha_creacion);
  SELECT id, agricultor_id, contexto_id, pregunta, fecha_creacion
  FROM consultas WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_respuesta_guardar$$
CREATE PROCEDURE sp_respuesta_guardar(
  IN p_consulta_id INT,
  IN p_respuesta TEXT,
  IN p_metodo_generacion VARCHAR(50),
  IN p_fecha_creacion DATETIME
)
BEGIN
  INSERT INTO respuestas (consulta_id, respuesta, metodo_generacion, fecha_creacion)
  VALUES (p_consulta_id, p_respuesta, p_metodo_generacion, p_fecha_creacion);
  SELECT id, consulta_id, respuesta, metodo_generacion, fecha_creacion
  FROM respuestas WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_evidencia_guardar$$
CREATE PROCEDURE sp_evidencia_guardar(
  IN p_consulta_id INT,
  IN p_respuesta_id INT,
  IN p_documento_id INT,
  IN p_titulo_documento VARCHAR(200),
  IN p_texto_fragmento TEXT,
  IN p_puntuacion_similitud DECIMAL(10,6)
)
BEGIN
  INSERT INTO evidencias
    (consulta_id, respuesta_id, documento_id, titulo_documento, texto_fragmento, puntuacion_similitud)
  VALUES
    (p_consulta_id, p_respuesta_id, p_documento_id, p_titulo_documento, p_texto_fragmento, p_puntuacion_similitud);
END$$

DROP PROCEDURE IF EXISTS sp_evidencias_listar_por_consulta$$
CREATE PROCEDURE sp_evidencias_listar_por_consulta(IN p_consulta_id INT)
BEGIN
  SELECT id, consulta_id, respuesta_id, documento_id, titulo_documento, texto_fragmento, puntuacion_similitud
  FROM evidencias
  WHERE consulta_id = p_consulta_id
  ORDER BY id ASC;
END$$

DROP PROCEDURE IF EXISTS sp_documento_conocimiento_existe_por_hash$$
CREATE PROCEDURE sp_documento_conocimiento_existe_por_hash(IN p_hash_contenido VARCHAR(64))
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM documentos_conocimiento WHERE hash_contenido = p_hash_contenido
  ) AS existe;
END$$

DROP PROCEDURE IF EXISTS sp_documento_conocimiento_guardar$$
CREATE PROCEDURE sp_documento_conocimiento_guardar(
  IN p_ruta_origen VARCHAR(500),
  IN p_hash_contenido VARCHAR(64),
  IN p_fecha_creacion DATETIME
)
BEGIN
  INSERT INTO documentos_conocimiento (ruta_origen, hash_contenido, fecha_creacion)
  VALUES (p_ruta_origen, p_hash_contenido, p_fecha_creacion);
  SELECT id, ruta_origen, hash_contenido, fecha_creacion
  FROM documentos_conocimiento WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_documentos_conocimiento_listar$$
CREATE PROCEDURE sp_documentos_conocimiento_listar()
BEGIN
  SELECT id, ruta_origen, hash_contenido, fecha_creacion
  FROM documentos_conocimiento
  ORDER BY fecha_creacion DESC, id DESC;
END$$

DROP PROCEDURE IF EXISTS sp_documento_conocimiento_buscar_por_id$$
CREATE PROCEDURE sp_documento_conocimiento_buscar_por_id(IN p_documento_id INT)
BEGIN
  SELECT id, ruta_origen, hash_contenido, fecha_creacion
  FROM documentos_conocimiento
  WHERE id = p_documento_id
  LIMIT 1;
END$$


DROP PROCEDURE IF EXISTS sp_administrador_buscar_por_correo$$
CREATE PROCEDURE sp_administrador_buscar_por_correo(IN p_correo VARCHAR(150))
BEGIN
  SELECT id, nombre, correo, contrasena_hash, activo
  FROM administradores
  WHERE correo = LOWER(TRIM(p_correo)) AND activo = 1
  LIMIT 1;
END$$

DROP PROCEDURE IF EXISTS sp_administrador_crear$$
CREATE PROCEDURE sp_administrador_crear(
  IN p_nombre VARCHAR(120),
  IN p_correo VARCHAR(150),
  IN p_contrasena_hash VARCHAR(255)
)
BEGIN
  IF EXISTS (SELECT 1 FROM administradores WHERE correo = LOWER(TRIM(p_correo))) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ya existe un administrador con ese correo';
  END IF;
  INSERT INTO administradores (nombre, correo, contrasena_hash, activo)
  VALUES (TRIM(p_nombre), LOWER(TRIM(p_correo)), p_contrasena_hash, 1);
  SELECT id, nombre, correo, activo
  FROM administradores WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_admin_documentos_listar$$
CREATE PROCEDURE sp_admin_documentos_listar()
BEGIN
  SELECT d.id, d.ruta_origen, d.hash_contenido, d.fecha_creacion,
         COALESCE(a.titulo, '') AS titulo,
         COALESCE(a.tema, '') AS tema,
         COALESCE(a.estado, 'ACTIVO') AS estado,
         COALESCE(a.version, 1) AS version,
         a.fecha_actualizacion
  FROM documentos_conocimiento d
  LEFT JOIN documentos_conocimiento_administracion a ON a.documento_id = d.id
  ORDER BY d.fecha_creacion DESC, d.id DESC;
END$$

DROP PROCEDURE IF EXISTS sp_admin_documento_metadata_asegurar$$
CREATE PROCEDURE sp_admin_documento_metadata_asegurar(
  IN p_documento_id INT,
  IN p_titulo VARCHAR(200),
  IN p_tema VARCHAR(50)
)
BEGIN
  INSERT INTO documentos_conocimiento_administracion
    (documento_id, titulo, tema, estado, version)
  VALUES (p_documento_id, TRIM(p_titulo), TRIM(p_tema), 'ACTIVO', 1)
  ON DUPLICATE KEY UPDATE
    titulo = IF(titulo = '', VALUES(titulo), titulo),
    tema = IF(tema = '', VALUES(tema), tema);
  SELECT documento_id, titulo, tema, estado, version, fecha_actualizacion
  FROM documentos_conocimiento_administracion
  WHERE documento_id = p_documento_id;
END$$

DROP PROCEDURE IF EXISTS sp_admin_documento_contenido_actualizar$$
CREATE PROCEDURE sp_admin_documento_contenido_actualizar(
  IN p_documento_id INT,
  IN p_hash_contenido VARCHAR(64),
  IN p_titulo VARCHAR(200),
  IN p_tema VARCHAR(50)
)
BEGIN
  IF NOT EXISTS (SELECT 1 FROM documentos_conocimiento WHERE id = p_documento_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Documento no encontrado';
  END IF;
  IF EXISTS (
    SELECT 1 FROM documentos_conocimiento
    WHERE hash_contenido = p_hash_contenido AND id <> p_documento_id
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El contenido coincide con otro documento';
  END IF;
  UPDATE documentos_conocimiento
  SET hash_contenido = p_hash_contenido
  WHERE id = p_documento_id;
  INSERT INTO documentos_conocimiento_administracion
    (documento_id, titulo, tema, estado, version)
  VALUES (p_documento_id, TRIM(p_titulo), TRIM(p_tema), 'ACTIVO', 2)
  ON DUPLICATE KEY UPDATE
    titulo = VALUES(titulo),
    tema = VALUES(tema),
    version = version + 1,
    fecha_actualizacion = CURRENT_TIMESTAMP;
  SELECT documento_id, titulo, tema, estado, version, fecha_actualizacion
  FROM documentos_conocimiento_administracion
  WHERE documento_id = p_documento_id;
END$$

DROP PROCEDURE IF EXISTS sp_admin_documento_estado_actualizar$$
CREATE PROCEDURE sp_admin_documento_estado_actualizar(
  IN p_documento_id INT,
  IN p_estado VARCHAR(10)
)
BEGIN
  IF p_estado NOT IN ('ACTIVO', 'INACTIVO') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Estado de documento inválido';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM documentos_conocimiento WHERE id = p_documento_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Documento no encontrado';
  END IF;
  INSERT INTO documentos_conocimiento_administracion
    (documento_id, titulo, tema, estado, version)
  VALUES (p_documento_id, '', '', p_estado, 1)
  ON DUPLICATE KEY UPDATE
    estado = VALUES(estado),
    fecha_actualizacion = CURRENT_TIMESTAMP;
  SELECT documento_id, estado, version, fecha_actualizacion
  FROM documentos_conocimiento_administracion
  WHERE documento_id = p_documento_id;
END$$

DROP PROCEDURE IF EXISTS sp_metrica_consulta_guardar$$
CREATE PROCEDURE sp_metrica_consulta_guardar(
  IN p_identificador_solicitud CHAR(36),
  IN p_codigo_respuesta SMALLINT,
  IN p_duracion_ms INT UNSIGNED
)
BEGIN
  INSERT INTO metricas_consulta
    (identificador_solicitud, codigo_respuesta, duracion_ms)
  VALUES (p_identificador_solicitud, p_codigo_respuesta, p_duracion_ms)
  ON DUPLICATE KEY UPDATE
    codigo_respuesta = VALUES(codigo_respuesta),
    duracion_ms = VALUES(duracion_ms);
END$$

DROP PROCEDURE IF EXISTS sp_metricas_consulta_resumen$$
CREATE PROCEDURE sp_metricas_consulta_resumen(IN p_dias INT)
BEGIN
  DECLARE v_dias INT DEFAULT 30;
  SET v_dias = LEAST(GREATEST(COALESCE(p_dias, 30), 1), 365);
  SELECT COUNT(*) AS total_solicitudes,
         COALESCE(SUM(codigo_respuesta BETWEEN 200 AND 299), 0) AS consultas_atendidas,
         COALESCE(SUM(codigo_respuesta >= 400), 0) AS solicitudes_con_error,
         COALESCE(ROUND(AVG(duracion_ms), 2), 0) AS promedio_ms,
         COALESCE(MAX(duracion_ms), 0) AS maximo_ms
  FROM metricas_consulta
  WHERE fecha_creacion >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL v_dias DAY);
END$$

DROP PROCEDURE IF EXISTS sp_evaluacion_ia_guardar$$
CREATE PROCEDURE sp_evaluacion_ia_guardar(
  IN p_dataset_version VARCHAR(100),
  IN p_proveedor VARCHAR(40),
  IN p_modelo VARCHAR(120),
  IN p_precision DECIMAL(8,6),
  IN p_pertinencia DECIMAL(8,6),
  IN p_fidelidad DECIMAL(8,6),
  IN p_recall_contexto DECIMAL(8,6),
  IN p_duracion_promedio_ms DECIMAL(12,3),
  IN p_total_muestras INT UNSIGNED
)
BEGIN
  INSERT INTO evaluaciones_ia
    (dataset_version, proveedor, modelo, precision_promedio, pertinencia_promedio,
     fidelidad_promedio, recall_contexto_promedio, duracion_promedio_ms, total_muestras)
  VALUES
    (p_dataset_version, p_proveedor, p_modelo, p_precision, p_pertinencia,
     p_fidelidad, p_recall_contexto, p_duracion_promedio_ms, p_total_muestras);
  SELECT id, dataset_version, proveedor, modelo, precision_promedio, pertinencia_promedio,
         fidelidad_promedio, recall_contexto_promedio, duracion_promedio_ms, total_muestras,
         fecha_creacion
  FROM evaluaciones_ia WHERE id = LAST_INSERT_ID();
END$$

DROP PROCEDURE IF EXISTS sp_evaluacion_ia_detalle_guardar$$
CREATE PROCEDURE sp_evaluacion_ia_detalle_guardar(
  IN p_evaluacion_id BIGINT,
  IN p_item_id VARCHAR(100),
  IN p_pregunta TEXT,
  IN p_precision DECIMAL(8,6),
  IN p_pertinencia DECIMAL(8,6),
  IN p_duracion_ms DECIMAL(12,3),
  IN p_respuesta TEXT
)
BEGIN
  INSERT INTO evaluaciones_ia_detalle
    (evaluacion_id, item_id, pregunta, precision_score, pertinencia, duracion_ms, respuesta)
  VALUES
    (p_evaluacion_id, p_item_id, p_pregunta, p_precision, p_pertinencia, p_duracion_ms, p_respuesta);
END$$

DROP PROCEDURE IF EXISTS sp_evaluaciones_ia_listar$$
CREATE PROCEDURE sp_evaluaciones_ia_listar()
BEGIN
  SELECT id, dataset_version, proveedor, modelo, precision_promedio, pertinencia_promedio,
         fidelidad_promedio, recall_contexto_promedio, duracion_promedio_ms, total_muestras,
         fecha_creacion
  FROM evaluaciones_ia ORDER BY fecha_creacion DESC, id DESC;
END$$

DROP PROCEDURE IF EXISTS sp_evaluacion_ia_detalles_listar$$
CREATE PROCEDURE sp_evaluacion_ia_detalles_listar(IN p_evaluacion_id BIGINT)
BEGIN
  SELECT item_id, pregunta, precision_score, pertinencia, duracion_ms, respuesta
  FROM evaluaciones_ia_detalle
  WHERE evaluacion_id = p_evaluacion_id
  ORDER BY id ASC;
END$$

DELIMITER ;
