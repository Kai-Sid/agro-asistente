-- Migración idempotente del PMV3. Ejecutar después de database/schema.sql.
USE agro_asistente;

CREATE TABLE IF NOT EXISTS administradores (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_administradores_correo (correo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS documentos_conocimiento_administracion (
    documento_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    tema VARCHAR(50) NOT NULL,
    estado ENUM('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO',
    version INT NOT NULL DEFAULT 1,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (documento_id),
    CONSTRAINT fk_documento_admin_documento
        FOREIGN KEY (documento_id) REFERENCES documentos_conocimiento (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS metricas_consulta (
    id BIGINT NOT NULL AUTO_INCREMENT,
    identificador_solicitud CHAR(36) NOT NULL,
    codigo_respuesta SMALLINT NOT NULL,
    duracion_ms INT UNSIGNED NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_metricas_consulta_fecha_codigo (fecha_creacion, codigo_respuesta),
    UNIQUE KEY uq_metricas_solicitud (identificador_solicitud)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS evaluaciones_ia (
    id BIGINT NOT NULL AUTO_INCREMENT,
    dataset_version VARCHAR(100) NOT NULL,
    proveedor VARCHAR(40) NOT NULL,
    modelo VARCHAR(120) NOT NULL,
    precision_promedio DECIMAL(8,6) NULL,
    pertinencia_promedio DECIMAL(8,6) NULL,
    fidelidad_promedio DECIMAL(8,6) NULL,
    recall_contexto_promedio DECIMAL(8,6) NULL,
    duracion_promedio_ms DECIMAL(12,3) NOT NULL DEFAULT 0,
    total_muestras INT UNSIGNED NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_evaluaciones_fecha (fecha_creacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS evaluaciones_ia_detalle (
    id BIGINT NOT NULL AUTO_INCREMENT,
    evaluacion_id BIGINT NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    pregunta TEXT NOT NULL,
    precision DECIMAL(8,6) NULL,
    pertinencia DECIMAL(8,6) NULL,
    duracion_ms DECIMAL(12,3) NOT NULL DEFAULT 0,
    respuesta TEXT NOT NULL,
    PRIMARY KEY (id),
    KEY idx_evaluacion_detalle (evaluacion_id),
    CONSTRAINT fk_evaluacion_detalle_evaluacion
        FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones_ia (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
