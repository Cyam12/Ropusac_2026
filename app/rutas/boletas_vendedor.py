import json

from datetime import date

from decimal import Decimal

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import current_user

from sqlalchemy import text

from app.extensiones import db

from app.servicios.correo import (
    ErrorCorreo,
    enviar_correo
)

from app.servicios.nubefact import (
    ErrorNubeFact,
    construir_payload_boleta,
    consultar_boleta,
    descargar_pdf,
    generar_boleta,
    obtener_serie_boleta
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "boletas_vendedor",
    __name__,
    url_prefix="/vendedor/boletas"
)


# =========================================================
# CONFIGURACION
# =========================================================

COTIZACIONES_POR_PAGINA = 20


# =========================================================
# MARCAR COTIZACIONES VENCIDAS
# =========================================================

def marcar_vencidas():

    try:

        db.session.execute(
            text(
                """
                SELECT marcar_cotizaciones_vencidas()
                """
            )
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR MARCANDO VENCIDAS:",
            error
        )


# =========================================================
# REGISTRAR API
# =========================================================

def registrar_api(
    servicio,
    operacion,
    exitoso,
    id_entidad=None,
    codigo_http=None,
    identificador=None,
    mensaje=None,
    respuesta=None
):

    respuesta_json = (
        json.dumps(
            respuesta,
            ensure_ascii=False,
            default=str
        )
        if respuesta is not None
        else None
    )

    db.session.execute(
        text(
            """
            INSERT INTO registros_api (
                servicio,
                operacion,
                id_usuario,
                entidad_relacionada,
                id_entidad_relacionada,
                codigo_http,
                exitoso,
                identificador_externo,
                mensaje,
                respuesta_resumida
            )
            VALUES (
                CAST(:servicio AS servicio_api_enum),
                :operacion,
                :id_usuario,
                :entidad,
                :id_entidad,
                :codigo_http,
                :exitoso,
                :identificador,
                :mensaje,
                CAST(:respuesta AS JSONB)
            )
            """
        ),

        {
            "servicio":
                servicio,

            "operacion":
                operacion,

            "id_usuario":
                current_user.id_usuario,

            "entidad":
                (
                    "boletas"
                    if servicio == "NUBEFACT"
                    else "envios_correo"
                ),

            "id_entidad":
                id_entidad,

            "codigo_http":
                codigo_http,

            "exitoso":
                exitoso,

            "identificador":
                identificador,

            "mensaje":
                mensaje,

            "respuesta":
                respuesta_json
        }
    )


# =========================================================
# BITACORA
# =========================================================

def registrar_bitacora(
    accion,
    entidad,
    id_entidad,
    descripcion,
    datos=None
):

    datos_json = (
        json.dumps(
            datos,
            ensure_ascii=False,
            default=str
        )
        if datos is not None
        else None
    )

    db.session.execute(
        text(
            """
            INSERT INTO bitacora_operaciones (
                id_usuario,
                accion,
                modulo,
                entidad,
                id_entidad,
                descripcion,
                datos_adicionales,
                direccion_ip
            )
            VALUES (
                :id_usuario,
                :accion,
                'BOLETAS',
                :entidad,
                :id_entidad,
                :descripcion,
                CAST(:datos AS JSONB),
                :direccion_ip
            )
            """
        ),

        {
            "id_usuario":
                current_user.id_usuario,

            "accion":
                accion,

            "entidad":
                entidad,

            "id_entidad":
                id_entidad,

            "descripcion":
                descripcion,

            "datos":
                datos_json,

            "direccion_ip":
                request.remote_addr
        }
    )


# =========================================================
# LISTAR
#
# OPTIMIZADO:
#
# - MAXIMO 20 COTIZACIONES POR PAGINA
# - SOLO COLUMNAS UTILIZADAS POR EL TEMPLATE
# - 21 FILAS PARA DETECTAR PAGINA SIGUIENTE
# - ORDEN POR PRIMARY KEY
# =========================================================

