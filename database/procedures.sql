-- Agro Asistente: procedimientos para operaciones MySQL del backend.
-- Ejecutar después de database/schema.sql. El backend debe usar CALL mediante callproc;
-- no mantener SELECT/INSERT/UPDATE del dominio dentro de adaptadores Python.
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
END$

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

DELIMITER ;
