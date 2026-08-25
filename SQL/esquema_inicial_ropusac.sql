-- =========================================================
-- 1. TIPOS ENUMERADOS
-- =========================================================

CREATE TYPE tipo_documento_enum AS ENUM (
    'DNI',
    'RUC',
    'SIN_DOCUMENTO'
);

CREATE TYPE moneda_enum AS ENUM (
    'PEN',
    'USD'
);

CREATE TYPE estado_cotizacion_enum AS ENUM (
    'BORRADOR',
    'EMITIDA',
    'ENVIADA',
    'APROBADA',
    'RECHAZADA',
    'VENCIDA',
    'CONVERTIDA_VENTA',
    'ANULADA'
);

CREATE TYPE estado_importacion_enum AS ENUM (
    'PROCESANDO',
    'COMPLETADA',
    'COMPLETADA_CON_ERRORES',
    'FALLIDA'
);

CREATE TYPE estado_venta_enum AS ENUM (
    'PENDIENTE_BOLETA',
    'FACTURADA',
    'ANULADA'
);

CREATE TYPE estado_boleta_enum AS ENUM (
    'PENDIENTE',
    'GENERADA',
    'ERROR',
    'ANULADA'
);

CREATE TYPE estado_envio_enum AS ENUM (
    'PENDIENTE',
    'ENVIADO',
    'ERROR'
);

CREATE TYPE tipo_documento_envio_enum AS ENUM (
    'COTIZACION',
    'BOLETA'
);

CREATE TYPE servicio_api_enum AS ENUM (
    'APIS_NET',
    'GEOAPIFY',
    'IMGBB',
    'EXCHANGE_RATE',
    'NUBEFACT',
    'SMTP'
);


-- =========================================================
-- 2. SECUENCIAS
-- =========================================================

CREATE SEQUENCE secuencia_cotizaciones START 1;
CREATE SEQUENCE secuencia_ventas START 1;


-- =========================================================
-- 3. ROLES
-- =========================================================

CREATE TABLE roles (
    id_rol BIGSERIAL PRIMARY KEY,

    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =========================================================
-- 4. PERMISOS
-- =========================================================

CREATE TABLE permisos (
    id_permiso BIGSERIAL PRIMARY KEY,

    codigo VARCHAR(80) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(255),

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =========================================================
-- 5. ROLES - PERMISOS
-- =========================================================

CREATE TABLE roles_permisos (
    id_rol BIGINT NOT NULL,
    id_permiso BIGINT NOT NULL,

    PRIMARY KEY (id_rol, id_permiso),

    CONSTRAINT fk_roles_permisos_rol
        FOREIGN KEY (id_rol)
        REFERENCES roles(id_rol)
        ON DELETE CASCADE,

    CONSTRAINT fk_roles_permisos_permiso
        FOREIGN KEY (id_permiso)
        REFERENCES permisos(id_permiso)
        ON DELETE CASCADE
);


-- =========================================================
-- 6. USUARIOS
-- =========================================================

CREATE TABLE usuarios (
    id_usuario BIGSERIAL PRIMARY KEY,

    id_rol BIGINT NOT NULL,

    tipo_documento tipo_documento_enum NOT NULL DEFAULT 'SIN_DOCUMENTO',
    numero_documento VARCHAR(20),

    nombres VARCHAR(120) NOT NULL,
    apellidos VARCHAR(120) NOT NULL,

    correo VARCHAR(180) NOT NULL,
    hash_contrasena VARCHAR(255) NOT NULL,

    celular VARCHAR(30),

    direccion VARCHAR(300),

    geoapify_place_id VARCHAR(255),
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),

    datos_obtenidos_api BOOLEAN NOT NULL DEFAULT FALSE,
    api_consultada_en TIMESTAMPTZ,

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    ultimo_acceso_en TIMESTAMPTZ,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol)
        REFERENCES roles(id_rol)
        ON DELETE RESTRICT,

    CONSTRAINT chk_usuario_tipo_documento
        CHECK (
            tipo_documento IN ('DNI', 'SIN_DOCUMENTO')
        ),

    CONSTRAINT chk_usuario_documento
        CHECK (
            (
                tipo_documento = 'DNI'
                AND numero_documento ~ '^[0-9]{8}$'
            )
            OR
            (
                tipo_documento = 'SIN_DOCUMENTO'
                AND numero_documento IS NULL
            )
        ),

    CONSTRAINT chk_usuario_latitud
        CHECK (
            latitud IS NULL
            OR latitud BETWEEN -90 AND 90
        ),

    CONSTRAINT chk_usuario_longitud
        CHECK (
            longitud IS NULL
            OR longitud BETWEEN -180 AND 180
        )
);

CREATE UNIQUE INDEX uq_usuarios_correo
    ON usuarios (LOWER(correo));

CREATE UNIQUE INDEX uq_usuarios_documento
    ON usuarios (numero_documento)
    WHERE numero_documento IS NOT NULL;


-- =========================================================
-- 7. PROVEEDORES
-- =========================================================