@bp.get("/")
@rol_requerido(
    "VENDEDOR"
)
def lista():

    marcar_vencidas()

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    estado = request.args.get(
        "estado",
        ""
    ).strip()

    pagina = request.args.get(
        "pagina",
        1,
        type=int
    )

    if pagina < 1:

        pagina = 1

    parametros = {}

    consulta = """
        SELECT
            c.id_cotizacion,
            c.numero_cotizacion,
            c.fecha_emision,
            c.fecha_vigencia,
            c.estado::TEXT AS estado_cotizacion,
            c.moneda::TEXT AS moneda,
            c.total,

            COALESCE(
                cl.razon_social,
                BTRIM(
                    COALESCE(cl.nombres, '')
                    || ' ' ||
                    COALESCE(cl.apellidos, '')
                )
            ) AS cliente,

            cl.numero_documento,

            u.id_usuario AS id_vendedor,

            BTRIM(
                COALESCE(u.nombres, '')
                || ' ' ||
                COALESCE(u.apellidos, '')
            ) AS vendedor,

            v.id_venta,

            b.id_boleta,
            b.estado::TEXT AS estado_boleta,
            b.serie,
            b.numero AS numero_boleta,

            CASE
                WHEN c.fecha_vigencia >= CURRENT_DATE
                    THEN TRUE
                ELSE FALSE
            END AS vigente

        FROM cotizaciones c

        INNER JOIN clientes cl
            ON cl.id_cliente =
               c.id_cliente

        INNER JOIN usuarios u
            ON u.id_usuario =
               c.id_vendedor

        LEFT JOIN ventas v
            ON v.id_cotizacion =
               c.id_cotizacion

        LEFT JOIN boletas b
            ON b.id_venta =
               v.id_venta

        WHERE 1 = 1
    """

    # =====================================================
    # BUSCAR
    # =====================================================

    if buscar:

        consulta += """
            AND (
                c.numero_cotizacion ILIKE :buscar
                OR cl.numero_documento ILIKE :buscar
                OR cl.razon_social ILIKE :buscar
                OR cl.nombres ILIKE :buscar
                OR cl.apellidos ILIKE :buscar
                OR u.nombres ILIKE :buscar
                OR u.apellidos ILIKE :buscar
                OR v.numero_venta ILIKE :buscar
                OR b.numero ILIKE :buscar
            )
        """

        parametros[
            "buscar"
        ] = (
            f"%{buscar}%"
        )

    # =====================================================
    # ESTADO
    # =====================================================

    if estado:

        consulta += """
            AND c.estado::TEXT = :estado
        """

        parametros[
            "estado"
        ] = estado

    # =====================================================
    # PAGINACION
    #
    # 20 VISIBLES
    # + 1 PARA SABER SI HAY SIGUIENTE PAGINA
    # =====================================================

    offset = (
        pagina - 1
    ) * COTIZACIONES_POR_PAGINA

    parametros[
        "limite"
    ] = (
        COTIZACIONES_POR_PAGINA
        + 1
    )

    parametros[
        "offset"
    ] = offset

    consulta += """
        ORDER BY
            c.id_cotizacion DESC

        LIMIT :limite
        OFFSET :offset
    """

    filas = (
        db.session.execute(
            text(
                consulta
            ),
            parametros
        )
        .mappings()
        .all()
    )

    # =====================================================
    # PAGINACION
    # =====================================================

    hay_siguiente = (
        len(
            filas
        )
        >
        COTIZACIONES_POR_PAGINA
    )

    cotizaciones = filas[
        :COTIZACIONES_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not cotizaciones
    ):

        return redirect(
            url_for(
                "boletas_vendedor.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar,

                estado=estado
            )
        )

    estados = [
        "EMITIDA",
        "ENVIADA",
        "APROBADA",
        "VENCIDA",
        "CONVERTIDA_VENTA",
        "RECHAZADA",
        "ANULADA"
    ]

    return render_template(
        "vendedor/boletas/lista.html",

        cotizaciones=(
            cotizaciones
        ),

        buscar=buscar,

        estado=estado,

        estados=estados,

        pagina=pagina,

        hay_anterior=(
            hay_anterior
        ),

        hay_siguiente=(
            hay_siguiente
        ),

        por_pagina=(
            COTIZACIONES_POR_PAGINA
        )
    )


# =========================================================
# APROBAR COTIZACION
#
# PASOS:
#
# 1. BLOQUEAR COTIZACION
# 2. VALIDAR VIGENCIA
# 3. BLOQUEAR PRODUCTOS
# 4. VALIDAR STOCK REAL
# 5. APROBAR COTIZACION
# 6. CREAR VENTA
# 7. DESCONTAR STOCK
#
# TODO EN UNA SOLA TRANSACCION.
# =========================================================

@bp.post(
    "/cotizacion/<int:id_cotizacion>/aprobar"
)
@rol_requerido(
    "VENDEDOR"
)
def aprobar_cotizacion(
    id_cotizacion
):

    marcar_vencidas()

    try:

        # =================================================
        # BLOQUEAR COTIZACION
        # =================================================

        cotizacion = (
            db.session.execute(
                text(
                    """
                    SELECT
                        id_cotizacion,
                        numero_cotizacion,
                        id_cliente,
                        id_vendedor,
                        fecha_vigencia,
                        estado::TEXT AS estado,
                        moneda::TEXT AS moneda,
                        tipo_cambio_soles_por_dolar,
                        subtotal,
                        total

                    FROM cotizaciones

                    WHERE id_cotizacion =
                        :id_cotizacion

                    FOR UPDATE
                    """
                ),

                {
                    "id_cotizacion":
                        id_cotizacion
                }
            )
            .mappings()
            .first()
        )

        if cotizacion is None:

            db.session.rollback()

            abort(
                404
            )

        # =================================================
        # YA EXISTE VENTA
        # =================================================

        venta_existente = (
            db.session.execute(
                text(
                    """
                    SELECT
                        id_venta

                    FROM ventas

                    WHERE id_cotizacion =
                        :id_cotizacion
                    """
                ),

                {
                    "id_cotizacion":
                        id_cotizacion
                }
            )
            .scalar_one_or_none()
        )

        if venta_existente:

            db.session.commit()

            return redirect(
                url_for(
                    "boletas_vendedor.generar_desde_venta",

                    id_venta=(
                        venta_existente
                    )
                )
            )

        # =================================================
        # VIGENCIA
        # =================================================

        if (
            cotizacion[
                "fecha_vigencia"
            ]
            <
            date.today()
        ):

            db.session.execute(
                text(
                    """
                    UPDATE cotizaciones

                    SET
                        estado = 'VENCIDA',
                        actualizado_por = :usuario

                    WHERE id_cotizacion =
                        :id_cotizacion
                    """
                ),

                {
                    "usuario":
                        current_user.id_usuario,

                    "id_cotizacion":
                        id_cotizacion
                }
            )

            db.session.commit()

            flash(
                (
                    "La cotización ya venció "
                    "y no puede aprobarse."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "boletas_vendedor.lista"
                )
            )

        # =================================================
        # ESTADO PERMITIDO
        # =================================================

        if (
            cotizacion[
                "estado"
            ]
            not in (
                "EMITIDA",
                "ENVIADA",
                "APROBADA"
            )
        ):

            db.session.rollback()

            flash(
                (
                    "La cotización no se encuentra "
                    "en un estado válido para "
                    "convertirse en venta."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "boletas_vendedor.lista"
                )
            )

        # =================================================
        # BLOQUEAR PRODUCTOS
        # =================================================

        productos = (
            db.session.execute(
                text(
                    """
                    SELECT
                        dc.id_producto,
                        dc.codigo_producto,
                        dc.nombre_producto,
                        dc.cantidad,

                        p.stock_disponible,
                        p.activo

                    FROM detalle_cotizaciones dc

                    INNER JOIN productos p
                        ON p.id_producto =
                           dc.id_producto

                    WHERE dc.id_cotizacion =
                        :id_cotizacion

                    ORDER BY p.id_producto

                    FOR UPDATE OF p
                    """
                ),

                {
                    "id_cotizacion":
                        id_cotizacion
                }
            )
            .mappings()
            .all()
        )

        if not productos:

            db.session.rollback()

            flash(
                (
                    "La cotización no contiene "
                    "productos."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "boletas_vendedor.lista"
                )
            )

        # =================================================
        # VALIDAR STOCK
        # =================================================

        for producto in productos:

            if not producto[
                "activo"
            ]:

                db.session.rollback()

                flash(
                    (
                        f"El producto "
                        f"{producto['nombre_producto']} "
                        "se encuentra inactivo."
                    ),
                    "danger"
                )

                return redirect(
                    url_for(
                        "boletas_vendedor.lista"
                    )
                )

            stock = Decimal(
                producto[
                    "stock_disponible"
                ]
                or 0
            )

            cantidad = Decimal(
                producto[
                    "cantidad"
                ]
            )

            if stock < cantidad:

                db.session.rollback()

                flash(
                    (
                        f"Stock insuficiente para "
                        f"{producto['nombre_producto']}. "
                        f"Disponible: {stock}. "
                        f"Solicitado: {cantidad}."
                    ),
                    "danger"
                )

                return redirect(
                    url_for(
                        "boletas_vendedor.lista"
                    )
                )

        # =================================================
        # APROBAR
        # =================================================

        if (
            cotizacion[
                "estado"
            ]
            != "APROBADA"
        ):

            db.session.execute(
                text(
                    """
                    UPDATE cotizaciones

                    SET
                        estado = 'APROBADA',
                        actualizado_por = :usuario

                    WHERE id_cotizacion =
                        :id_cotizacion
                    """
                ),

                {
                    "usuario":
                        current_user.id_usuario,

                    "id_cotizacion":
                        id_cotizacion
                }
            )

        # =================================================
        # CREAR VENTA
        # =================================================

        id_venta = (
            db.session.execute(
                text(
                    """
                    INSERT INTO ventas (
                        numero_venta,
                        id_cotizacion,
                        id_cliente,
                        id_vendedor,
                        moneda,
                        tipo_cambio_soles_por_dolar,
                        subtotal,
                        total
                    )
                    VALUES (
                        '',
                        :id_cotizacion,
                        :id_cliente,
                        :id_vendedor,
                        CAST(:moneda AS moneda_enum),
                        :tipo_cambio,
                        :subtotal,
                        :total
                    )
                    RETURNING id_venta
                    """
                ),

                {
                    "id_cotizacion":
                        cotizacion[
                            "id_cotizacion"
                        ],

                    "id_cliente":
                        cotizacion[
                            "id_cliente"
                        ],

                    "id_vendedor":
                        cotizacion[
                            "id_vendedor"
                        ],

                    "moneda":
                        cotizacion[
                            "moneda"
                        ],

                    "tipo_cambio":
                        cotizacion[
                            "tipo_cambio_soles_por_dolar"
                        ],

                    "subtotal":
                        cotizacion[
                            "subtotal"
                        ],

                    "total":
                        cotizacion[
                            "total"
                        ]
                }
            )
            .scalar_one()
        )

        # =================================================
        # DESCONTAR STOCK
        # =================================================

        for producto in productos:

            resultado = (
                db.session.execute(
                    text(
                        """
                        UPDATE productos

                        SET
                            stock_disponible =
                                stock_disponible
                                -
                                :cantidad,

                            actualizado_por =
                                :usuario

                        WHERE id_producto =
                            :id_producto

                          AND stock_disponible >=
                            :cantidad
                        """
                    ),

                    {
                        "cantidad":
                            producto[
                                "cantidad"
                            ],

                        "usuario":
                            current_user.id_usuario,

                        "id_producto":
                            producto[
                                "id_producto"
                            ]
                    }
                )
            )

            if (
                resultado.rowcount
                != 1
            ):

                raise RuntimeError(
                    (
                        "El stock cambió durante "
                        "la aprobación de la venta."
                    )
                )

        # =================================================
        # BITACORA
        # =================================================

        registrar_bitacora(
            accion=(
                "APROBAR_COTIZACION"
            ),

            entidad=(
                "cotizaciones"
            ),

            id_entidad=(
                id_cotizacion
            ),

            descripcion=(
                "Cotización aprobada y convertida "
                "en venta. Se descontó el stock."
            ),

            datos={
                "id_venta":
                    id_venta,

                "vendedor_que_aprobo":
                    current_user.id_usuario
            }
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR APROBANDO COTIZACION:",
            error
        )

        flash(
            (
                "No se pudo aprobar la cotización "
                "ni convertirla en venta."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "boletas_vendedor.lista"
            )
        )

    return redirect(
        url_for(
            "boletas_vendedor.generar_desde_venta",

            id_venta=(
                id_venta
            )
        )
    )