CREATE TABLE proveedores (
    id_proveedor BIGSERIAL PRIMARY KEY,

    tipo_documento tipo_documento_enum NOT NULL DEFAULT 'SIN_DOCUMENTO',
    numero_documento VARCHAR(20),

    razon_social VARCHAR(200) NOT NULL,
    nombre_comercial VARCHAR(200),

    correo VARCHAR(180),
    celular VARCHAR(30),
    telefono VARCHAR(30),

    direccion_fiscal VARCHAR(300),

    datos_obtenidos_api BOOLEAN NOT NULL DEFAULT FALSE,
    api_consultada_en TIMESTAMPTZ,

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_por BIGINT NOT NULL,
    actualizado_por BIGINT,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_proveedor_creado_por
        FOREIGN KEY (creado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT fk_proveedor_actualizado_por
        FOREIGN KEY (actualizado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_proveedor_tipo_documento
        CHECK (
            tipo_documento IN ('RUC', 'SIN_DOCUMENTO')
        ),

    CONSTRAINT chk_proveedor_documento
        CHECK (
            (
                tipo_documento = 'RUC'
                AND numero_documento ~ '^[0-9]{11}$'
            )
            OR
            (
                tipo_documento = 'SIN_DOCUMENTO'
                AND numero_documento IS NULL
            )
        )
);

CREATE UNIQUE INDEX uq_proveedores_documento
    ON proveedores(numero_documento)
    WHERE numero_documento IS NOT NULL;


-- =========================================================
-- 8. CLIENTES
-- =========================================================

CREATE TABLE clientes (
    id_cliente BIGSERIAL PRIMARY KEY,

    tipo_documento tipo_documento_enum NOT NULL,
    numero_documento VARCHAR(20),

    nombres VARCHAR(150),
    apellidos VARCHAR(150),
    razon_social VARCHAR(200),

    correo VARCHAR(180),
    celular VARCHAR(30),
    telefono VARCHAR(30),

    direccion VARCHAR(300),

    geoapify_place_id VARCHAR(255),
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),

    datos_obtenidos_api BOOLEAN NOT NULL DEFAULT FALSE,
    api_consultada_en TIMESTAMPTZ,

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_por BIGINT NOT NULL,
    actualizado_por BIGINT,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_cliente_creado_por
        FOREIGN KEY (creado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT fk_cliente_actualizado_por
        FOREIGN KEY (actualizado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_cliente_documento
        CHECK (
            (
                tipo_documento = 'DNI'
                AND numero_documento ~ '^[0-9]{8}$'
            )
            OR
            (
                tipo_documento = 'RUC'
                AND numero_documento ~ '^[0-9]{11}$'
            )
            OR
            (
                tipo_documento = 'SIN_DOCUMENTO'
                AND numero_documento IS NULL
            )
        ),

    CONSTRAINT chk_cliente_nombre
        CHECK (
            razon_social IS NOT NULL
            OR nombres IS NOT NULL
        ),

    CONSTRAINT chk_cliente_latitud
        CHECK (
            latitud IS NULL
            OR latitud BETWEEN -90 AND 90
        ),

    CONSTRAINT chk_cliente_longitud
        CHECK (
            longitud IS NULL
            OR longitud BETWEEN -180 AND 180
        )
);

CREATE UNIQUE INDEX uq_clientes_documento
    ON clientes(numero_documento)
    WHERE numero_documento IS NOT NULL;

CREATE INDEX idx_clientes_correo
    ON clientes(LOWER(correo));


-- =========================================================
-- 9. PRODUCTOS
-- =========================================================

CREATE TABLE productos (
    id_producto BIGSERIAL PRIMARY KEY,

    id_proveedor BIGINT NOT NULL,

    codigo_producto VARCHAR(60) NOT NULL UNIQUE,
    codigo_proveedor VARCHAR(100),

    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,

    categoria VARCHAR(150),
    marca VARCHAR(120),
    modelo VARCHAR(120),

    unidad_medida VARCHAR(50) NOT NULL DEFAULT 'UNIDAD',

    precio_base_actual NUMERIC(14,2) NOT NULL,
    precio_venta_actual NUMERIC(14,2),

    moneda_precio moneda_enum NOT NULL DEFAULT 'PEN',

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_por BIGINT NOT NULL,
    actualizado_por BIGINT,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_producto_proveedor
        FOREIGN KEY (id_proveedor)
        REFERENCES proveedores(id_proveedor)
        ON DELETE RESTRICT,

    CONSTRAINT fk_producto_creado_por
        FOREIGN KEY (creado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT fk_producto_actualizado_por
        FOREIGN KEY (actualizado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_precio_base
        CHECK (precio_base_actual >= 0),

    CONSTRAINT chk_precio_venta
        CHECK (
            precio_venta_actual IS NULL
            OR precio_venta_actual >= 0
        )
);

CREATE INDEX idx_productos_proveedor
    ON productos(id_proveedor);

CREATE INDEX idx_productos_nombre
    ON productos(nombre);

CREATE INDEX idx_productos_activos
    ON productos(activo);


-- =========================================================
-- 10. IMAGENES DE PRODUCTOS - IMGBB
-- =========================================================

CREATE TABLE imagenes_productos (
    id_imagen_producto BIGSERIAL PRIMARY KEY,

    id_producto BIGINT NOT NULL,

    id_imagen_externa VARCHAR(255),

    url_imagen TEXT NOT NULL,
    url_visualizacion TEXT,
    url_eliminacion TEXT,

    nombre_archivo_original VARCHAR(255),

    es_principal BOOLEAN NOT NULL DEFAULT TRUE,
    activa BOOLEAN NOT NULL DEFAULT TRUE,

    subida_por BIGINT NOT NULL,

    creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    eliminada_en TIMESTAMPTZ,

    CONSTRAINT fk_imagen_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE CASCADE,

    CONSTRAINT fk_imagen_subida_por
        FOREIGN KEY (subida_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT
);

CREATE INDEX idx_imagenes_producto
    ON imagenes_productos(id_producto);

CREATE UNIQUE INDEX uq_imagen_principal_producto
    ON imagenes_productos(id_producto)
    WHERE es_principal = TRUE
      AND activa = TRUE;


-- =========================================================
-- 11. HISTORIAL DE PRECIOS BASE
-- =========================================================

CREATE TABLE historial_precios_base (
    id_historial_precio_base BIGSERIAL PRIMARY KEY,

    id_producto BIGINT NOT NULL,

    precio_anterior NUMERIC(14,2),
    precio_nuevo NUMERIC(14,2) NOT NULL,

    cambiado_por BIGINT NOT NULL,

    cambiado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_historial_base_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE RESTRICT,

    CONSTRAINT fk_historial_base_usuario
        FOREIGN KEY (cambiado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT
);

CREATE INDEX idx_historial_base_producto
    ON historial_precios_base(id_producto);


-- =========================================================
-- 12. HISTORIAL DE PRECIOS DE VENTA
-- =========================================================

CREATE TABLE historial_precios_venta (
    id_historial_precio_venta BIGSERIAL PRIMARY KEY,

    id_producto BIGINT NOT NULL,

    precio_anterior NUMERIC(14,2),
    precio_nuevo NUMERIC(14,2) NOT NULL,

    cambiado_por BIGINT NOT NULL,

    cambiado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_historial_venta_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE RESTRICT,

    CONSTRAINT fk_historial_venta_usuario
        FOREIGN KEY (cambiado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT
);

CREATE INDEX idx_historial_venta_producto
    ON historial_precios_venta(id_producto);


-- =========================================================
-- 13. IMPORTACIONES DE PRODUCTOS POR EXCEL
-- =========================================================

CREATE TABLE importaciones_productos (
    id_importacion BIGSERIAL PRIMARY KEY,

    nombre_archivo VARCHAR(255) NOT NULL,

    estado estado_importacion_enum NOT NULL
        DEFAULT 'PROCESANDO',

    total_filas INTEGER NOT NULL DEFAULT 0,
    filas_correctas INTEGER NOT NULL DEFAULT 0,
    filas_con_error INTEGER NOT NULL DEFAULT 0,

    detalle_errores JSONB,

    importado_por BIGINT NOT NULL,

    iniciado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizado_en TIMESTAMPTZ,

    CONSTRAINT fk_importacion_usuario
        FOREIGN KEY (importado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_importacion_totales
        CHECK (
            total_filas >= 0
            AND filas_correctas >= 0
            AND filas_con_error >= 0
        )
);


-- =========================================================
-- 14. TIPOS DE CAMBIO
-- ExchangeRate-API
-- soles_por_dolar representa cuantos PEN equivalen a 1 USD.
-- Ejemplo conceptual: 1 USD = X PEN.
-- =========================================================

CREATE TABLE tipos_cambio (
    id_tipo_cambio BIGSERIAL PRIMARY KEY,

    soles_por_dolar NUMERIC(12,6) NOT NULL,

    proveedor VARCHAR(100) NOT NULL DEFAULT 'ExchangeRate-API',

    fecha_tipo_cambio DATE NOT NULL DEFAULT CURRENT_DATE,

    obtenido_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    identificador_consulta VARCHAR(255),

    CONSTRAINT chk_tipo_cambio_positivo
        CHECK (soles_por_dolar > 0)
);

CREATE INDEX idx_tipo_cambio_fecha
    ON tipos_cambio(fecha_tipo_cambio DESC);


-- =========================================================
-- 15. COTIZACIONES
-- =========================================================

CREATE TABLE cotizaciones (
    id_cotizacion BIGSERIAL PRIMARY KEY,

    numero_cotizacion VARCHAR(40) NOT NULL UNIQUE,

    id_cliente BIGINT NOT NULL,
    id_vendedor BIGINT NOT NULL,

    id_tipo_cambio BIGINT NOT NULL,

    moneda moneda_enum NOT NULL,

    tipo_cambio_soles_por_dolar NUMERIC(12,6) NOT NULL,

    fecha_emision DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_vigencia DATE NOT NULL,

    estado estado_cotizacion_enum NOT NULL DEFAULT 'BORRADOR',

    subtotal NUMERIC(14,2) NOT NULL DEFAULT 0,
    total NUMERIC(14,2) NOT NULL DEFAULT 0,

    total_equivalente NUMERIC(14,2)
    GENERATED ALWAYS AS (
        CASE
            WHEN moneda = 'PEN'
                THEN ROUND(total / tipo_cambio_soles_por_dolar, 2)
            ELSE
                ROUND(total * tipo_cambio_soles_por_dolar, 2)
        END
    ) STORED,

    observaciones TEXT,

    pdf_nombre_archivo VARCHAR(255),
    pdf_url TEXT,
    pdf_generado_en TIMESTAMPTZ,

    enviada_correo_en TIMESTAMPTZ,
    aprobada_en TIMESTAMPTZ,

    actualizado_por BIGINT,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_cotizacion_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
        ON DELETE RESTRICT,

    CONSTRAINT fk_cotizacion_vendedor
        FOREIGN KEY (id_vendedor)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT fk_cotizacion_tipo_cambio
        FOREIGN KEY (id_tipo_cambio)
        REFERENCES tipos_cambio(id_tipo_cambio)
        ON DELETE RESTRICT,

    CONSTRAINT fk_cotizacion_actualizado_por
        FOREIGN KEY (actualizado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_cotizacion_vigencia
        CHECK (fecha_vigencia >= fecha_emision),

    CONSTRAINT chk_cotizacion_tipo_cambio
        CHECK (tipo_cambio_soles_por_dolar > 0),

    CONSTRAINT chk_cotizacion_total
        CHECK (
            subtotal >= 0
            AND total >= 0
        )
);

CREATE INDEX idx_cotizacion_cliente
    ON cotizaciones(id_cliente);

CREATE INDEX idx_cotizacion_vendedor
    ON cotizaciones(id_vendedor);

CREATE INDEX idx_cotizacion_estado
    ON cotizaciones(estado);

CREATE INDEX idx_cotizacion_vigencia
    ON cotizaciones(fecha_vigencia);


-- =========================================================
-- 16. DETALLE DE COTIZACIONES
-- =========================================================

CREATE TABLE detalle_cotizaciones (
    id_detalle_cotizacion BIGSERIAL PRIMARY KEY,

    id_cotizacion BIGINT NOT NULL,
    id_producto BIGINT NOT NULL,

    -- Snapshot historico
    codigo_producto VARCHAR(60) NOT NULL,
    nombre_producto VARCHAR(200) NOT NULL,

    cantidad NUMERIC(14,3) NOT NULL,

    -- Precio original del catalogo en PEN
    precio_unitario_pen_referencia NUMERIC(14,2) NOT NULL,

    -- Precio expresado en la moneda elegida para la cotizacion
    precio_unitario NUMERIC(14,2) NOT NULL,

    subtotal NUMERIC(14,2)
    GENERATED ALWAYS AS (
        ROUND(cantidad * precio_unitario, 2)
    ) STORED,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_detalle_cotizacion
        FOREIGN KEY (id_cotizacion)
        REFERENCES cotizaciones(id_cotizacion)
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE RESTRICT,

    CONSTRAINT chk_detalle_cantidad
        CHECK (cantidad > 0),

    CONSTRAINT chk_detalle_precio
        CHECK (
            precio_unitario >= 0
            AND precio_unitario_pen_referencia >= 0
        )
);

CREATE INDEX idx_detalle_cotizacion
    ON detalle_cotizaciones(id_cotizacion);

CREATE INDEX idx_detalle_cotizacion_producto
    ON detalle_cotizaciones(id_producto);


-- =========================================================
-- 17. HISTORIAL DE ESTADOS DE COTIZACION
-- =========================================================

CREATE TABLE historial_estados_cotizacion (
    id_historial_estado BIGSERIAL PRIMARY KEY,

    id_cotizacion BIGINT NOT NULL,

    estado_anterior estado_cotizacion_enum,
    estado_nuevo estado_cotizacion_enum NOT NULL,

    cambiado_por BIGINT,

    observacion VARCHAR(500),

    cambiado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_historial_cotizacion
        FOREIGN KEY (id_cotizacion)
        REFERENCES cotizaciones(id_cotizacion)
        ON DELETE RESTRICT,

    CONSTRAINT fk_historial_cotizacion_usuario
        FOREIGN KEY (cambiado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT
);

CREATE INDEX idx_historial_estado_cotizacion
    ON historial_estados_cotizacion(id_cotizacion);


-- =========================================================
-- 18. VENTAS
-- Una venta SIEMPRE nace de una cotizacion aprobada.
-- =========================================================

CREATE TABLE ventas (
    id_venta BIGSERIAL PRIMARY KEY,

    numero_venta VARCHAR(40) NOT NULL UNIQUE,

    id_cotizacion BIGINT NOT NULL UNIQUE,
    id_cliente BIGINT NOT NULL,
    id_vendedor BIGINT NOT NULL,

    fecha_venta DATE NOT NULL DEFAULT CURRENT_DATE,

    moneda moneda_enum NOT NULL,

    tipo_cambio_soles_por_dolar NUMERIC(12,6) NOT NULL,

    subtotal NUMERIC(14,2) NOT NULL,
    total NUMERIC(14,2) NOT NULL,

    estado estado_venta_enum NOT NULL
        DEFAULT 'PENDIENTE_BOLETA',

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_venta_cotizacion
        FOREIGN KEY (id_cotizacion)
        REFERENCES cotizaciones(id_cotizacion)
        ON DELETE RESTRICT,

    CONSTRAINT fk_venta_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
        ON DELETE RESTRICT,

    CONSTRAINT fk_venta_vendedor
        FOREIGN KEY (id_vendedor)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_venta_tipo_cambio
        CHECK (tipo_cambio_soles_por_dolar > 0),

    CONSTRAINT chk_venta_total
        CHECK (
            subtotal >= 0
            AND total >= 0
        )
);

CREATE INDEX idx_ventas_cliente
    ON ventas(id_cliente);

CREATE INDEX idx_ventas_vendedor
    ON ventas(id_vendedor);

CREATE INDEX idx_ventas_estado
    ON ventas(estado);


-- =========================================================
-- 19. DETALLE DE VENTAS
-- Snapshot inmutable de lo que realmente se vendio
-- =========================================================

CREATE TABLE detalle_ventas (
    id_detalle_venta BIGSERIAL PRIMARY KEY,

    id_venta BIGINT NOT NULL,
    id_producto BIGINT NOT NULL,

    codigo_producto VARCHAR(60) NOT NULL,
    nombre_producto VARCHAR(200) NOT NULL,

    cantidad NUMERIC(14,3) NOT NULL,
    precio_unitario NUMERIC(14,2) NOT NULL,

    subtotal NUMERIC(14,2)
    GENERATED ALWAYS AS (
        ROUND(cantidad * precio_unitario, 2)
    ) STORED,

    CONSTRAINT fk_detalle_venta
        FOREIGN KEY (id_venta)
        REFERENCES ventas(id_venta)
        ON DELETE RESTRICT,

    CONSTRAINT fk_detalle_venta_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE RESTRICT,

    CONSTRAINT chk_detalle_venta_cantidad
        CHECK (cantidad > 0),

    CONSTRAINT chk_detalle_venta_precio
        CHECK (precio_unitario >= 0)
);

CREATE INDEX idx_detalle_venta
    ON detalle_ventas(id_venta);


-- =========================================================
-- 20. BOLETAS
-- La boleta pertenece a una VENTA, nunca directamente
-- a una cotizacion.
-- =========================================================

CREATE TABLE boletas (
    id_boleta BIGSERIAL PRIMARY KEY,

    id_venta BIGINT NOT NULL UNIQUE,

    estado estado_boleta_enum NOT NULL DEFAULT 'PENDIENTE',

    tipo_comprobante VARCHAR(30) NOT NULL DEFAULT 'BOLETA',

    serie VARCHAR(20),
    numero VARCHAR(30),

    identificador_nubefact VARCHAR(255),

    fecha_emision DATE,

    moneda moneda_enum NOT NULL,
    total NUMERIC(14,2) NOT NULL,

    -- Snapshot del cliente usado para facturacion
    cliente_tipo_documento tipo_documento_enum,
    cliente_numero_documento VARCHAR(20),
    cliente_nombre VARCHAR(250) NOT NULL,
    cliente_direccion VARCHAR(300),
    cliente_correo VARCHAR(180),

    enlace_pdf TEXT,
    enlace_xml TEXT,
    enlace_cdr TEXT,

    codigo_hash TEXT,
    cadena_codigo_qr TEXT,

    respuesta_nubefact JSONB,
    mensaje_nubefact TEXT,

    generada_en TIMESTAMPTZ,

    creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_boleta_venta
        FOREIGN KEY (id_venta)
        REFERENCES ventas(id_venta)
        ON DELETE RESTRICT,

    CONSTRAINT chk_boleta_total
        CHECK (total >= 0)
);

CREATE UNIQUE INDEX uq_boleta_serie_numero
    ON boletas(serie, numero)
    WHERE serie IS NOT NULL
      AND numero IS NOT NULL;

CREATE INDEX idx_boletas_estado
    ON boletas(estado);


-- =========================================================
-- 21. ENVIOS DE CORREO SMTP
-- =========================================================

CREATE TABLE envios_correo (
    id_envio_correo BIGSERIAL PRIMARY KEY,

    tipo_documento tipo_documento_envio_enum NOT NULL,

    id_cotizacion BIGINT,
    id_boleta BIGINT,

    destinatario VARCHAR(180) NOT NULL,
    asunto VARCHAR(300) NOT NULL,

    estado estado_envio_enum NOT NULL DEFAULT 'PENDIENTE',

    numero_intento INTEGER NOT NULL DEFAULT 1,

    mensaje_error TEXT,

    enviado_por BIGINT NOT NULL,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enviado_en TIMESTAMPTZ,

    CONSTRAINT fk_envio_cotizacion
        FOREIGN KEY (id_cotizacion)
        REFERENCES cotizaciones(id_cotizacion)
        ON DELETE RESTRICT,

    CONSTRAINT fk_envio_boleta
        FOREIGN KEY (id_boleta)
        REFERENCES boletas(id_boleta)
        ON DELETE RESTRICT,

    CONSTRAINT fk_envio_usuario
        FOREIGN KEY (enviado_por)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT chk_envio_documento
        CHECK (
            (
                tipo_documento = 'COTIZACION'
                AND id_cotizacion IS NOT NULL
                AND id_boleta IS NULL
            )
            OR
            (
                tipo_documento = 'BOLETA'
                AND id_boleta IS NOT NULL
                AND id_cotizacion IS NULL
            )
        ),

    CONSTRAINT chk_numero_intento
        CHECK (numero_intento > 0)
);

CREATE INDEX idx_envios_cotizacion
    ON envios_correo(id_cotizacion);

CREATE INDEX idx_envios_boleta
    ON envios_correo(id_boleta);

CREATE INDEX idx_envios_estado
    ON envios_correo(estado);


-- =========================================================
-- 22. REGISTRO DE INTEGRACIONES / APIS
-- No guardar API Keys ni contrasenas.
-- =========================================================

CREATE TABLE registros_api (
    id_registro_api BIGSERIAL PRIMARY KEY,

    servicio servicio_api_enum NOT NULL,

    operacion VARCHAR(120) NOT NULL,

    id_usuario BIGINT,

    entidad_relacionada VARCHAR(80),
    id_entidad_relacionada BIGINT,

    codigo_http INTEGER,

    exitoso BOOLEAN NOT NULL,

    identificador_externo VARCHAR(255),

    mensaje TEXT,

    respuesta_resumida JSONB,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_registro_api_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE SET NULL
);

CREATE INDEX idx_registros_api_servicio
    ON registros_api(servicio);

CREATE INDEX idx_registros_api_fecha
    ON registros_api(creado_en DESC);


-- =========================================================
-- 23. BITACORA GENERAL DE OPERACIONES
-- =========================================================

CREATE TABLE bitacora_operaciones (
    id_bitacora BIGSERIAL PRIMARY KEY,

    id_usuario BIGINT,

    accion VARCHAR(100) NOT NULL,
    modulo VARCHAR(100) NOT NULL,

    entidad VARCHAR(100),
    id_entidad BIGINT,

    descripcion TEXT,

    datos_adicionales JSONB,

    direccion_ip VARCHAR(50),

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_bitacora_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE SET NULL
);

CREATE INDEX idx_bitacora_usuario
    ON bitacora_operaciones(id_usuario);

CREATE INDEX idx_bitacora_fecha
    ON bitacora_operaciones(creado_en DESC);

CREATE INDEX idx_bitacora_modulo
    ON bitacora_operaciones(modulo);


-- =========================================================
-- 24. FUNCION GENERICA PARA actualizado_en
-- =========================================================

CREATE OR REPLACE FUNCTION fn_actualizar_fecha_modificacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_roles_actualizado
BEFORE UPDATE ON roles
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_modificacion();


CREATE TRIGGER trg_usuarios_actualizado
BEFORE UPDATE ON usuarios
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_modificacion();


CREATE TRIGGER trg_proveedores_actualizado
BEFORE UPDATE ON proveedores
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_modificacion();


CREATE TRIGGER trg_clientes_actualizado
BEFORE UPDATE ON clientes
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_modificacion();


CREATE TRIGGER trg_productos_actualizado
BEFORE UPDATE ON productos
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_modificacion();


CREATE TRIGGER trg_cotizaciones_actualizado
BEFORE UPDATE ON cotizaciones
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_fecha_modificacion();


-- =========================================================
-- 25. TRIGGER PARA actualizada_en DE BOLETAS
-- =========================================================

CREATE OR REPLACE FUNCTION fn_actualizar_boleta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.actualizada_en = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_boletas_actualizada
BEFORE UPDATE ON boletas
FOR EACH ROW
EXECUTE FUNCTION fn_actualizar_boleta();


-- =========================================================
-- 26. HISTORIAL AUTOMATICO DE PRECIOS
-- =========================================================

CREATE OR REPLACE FUNCTION fn_registrar_historial_precios()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_usuario BIGINT;
BEGIN

    v_usuario := COALESCE(NEW.actualizado_por, NEW.creado_por);

    IF TG_OP = 'INSERT' THEN

        INSERT INTO historial_precios_base (
            id_producto,
            precio_anterior,
            precio_nuevo,
            cambiado_por
        )
        VALUES (
            NEW.id_producto,
            NULL,
            NEW.precio_base_actual,
            NEW.creado_por
        );

        IF NEW.precio_venta_actual IS NOT NULL THEN

            INSERT INTO historial_precios_venta (
                id_producto,
                precio_anterior,
                precio_nuevo,
                cambiado_por
            )
            VALUES (
                NEW.id_producto,
                NULL,
                NEW.precio_venta_actual,
                NEW.creado_por
            );

        END IF;

    ELSE

        IF OLD.precio_base_actual
           IS DISTINCT FROM NEW.precio_base_actual THEN

            INSERT INTO historial_precios_base (
                id_producto,
                precio_anterior,
                precio_nuevo,
                cambiado_por
            )
            VALUES (
                NEW.id_producto,
                OLD.precio_base_actual,
                NEW.precio_base_actual,
                v_usuario
            );

        END IF;


        IF OLD.precio_venta_actual
           IS DISTINCT FROM NEW.precio_venta_actual
           AND NEW.precio_venta_actual IS NOT NULL THEN

            INSERT INTO historial_precios_venta (
                id_producto,
                precio_anterior,
                precio_nuevo,
                cambiado_por
            )
            VALUES (
                NEW.id_producto,
                OLD.precio_venta_actual,
                NEW.precio_venta_actual,
                v_usuario
            );

        END IF;

    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_historial_precios_producto
AFTER INSERT OR UPDATE OF precio_base_actual, precio_venta_actual
ON productos
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_historial_precios();


-- =========================================================
-- 27. GENERAR NUMERO AUTOMATICO DE COTIZACION
-- Ejemplo: COT-2026-000001
-- =========================================================

CREATE OR REPLACE FUNCTION fn_preparar_cotizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF TG_OP = 'INSERT' THEN

        IF NEW.numero_cotizacion IS NULL
           OR BTRIM(NEW.numero_cotizacion) = '' THEN

            NEW.numero_cotizacion :=
                'COT-' ||
                TO_CHAR(CURRENT_DATE, 'YYYY') ||
                '-' ||
                LPAD(
                    NEXTVAL('secuencia_cotizaciones')::TEXT,
                    6,
                    '0'
                );

        END IF;

    END IF;


    IF TG_OP = 'UPDATE' THEN

        IF NEW.estado = 'APROBADA'
           AND OLD.estado IS DISTINCT FROM 'APROBADA' THEN

            NEW.aprobada_en = NOW();

        END IF;

    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_preparar_cotizacion
BEFORE INSERT OR UPDATE ON cotizaciones
FOR EACH ROW
EXECUTE FUNCTION fn_preparar_cotizacion();


-- =========================================================
-- 28. RECALCULAR TOTAL AUTOMATICAMENTE
-- =========================================================

CREATE OR REPLACE FUNCTION fn_recalcular_total_cotizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_cotizacion BIGINT;
BEGIN

    IF TG_OP = 'DELETE' THEN
        v_id_cotizacion := OLD.id_cotizacion;
    ELSE
        v_id_cotizacion := NEW.id_cotizacion;
    END IF;

    UPDATE cotizaciones
    SET
        subtotal = COALESCE(
            (
                SELECT SUM(subtotal)
                FROM detalle_cotizaciones
                WHERE id_cotizacion = v_id_cotizacion
            ),
            0
        ),
        total = COALESCE(
            (
                SELECT SUM(subtotal)
                FROM detalle_cotizaciones
                WHERE id_cotizacion = v_id_cotizacion
            ),
            0
        )
    WHERE id_cotizacion = v_id_cotizacion;

    RETURN NULL;
END;
$$;


CREATE TRIGGER trg_recalcular_total_cotizacion
AFTER INSERT OR UPDATE OR DELETE
ON detalle_cotizaciones
FOR EACH ROW
EXECUTE FUNCTION fn_recalcular_total_cotizacion();


-- =========================================================
-- 29. HISTORIAL AUTOMATICO DE ESTADOS
-- =========================================================

CREATE OR REPLACE FUNCTION fn_registrar_estado_cotizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF TG_OP = 'INSERT' THEN

        INSERT INTO historial_estados_cotizacion (
            id_cotizacion,
            estado_anterior,
            estado_nuevo,
            cambiado_por
        )
        VALUES (
            NEW.id_cotizacion,
            NULL,
            NEW.estado,
            COALESCE(NEW.actualizado_por, NEW.id_vendedor)
        );

    ELSIF OLD.estado IS DISTINCT FROM NEW.estado THEN

        INSERT INTO historial_estados_cotizacion (
            id_cotizacion,
            estado_anterior,
            estado_nuevo,
            cambiado_por
        )
        VALUES (
            NEW.id_cotizacion,
            OLD.estado,
            NEW.estado,
            COALESCE(NEW.actualizado_por, NEW.id_vendedor)
        );

    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_historial_estado_cotizacion
AFTER INSERT OR UPDATE OF estado
ON cotizaciones
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_estado_cotizacion();


-- =========================================================
-- 30. MARCAR COTIZACIONES VENCIDAS
-- Esta funcion puede ejecutarse al abrir el dashboard,
-- antes de listar cotizaciones o mediante tarea programada.
-- =========================================================

CREATE OR REPLACE FUNCTION marcar_cotizaciones_vencidas()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cantidad INTEGER;
BEGIN

    UPDATE cotizaciones
    SET estado = 'VENCIDA'
    WHERE fecha_vigencia < CURRENT_DATE
      AND estado IN (
          'EMITIDA',
          'ENVIADA',
          'APROBADA'
      );

    GET DIAGNOSTICS v_cantidad = ROW_COUNT;

    RETURN v_cantidad;
END;
$$;


-- =========================================================
-- 31. VALIDAR Y CREAR VENTA DESDE COTIZACION
--
-- REGLAS:
-- - Debe estar APROBADA
-- - No debe estar vencida
-- - Solo puede existir una venta por cotizacion
-- - Los importes se copian de la cotizacion
-- =========================================================

CREATE OR REPLACE FUNCTION fn_validar_venta_desde_cotizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cotizacion cotizaciones%ROWTYPE;
BEGIN

    SELECT *
    INTO v_cotizacion
    FROM cotizaciones
    WHERE id_cotizacion = NEW.id_cotizacion
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'La cotizacion % no existe',
            NEW.id_cotizacion;
    END IF;


    IF v_cotizacion.estado <> 'APROBADA' THEN
        RAISE EXCEPTION
            'La cotizacion debe estar APROBADA para convertirse en venta';
    END IF;


    IF v_cotizacion.fecha_vigencia < CURRENT_DATE THEN
        RAISE EXCEPTION
            'La cotizacion esta vencida y no puede convertirse en venta';
    END IF;


    IF EXISTS (
        SELECT 1
        FROM ventas
        WHERE id_cotizacion = NEW.id_cotizacion
    ) THEN
        RAISE EXCEPTION
            'La cotizacion ya fue convertida en venta';
    END IF;


    IF NEW.numero_venta IS NULL
       OR BTRIM(NEW.numero_venta) = '' THEN

        NEW.numero_venta :=
            'VTA-' ||
            TO_CHAR(CURRENT_DATE, 'YYYY') ||
            '-' ||
            LPAD(
                NEXTVAL('secuencia_ventas')::TEXT,
                6,
                '0'
            );

    END IF;


    NEW.id_cliente :=
        v_cotizacion.id_cliente;

    NEW.id_vendedor :=
        v_cotizacion.id_vendedor;

    NEW.moneda :=
        v_cotizacion.moneda;

    NEW.tipo_cambio_soles_por_dolar :=
        v_cotizacion.tipo_cambio_soles_por_dolar;

    NEW.subtotal :=
        v_cotizacion.subtotal;

    NEW.total :=
        v_cotizacion.total;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validar_venta_cotizacion
BEFORE INSERT ON ventas
FOR EACH ROW
EXECUTE FUNCTION fn_validar_venta_desde_cotizacion();


-- =========================================================
-- 32. COPIAR DETALLE DE COTIZACION A VENTA
-- Y CAMBIAR ESTADO DE LA COTIZACION
-- =========================================================

CREATE OR REPLACE FUNCTION fn_finalizar_conversion_venta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    INSERT INTO detalle_ventas (
        id_venta,
        id_producto,
        codigo_producto,
        nombre_producto,
        cantidad,
        precio_unitario
    )
    SELECT
        NEW.id_venta,
        dc.id_producto,
        dc.codigo_producto,
        dc.nombre_producto,
        dc.cantidad,
        dc.precio_unitario
    FROM detalle_cotizaciones dc
    WHERE dc.id_cotizacion = NEW.id_cotizacion;


    UPDATE cotizaciones
    SET
        estado = 'CONVERTIDA_VENTA',
        actualizado_por = NEW.id_vendedor
    WHERE id_cotizacion = NEW.id_cotizacion;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_finalizar_conversion_venta
AFTER INSERT ON ventas
FOR EACH ROW
EXECUTE FUNCTION fn_finalizar_conversion_venta();


-- =========================================================
-- 33. PREPARAR BOLETA DESDE LA VENTA
-- =========================================================

CREATE OR REPLACE FUNCTION fn_preparar_boleta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_venta ventas%ROWTYPE;
    v_cliente clientes%ROWTYPE;
BEGIN

    SELECT *
    INTO v_venta
    FROM ventas
    WHERE id_venta = NEW.id_venta;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La venta indicada no existe';
    END IF;


    SELECT *
    INTO v_cliente
    FROM clientes
    WHERE id_cliente = v_venta.id_cliente;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El cliente de la venta no existe';
    END IF;


    NEW.moneda := v_venta.moneda;
    NEW.total := v_venta.total;

    NEW.cliente_tipo_documento :=
        v_cliente.tipo_documento;

    NEW.cliente_numero_documento :=
        v_cliente.numero_documento;

    NEW.cliente_nombre :=
        COALESCE(
            v_cliente.razon_social,
            BTRIM(
                COALESCE(v_cliente.nombres, '') ||
                ' ' ||
                COALESCE(v_cliente.apellidos, '')
            )
        );

    NEW.cliente_direccion :=
        v_cliente.direccion;

    NEW.cliente_correo :=
        v_cliente.correo;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_preparar_boleta
BEFORE INSERT ON boletas
FOR EACH ROW
EXECUTE FUNCTION fn_preparar_boleta();


-- =========================================================
-- 34. CUANDO NUBEFACT GENERA LA BOLETA,
-- MARCAR LA VENTA COMO FACTURADA
-- =========================================================

CREATE OR REPLACE FUNCTION fn_sincronizar_venta_boleta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.estado = 'GENERADA'
       AND (
            TG_OP = 'INSERT'
            OR OLD.estado IS DISTINCT FROM 'GENERADA'
       ) THEN

        UPDATE ventas
        SET estado = 'FACTURADA'
        WHERE id_venta = NEW.id_venta;

    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_sincronizar_venta_boleta
AFTER INSERT OR UPDATE OF estado
ON boletas
FOR EACH ROW
EXECUTE FUNCTION fn_sincronizar_venta_boleta();


-- =========================================================
-- 35. VISTA DEL CATALOGO PARA EL VENDEDOR
-- Solo productos activos con precio de venta establecido.
-- =========================================================

CREATE VIEW vista_catalogo_productos AS
SELECT
    p.id_producto,
    p.codigo_producto,
    p.nombre,
    p.descripcion,
    p.categoria,
    p.marca,
    p.modelo,
    p.unidad_medida,

    p.precio_venta_actual,
    p.moneda_precio,

    pr.id_proveedor,
    pr.razon_social AS proveedor,

    ip.url_imagen,
    ip.url_visualizacion

FROM productos p

INNER JOIN proveedores pr
    ON pr.id_proveedor = p.id_proveedor

LEFT JOIN imagenes_productos ip
    ON ip.id_producto = p.id_producto
   AND ip.es_principal = TRUE
   AND ip.activa = TRUE

WHERE
    p.activo = TRUE
    AND pr.activo = TRUE
    AND p.precio_venta_actual IS NOT NULL;


-- =========================================================
-- 36. VISTA DE HISTORIAL DEL VENDEDOR
-- Cotizaciones + ventas + boletas
-- =========================================================

CREATE VIEW vista_historial_operaciones_vendedor AS

SELECT
    c.id_vendedor,

    'COTIZACION'::VARCHAR AS tipo_operacion,

    c.id_cotizacion AS id_operacion,

    c.numero_cotizacion AS numero_operacion,

    c.creado_en AS fecha_operacion,

    c.id_cliente,

    COALESCE(
        cl.razon_social,
        BTRIM(
            COALESCE(cl.nombres, '') ||
            ' ' ||
            COALESCE(cl.apellidos, '')
        )
    ) AS cliente,

    c.estado::TEXT AS estado,

    c.moneda::TEXT AS moneda,

    c.total,

    c.pdf_url AS url_documento

FROM cotizaciones c

INNER JOIN clientes cl
    ON cl.id_cliente = c.id_cliente


UNION ALL


SELECT
    v.id_vendedor,

    'VENTA'::VARCHAR AS tipo_operacion,

    v.id_venta AS id_operacion,

    v.numero_venta AS numero_operacion,

    v.creado_en AS fecha_operacion,

    v.id_cliente,

    COALESCE(
        cl.razon_social,
        BTRIM(
            COALESCE(cl.nombres, '') ||
            ' ' ||
            COALESCE(cl.apellidos, '')
        )
    ) AS cliente,

    v.estado::TEXT AS estado,

    v.moneda::TEXT AS moneda,

    v.total,

    NULL::TEXT AS url_documento

FROM ventas v

INNER JOIN clientes cl
    ON cl.id_cliente = v.id_cliente


UNION ALL


SELECT
    v.id_vendedor,

    'BOLETA'::VARCHAR AS tipo_operacion,

    b.id_boleta AS id_operacion,

    COALESCE(
        b.serie || '-' || b.numero,
        'BOLETA-' || b.id_boleta::TEXT
    ) AS numero_operacion,

    b.creada_en AS fecha_operacion,

    v.id_cliente,

    b.cliente_nombre AS cliente,

    b.estado::TEXT AS estado,

    b.moneda::TEXT AS moneda,

    b.total,

    b.enlace_pdf AS url_documento

FROM boletas b

INNER JOIN ventas v
    ON v.id_venta = b.id_venta;


-- =========================================================
-- 37. CARGA INICIAL DE ROLES
-- =========================================================

INSERT INTO roles (
    codigo,
    nombre,
    descripcion
)
VALUES
(
    'ADMINISTRADOR',
    'Administrador',
    'Gestion general del sistema'
),
(
    'AREA_COMERCIAL',
    'Area Comercial',
    'Gestion de proveedores, productos y precios'
),
(
    'VENDEDOR',
    'Vendedor',
    'Gestion de clientes, cotizaciones, ventas y boletas'
);


-- =========================================================
-- 38. CARGA INICIAL DE PERMISOS
-- =========================================================

INSERT INTO permisos (codigo, nombre) VALUES

('USUARIOS_GESTIONAR',
 'Gestionar usuarios'),

('PROVEEDORES_CONSULTAR',
 'Consultar proveedores'),

('PROVEEDORES_GESTIONAR',
 'Gestionar proveedores'),

('CLIENTES_CONSULTAR',
 'Consultar clientes'),

('CLIENTES_GESTIONAR',
 'Gestionar clientes'),

('CLIENTES_EDITAR_CONTACTO',
 'Editar datos de contacto de clientes'),

('PRODUCTOS_CONSULTAR',
 'Consultar productos'),

('PRODUCTOS_GESTIONAR',
 'Gestionar productos'),

('PRODUCTOS_IMPORTAR',
 'Importar productos desde Excel'),

('PRECIOS_VENTA_GESTIONAR',
 'Gestionar precios de venta'),

('COTIZACIONES_CREAR',
 'Crear cotizaciones'),

('COTIZACIONES_CONSULTAR_PROPIAS',
 'Consultar cotizaciones propias'),

('COTIZACIONES_CONSULTAR_TODAS',
 'Consultar todas las cotizaciones'),

('BOLETAS_GENERAR',
 'Generar boletas'),

('BOLETAS_CONSULTAR_PROPIAS',
 'Consultar boletas propias'),

('BOLETAS_CONSULTAR_TODAS',
 'Consultar todas las boletas'),

('HISTORIAL_CONSULTAR',
 'Consultar historial de operaciones');


-- =========================================================
-- 39. PERMISOS DEL ADMINISTRADOR
-- =========================================================

INSERT INTO roles_permisos (
    id_rol,
    id_permiso
)
SELECT
    r.id_rol,
    p.id_permiso
FROM roles r
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR'
AND p.codigo IN (
    'USUARIOS_GESTIONAR',

    'PROVEEDORES_CONSULTAR',
    'PROVEEDORES_GESTIONAR',

    'CLIENTES_CONSULTAR',
    'CLIENTES_GESTIONAR',

    'PRODUCTOS_CONSULTAR',
    'PRODUCTOS_GESTIONAR',

    'PRECIOS_VENTA_GESTIONAR',

    'COTIZACIONES_CONSULTAR_TODAS',

    'BOLETAS_CONSULTAR_TODAS'
);


-- =========================================================
-- 40. PERMISOS DEL AREA COMERCIAL
-- =========================================================

INSERT INTO roles_permisos (
    id_rol,
    id_permiso
)
SELECT
    r.id_rol,
    p.id_permiso
FROM roles r
CROSS JOIN permisos p
WHERE r.codigo = 'AREA_COMERCIAL'
AND p.codigo IN (
    'PROVEEDORES_CONSULTAR',
    'PROVEEDORES_GESTIONAR',

    'PRODUCTOS_CONSULTAR',
    'PRODUCTOS_GESTIONAR',
    'PRODUCTOS_IMPORTAR',

    'PRECIOS_VENTA_GESTIONAR'
);


-- =========================================================
-- 41. PERMISOS DEL VENDEDOR
-- =========================================================

INSERT INTO roles_permisos (
    id_rol,
    id_permiso
)
SELECT
    r.id_rol,
    p.id_permiso
FROM roles r
CROSS JOIN permisos p
WHERE r.codigo = 'VENDEDOR'
AND p.codigo IN (
    'CLIENTES_CONSULTAR',
    'CLIENTES_GESTIONAR',
    'CLIENTES_EDITAR_CONTACTO',

    'PRODUCTOS_CONSULTAR',

    'COTIZACIONES_CREAR',
    'COTIZACIONES_CONSULTAR_PROPIAS',

    'BOLETAS_GENERAR',
    'BOLETAS_CONSULTAR_PROPIAS',

    'HISTORIAL_CONSULTAR'
);


-- =========================================================
-- 42. INDICES ADICIONALES
-- =========================================================

CREATE INDEX idx_usuarios_rol
    ON usuarios(id_rol);

CREATE INDEX idx_usuarios_activo
    ON usuarios(activo);

CREATE INDEX idx_proveedores_activo
    ON proveedores(activo);

CREATE INDEX idx_cotizaciones_fecha
    ON cotizaciones(fecha_emision DESC);

CREATE INDEX idx_ventas_fecha
    ON ventas(fecha_venta DESC);

CREATE INDEX idx_boletas_venta
    ON boletas(id_venta);