# =========================================================
# CREAR / OBTENER REGISTRO DE BOLETA
# =========================================================

def asegurar_boleta(
    id_venta
):

    existente = (
        db.session.execute(
            text(
                """
                SELECT
                    id_boleta

                FROM boletas

                WHERE id_venta =
                    :id_venta
                """
            ),

            {
                "id_venta":
                    id_venta
            }
        )
        .scalar_one_or_none()
    )

    if existente:

        return existente

    serie = (
        obtener_serie_boleta()
    )

    id_boleta = (
        db.session.execute(
            text(
                """
                INSERT INTO boletas (
                    id_venta
                )
                VALUES (
                    :id_venta
                )
                RETURNING id_boleta
                """
            ),

            {
                "id_venta":
                    id_venta
            }
        )
        .scalar_one()
    )

    db.session.execute(
        text(
            """
            UPDATE boletas

            SET
                serie = :serie,

                numero =
                    CAST(
                        id_boleta AS TEXT
                    ),

                fecha_emision =
                    CURRENT_DATE

            WHERE id_boleta =
                :id_boleta
            """
        ),

        {
            "serie":
                serie,

            "id_boleta":
                id_boleta
        }
    )

    db.session.commit()

    return id_boleta


# =========================================================
# OBTENER DATOS PARA NUBEFACT
# =========================================================

def obtener_datos_nubefact(
    id_boleta
):

    cabecera = (
        db.session.execute(
            text(
                """
                SELECT
                    b.id_boleta,
                    b.id_venta,
                    b.estado::TEXT AS estado,
                    b.serie,
                    b.numero,
                    b.fecha_emision,
                    b.moneda::TEXT AS moneda,
                    b.total,

                    b.cliente_tipo_documento::TEXT
                        AS cliente_tipo_documento,

                    b.cliente_numero_documento,
                    b.cliente_nombre,
                    b.cliente_direccion,
                    b.cliente_correo,

                    v.numero_venta,
                    v.id_cotizacion,
                    v.tipo_cambio_soles_por_dolar,
                    v.subtotal AS venta_subtotal,
                    v.total AS venta_total,
                    v.moneda::TEXT AS venta_moneda,

                    c.numero_cotizacion

                FROM boletas b

                INNER JOIN ventas v
                    ON v.id_venta = b.id_venta

                INNER JOIN cotizaciones c
                    ON c.id_cotizacion =
                       v.id_cotizacion

                WHERE b.id_boleta =
                    :id_boleta
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .mappings()
        .first()
    )

    if cabecera is None:

        return None

    detalles = (
        db.session.execute(
            text(
                """
                SELECT
                    dv.id_producto,
                    dv.codigo_producto,
                    dv.nombre_producto,
                    dv.cantidad,
                    dv.precio_unitario,
                    dv.subtotal,

                    p.unidad_medida

                FROM detalle_ventas dv

                INNER JOIN productos p
                    ON p.id_producto =
                       dv.id_producto

                WHERE dv.id_venta =
                    :id_venta

                ORDER BY
                    dv.id_detalle_venta
                """
            ),

            {
                "id_venta":
                    cabecera[
                        "id_venta"
                    ]
            }
        )
        .mappings()
        .all()
    )

    boleta = {
        "id_boleta":
            cabecera[
                "id_boleta"
            ],

        "serie":
            cabecera[
                "serie"
            ],

        "numero":
            cabecera[
                "numero"
            ],

        "fecha_emision":
            cabecera[
                "fecha_emision"
            ],

        "cliente_tipo_documento":
            cabecera[
                "cliente_tipo_documento"
            ],

        "cliente_numero_documento":
            cabecera[
                "cliente_numero_documento"
            ],

        "cliente_nombre":
            cabecera[
                "cliente_nombre"
            ],

        "cliente_direccion":
            cabecera[
                "cliente_direccion"
            ],

        "cliente_correo":
            cabecera[
                "cliente_correo"
            ]
    }

    venta = {
        "id_venta":
            cabecera[
                "id_venta"
            ],

        "numero_venta":
            cabecera[
                "numero_venta"
            ],

        "moneda":
            cabecera[
                "venta_moneda"
            ],

        "tipo_cambio_soles_por_dolar":
            cabecera[
                "tipo_cambio_soles_por_dolar"
            ],

        "subtotal":
            cabecera[
                "venta_subtotal"
            ],

        "total":
            cabecera[
                "venta_total"
            ]
    }

    cotizacion = {
        "id_cotizacion":
            cabecera[
                "id_cotizacion"
            ],

        "numero_cotizacion":
            cabecera[
                "numero_cotizacion"
            ]
    }

    return {
        "boleta":
            boleta,

        "venta":
            venta,

        "cotizacion":
            cotizacion,

        "detalles":
            detalles
    }


# =========================================================
# GUARDAR RESPUESTA CORRECTA NUBEFACT
# =========================================================

def guardar_boleta_generada(
    id_boleta,
    resultado
):

    respuesta_json = (
        json.dumps(
            resultado[
                "raw"
            ],
            ensure_ascii=False,
            default=str
        )
    )

    db.session.execute(
        text(
            """
            UPDATE boletas

            SET
                estado = 'GENERADA',

                serie =
                    COALESCE(
                        :serie,
                        serie
                    ),

                numero =
                    COALESCE(
                        CAST(
                            :numero AS TEXT
                        ),
                        numero
                    ),

                identificador_nubefact =
                    :identificador,

                enlace_pdf =
                    :enlace_pdf,

                enlace_xml =
                    :enlace_xml,

                enlace_cdr =
                    :enlace_cdr,

                codigo_hash =
                    :codigo_hash,

                cadena_codigo_qr =
                    :cadena_qr,

                respuesta_nubefact =
                    CAST(
                        :respuesta AS JSONB
                    ),

                mensaje_nubefact =
                    :mensaje,

                generada_en =
                    NOW()

            WHERE id_boleta =
                :id_boleta
            """
        ),

        {
            "serie":
                resultado[
                    "serie"
                ],

            "numero":
                resultado[
                    "numero"
                ],

            "identificador":
                resultado[
                    "identificador"
                ],

            "enlace_pdf":
                resultado[
                    "enlace_pdf"
                ],

            "enlace_xml":
                resultado[
                    "enlace_xml"
                ],

            "enlace_cdr":
                resultado[
                    "enlace_cdr"
                ],

            "codigo_hash":
                resultado[
                    "codigo_hash"
                ],

            "cadena_qr":
                resultado[
                    "cadena_qr"
                ],

            "respuesta":
                respuesta_json,

            "mensaje":
                resultado[
                    "mensaje"
                ],

            "id_boleta":
                id_boleta
        }
    )

    registrar_api(
        servicio=(
            "NUBEFACT"
        ),

        operacion=(
            "GENERAR_BOLETA"
        ),

        exitoso=True,

        id_entidad=(
            id_boleta
        ),

        codigo_http=(
            resultado[
                "codigo_http"
            ]
        ),

        identificador=(
            resultado[
                "identificador"
            ]
        ),

        mensaje=(
            resultado[
                "mensaje"
            ]
        ),

        respuesta=(
            resultado[
                "raw"
            ]
        )
    )

    registrar_bitacora(
        accion=(
            "GENERAR_BOLETA"
        ),

        entidad=(
            "boletas"
        ),

        id_entidad=(
            id_boleta
        ),

        descripcion=(
            "Boleta electrónica generada "
            "mediante NubeFact."
        )
    )

    db.session.commit()


# =========================================================
# GUARDAR ERROR NUBEFACT
# =========================================================

def guardar_error_nubefact(
    id_boleta,
    error
):

    respuesta = (
        error.respuesta
        if isinstance(
            error,
            ErrorNubeFact
        )
        else None
    )

    respuesta_json = (
        json.dumps(
            respuesta,
            ensure_ascii=False,
            default=str
        )
        if respuesta is not None
        else None
    )

    mensaje = str(
        error
    )

    db.session.execute(
        text(
            """
            UPDATE boletas

            SET
                estado =
                    'ERROR',

                mensaje_nubefact =
                    :mensaje,

                respuesta_nubefact =
                    CAST(
                        :respuesta AS JSONB
                    )

            WHERE id_boleta =
                :id_boleta
            """
        ),

        {
            "mensaje":
                mensaje,

            "respuesta":
                respuesta_json,

            "id_boleta":
                id_boleta
        }
    )

    registrar_api(
        servicio=(
            "NUBEFACT"
        ),

        operacion=(
            "GENERAR_BOLETA"
        ),

        exitoso=False,

        id_entidad=(
            id_boleta
        ),

        codigo_http=(
            error.codigo_http
            if isinstance(
                error,
                ErrorNubeFact
            )
            else None
        ),

        mensaje=(
            mensaje
        ),

        respuesta=(
            respuesta
        )
    )

    db.session.commit()


# =========================================================
# EMITIR NUBEFACT
# =========================================================

def emitir_boleta(
    id_boleta,
    consultar_antes=False
):

    datos = (
        obtener_datos_nubefact(
            id_boleta
        )
    )

    if datos is None:

        raise ErrorNubeFact(
            "La boleta no existe."
        )

    boleta = (
        datos[
            "boleta"
        ]
    )

    if consultar_antes:

        consulta = (
            consultar_boleta(
                boleta[
                    "serie"
                ],
                boleta[
                    "numero"
                ]
            )
        )

        if consulta:

            guardar_boleta_generada(
                id_boleta,
                consulta
            )

            return consulta

    payload = (
        construir_payload_boleta(
            boleta=(
                datos[
                    "boleta"
                ]
            ),

            venta=(
                datos[
                    "venta"
                ]
            ),

            cotizacion=(
                datos[
                    "cotizacion"
                ]
            ),

            detalles=(
                datos[
                    "detalles"
                ]
            )
        )
    )

    resultado = (
        generar_boleta(
            payload
        )
    )

    guardar_boleta_generada(
        id_boleta,
        resultado
    )

    return resultado


# =========================================================
# GENERAR DESDE VENTA
# =========================================================

@bp.get(
    "/venta/<int:id_venta>/generar"
)
@rol_requerido(
    "VENDEDOR"
)
def generar_desde_venta(
    id_venta
):

    venta = (
        db.session.execute(
            text(
                """
                SELECT
                    id_venta

                FROM ventas

                WHERE id_venta =
                    :id_venta
                """
            ),

            {
                "id_venta":
                    id_venta
            }
        )
        .scalar_one_or_none()
    )

    if not venta:

        abort(
            404
        )

    try:

        id_boleta = (
            asegurar_boleta(
                id_venta
            )
        )

    except ErrorNubeFact as error:

        flash(
            str(
                error
            ),
            "danger"
        )

        return redirect(
            url_for(
                "boletas_vendedor.lista"
            )
        )

    estado = (
        db.session.execute(
            text(
                """
                SELECT
                    estado::TEXT

                FROM boletas

                WHERE id_boleta =
                    :id_boleta
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .scalar_one()
    )

    if estado == "GENERADA":

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    try:

        emitir_boleta(
            id_boleta
        )

    except ErrorNubeFact as error:

        guardar_error_nubefact(
            id_boleta,
            error
        )

        flash(
            (
                "La venta fue registrada y el stock "
                "ya fue descontado, pero NubeFact "
                f"no pudo generar la boleta: {error}. "
                "Puede reintentarlo sin volver a "
                "descontar stock."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    flash(
        (
            "Cotización aprobada, venta registrada, "
            "stock descontado y boleta generada "
            "correctamente."
        ),
        "success"
    )

    return redirect(
        url_for(
            "boletas_vendedor.detalle",

            id_boleta=(
                id_boleta
            )
        )
    )


# =========================================================
# REINTENTAR NUBEFACT
# =========================================================

@bp.post(
    "/<int:id_boleta>/reintentar"
)
@rol_requerido(
    "VENDEDOR"
)
def reintentar(
    id_boleta
):

    estado = (
        db.session.execute(
            text(
                """
                SELECT
                    estado::TEXT

                FROM boletas

                WHERE id_boleta =
                    :id_boleta
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .scalar_one_or_none()
    )

    if estado is None:

        abort(
            404
        )

    if estado == "GENERADA":

        flash(
            "La boleta ya fue generada.",
            "info"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    try:

        emitir_boleta(
            id_boleta,
            consultar_antes=True
        )

    except ErrorNubeFact as error:

        guardar_error_nubefact(
            id_boleta,
            error
        )

        flash(
            (
                "NubeFact aún no pudo generar "
                f"la boleta: {error}"
            ),
            "danger"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    flash(
        "Boleta generada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "boletas_vendedor.detalle",

            id_boleta=(
                id_boleta
            )
        )
    )


# =========================================================
# DETALLE BOLETA
# =========================================================

@bp.get(
    "/<int:id_boleta>"
)
@rol_requerido(
    "VENDEDOR"
)
def detalle(
    id_boleta
):

    boleta = (
        db.session.execute(
            text(
                """
                SELECT
                    b.id_boleta,
                    b.estado::TEXT AS estado,
                    b.serie,
                    b.numero,
                    b.fecha_emision,
                    b.moneda::TEXT AS moneda,
                    b.total,

                    b.cliente_tipo_documento::TEXT
                        AS cliente_tipo_documento,

                    b.cliente_numero_documento,
                    b.cliente_nombre,
                    b.cliente_direccion,
                    b.cliente_correo,

                    b.enlace_pdf,
                    b.enlace_xml,
                    b.enlace_cdr,
                    b.codigo_hash,
                    b.mensaje_nubefact,
                    b.generada_en,

                    v.id_venta,
                    v.numero_venta,
                    v.subtotal,
                    v.estado::TEXT AS estado_venta,
                    v.tipo_cambio_soles_por_dolar,

                    c.id_cotizacion,
                    c.numero_cotizacion,

                    BTRIM(
                        COALESCE(u.nombres, '')
                        || ' ' ||
                        COALESCE(u.apellidos, '')
                    ) AS vendedor_original

                FROM boletas b

                INNER JOIN ventas v
                    ON v.id_venta =
                       b.id_venta

                INNER JOIN cotizaciones c
                    ON c.id_cotizacion =
                       v.id_cotizacion

                INNER JOIN usuarios u
                    ON u.id_usuario =
                       v.id_vendedor

                WHERE b.id_boleta =
                    :id_boleta
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .mappings()
        .first()
    )

    if boleta is None:

        abort(
            404
        )

    detalles = (
        db.session.execute(
            text(
                """
                SELECT
                    dv.codigo_producto,
                    dv.nombre_producto,
                    dv.cantidad,
                    dv.precio_unitario,
                    dv.subtotal,

                    p.unidad_medida

                FROM detalle_ventas dv

                INNER JOIN productos p
                    ON p.id_producto =
                       dv.id_producto

                WHERE dv.id_venta =
                    :id_venta

                ORDER BY
                    dv.id_detalle_venta
                """
            ),

            {
                "id_venta":
                    boleta[
                        "id_venta"
                    ]
            }
        )
        .mappings()
        .all()
    )

    igv = (
        Decimal(
            boleta[
                "total"
            ]
            or 0
        )
        -
        Decimal(
            boleta[
                "subtotal"
            ]
            or 0
        )
    )

    return render_template(
        "vendedor/boletas/detalle.html",

        boleta=boleta,

        detalles=detalles,

        igv=igv
    )


# =========================================================
# PDF
# =========================================================

@bp.get(
    "/<int:id_boleta>/pdf"
)
@rol_requerido(
    "VENDEDOR"
)
def pdf(
    id_boleta
):

    boleta = (
        db.session.execute(
            text(
                """
                SELECT
                    serie,
                    numero,
                    estado::TEXT AS estado,
                    enlace_pdf

                FROM boletas

                WHERE id_boleta =
                    :id_boleta
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .mappings()
        .first()
    )

    if boleta is None:

        abort(
            404
        )

    if (
        boleta[
            "estado"
        ]
        != "GENERADA"
        or not boleta[
            "enlace_pdf"
        ]
    ):

        abort(
            404
        )

    try:

        contenido = descargar_pdf(
            boleta[
                "enlace_pdf"
            ]
        )

    except ErrorNubeFact as error:

        flash(
            str(
                error
            ),
            "danger"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    descargar = (
        request.args.get(
            "descargar",
            ""
        )
        == "1"
    )

    nombre = (
        f"{boleta['serie']}-"
        f"{boleta['numero']}.pdf"
    )

    disposicion = (
        "attachment"
        if descargar
        else "inline"
    )

    return Response(
        contenido,

        status=200,

        headers={
            "Content-Type":
                "application/pdf",

            "Content-Disposition":
                (
                    f'{disposicion}; '
                    f'filename="{nombre}"'
                )
        }
    )


# =========================================================
# ENVIAR POR CORREO
# =========================================================

@bp.post(
    "/<int:id_boleta>/enviar-correo"
)
@rol_requerido(
    "VENDEDOR"
)
def enviar_boleta_correo(
    id_boleta
):

    boleta = (
        db.session.execute(
            text(
                """
                SELECT
                    id_boleta,
                    estado::TEXT AS estado,
                    serie,
                    numero,
                    cliente_nombre,
                    cliente_correo,
                    enlace_pdf

                FROM boletas

                WHERE id_boleta =
                    :id_boleta
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .mappings()
        .first()
    )

    if boleta is None:

        abort(
            404
        )

    if (
        boleta[
            "estado"
        ]
        != "GENERADA"
    ):

        flash(
            (
                "La boleta todavía no ha sido "
                "generada correctamente."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    if not boleta[
        "cliente_correo"
    ]:

        flash(
            (
                "El cliente no tiene un "
                "correo electrónico registrado."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    numero_intento = (
        db.session.execute(
            text(
                """
                SELECT
                    COALESCE(
                        MAX(numero_intento),
                        0
                    ) + 1

                FROM envios_correo

                WHERE id_boleta =
                    :id_boleta

                  AND tipo_documento =
                    'BOLETA'
                """
            ),

            {
                "id_boleta":
                    id_boleta
            }
        )
        .scalar_one()
    )

    asunto = (
        f"Boleta ROPUSAC "
        f"{boleta['serie']}-"
        f"{boleta['numero']}"
    )

    cuerpo = (
        f"Estimado(a) "
        f"{boleta['cliente_nombre']},\n\n"
        "Adjuntamos su boleta electrónica "
        f"{boleta['serie']}-"
        f"{boleta['numero']}.\n\n"
        "Gracias por su preferencia.\n\n"
        "Saludos,\n"
        "ROPUSAC"
    )

    try:

        pdf_bytes = descargar_pdf(
            boleta[
                "enlace_pdf"
            ]
        )

        enviar_correo(
            destinatario=(
                boleta[
                    "cliente_correo"
                ]
            ),

            asunto=asunto,

            cuerpo=cuerpo,

            archivo=(
                pdf_bytes
            ),

            nombre_archivo=(
                f"{boleta['serie']}-"
                f"{boleta['numero']}.pdf"
            )
        )

    except (
        ErrorNubeFact,
        ErrorCorreo
    ) as error:

        try:

            db.session.execute(
                text(
                    """
                    INSERT INTO envios_correo (
                        tipo_documento,
                        id_boleta,
                        destinatario,
                        asunto,
                        estado,
                        numero_intento,
                        mensaje_error,
                        enviado_por
                    )
                    VALUES (
                        'BOLETA',
                        :id_boleta,
                        :destinatario,
                        :asunto,
                        'ERROR',
                        :numero_intento,
                        :mensaje_error,
                        :usuario
                    )
                    """
                ),

                {
                    "id_boleta":
                        id_boleta,

                    "destinatario":
                        boleta[
                            "cliente_correo"
                        ],

                    "asunto":
                        asunto,

                    "numero_intento":
                        numero_intento,

                    "mensaje_error":
                        str(
                            error
                        ),

                    "usuario":
                        current_user.id_usuario
                }
            )

            registrar_api(
                servicio=(
                    "SMTP"
                ),

                operacion=(
                    "ENVIAR_BOLETA"
                ),

                exitoso=False,

                id_entidad=(
                    id_boleta
                ),

                mensaje=str(
                    error
                )
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

        flash(
            str(
                error
            ),
            "danger"
        )

        return redirect(
            url_for(
                "boletas_vendedor.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    # =====================================================
    # ENVIO EXITOSO
    # =====================================================

    try:

        db.session.execute(
            text(
                """
                INSERT INTO envios_correo (
                    tipo_documento,
                    id_boleta,
                    destinatario,
                    asunto,
                    estado,
                    numero_intento,
                    enviado_por,
                    enviado_en
                )
                VALUES (
                    'BOLETA',
                    :id_boleta,
                    :destinatario,
                    :asunto,
                    'ENVIADO',
                    :numero_intento,
                    :usuario,
                    NOW()
                )
                """
            ),

            {
                "id_boleta":
                    id_boleta,

                "destinatario":
                    boleta[
                        "cliente_correo"
                    ],

                "asunto":
                    asunto,

                "numero_intento":
                    numero_intento,

                "usuario":
                    current_user.id_usuario
            }
        )

        registrar_api(
            servicio=(
                "SMTP"
            ),

            operacion=(
                "ENVIAR_BOLETA"
            ),

            exitoso=True,

            id_entidad=(
                id_boleta
            ),

            mensaje=(
                "Boleta enviada correctamente."
            )
        )

        registrar_bitacora(
            accion=(
                "ENVIAR_BOLETA_CORREO"
            ),

            entidad=(
                "boletas"
            ),

            id_entidad=(
                id_boleta
            ),

            descripcion=(
                "Boleta electrónica enviada "
                "por correo al cliente."
            )
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR REGISTRANDO ENVIO BOLETA:",
            error
        )

    flash(
        (
            "Boleta enviada correctamente a "
            f"{boleta['cliente_correo']}."
        ),
        "success"
    )

    return redirect(
        url_for(
            "boletas_vendedor.detalle",

            id_boleta=(
                id_boleta
            )
        )
    )