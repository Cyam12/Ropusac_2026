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

from sqlalchemy import (
    func,
    text
)

from app.extensiones import db

from app.modelos import (
    Boleta,
    Cliente,
    Cotizacion,
    Producto,
    Proveedor,
    Venta
)

from app.servicios.nubefact import (
    ErrorNubeFact,
    descargar_pdf
)

from app.servicios.pdf_cotizacion import (
    generar_pdf_cotizacion
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


# =========================================================
# CONFIGURACION
# =========================================================

HISTORIAL_POR_PAGINA = 20


# =========================================================
# AUXILIAR
# =========================================================

def dos_decimales(
    valor
):

    return Decimal(
        valor
        or 0
    ).quantize(
        Decimal(
            "0.01"
        )
    )


# =========================================================
# MARCAR COTIZACIONES VENCIDAS
# =========================================================

def actualizar_cotizaciones_vencidas():

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
            "ERROR ACTUALIZANDO COTIZACIONES VENCIDAS:",
            error
        )


# =========================================================
# AREA COMERCIAL
#
# SE CONSERVA SU LOGICA ACTUAL.
# =========================================================

@bp.get(
    "/area-comercial"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def area_comercial():

    proveedores_general = (
        db.session.scalar(
            db.select(
                func.count(
                    Proveedor.id_proveedor
                )
            )
        )
        or 0
    )

    proveedores_usuario = (
        db.session.scalar(
            db.select(
                func.count(
                    Proveedor.id_proveedor
                )
            )
            .where(
                Proveedor.creado_por
                == current_user.id_usuario
            )
        )
        or 0
    )

    productos_general = (
        db.session.scalar(
            db.select(
                func.count(
                    Producto.id_producto
                )
            )
        )
        or 0
    )

    productos_usuario = (
        db.session.scalar(
            db.select(
                func.count(
                    Producto.id_producto
                )
            )
            .where(
                Producto.creado_por
                == current_user.id_usuario
            )
        )
        or 0
    )

    return render_template(
        "area_comercial/inicio.html",

        proveedores_general=(
            proveedores_general
        ),

        proveedores_usuario=(
            proveedores_usuario
        ),

        productos_general=(
            productos_general
        ),

        productos_usuario=(
            productos_usuario
        )
    )


# =========================================================
# VENDEDOR - INICIO
#
# OPTIMIZADO:
#
# ANTES:
#
# CONSULTA 1 -> CLIENTES
# CONSULTA 2 -> COTIZACIONES
# CONSULTA 3 -> BOLETAS
#
# AHORA:
#
# UNA SOLA CONSULTA A POSTGRESQL.
#
# LA LOGICA Y LOS VALORES MOSTRADOS
# SIGUEN SIENDO LOS MISMOS.
# =========================================================

@bp.get(
    "/vendedor"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor():

    id_usuario = (
        current_user.id_usuario
    )

    # =====================================================
    # INDICADORES
    #
    # TODO SE OBTIENE EN UN SOLO VIAJE A NEON.
    # =====================================================

    indicadores = (
        db.session.execute(
            text(
                """
                SELECT

                    (
                        SELECT COUNT(*)

                        FROM clientes

                        WHERE creado_por =
                            :id_usuario
                    ) AS clientes_usuario,

                    (
                        SELECT COUNT(*)

                        FROM cotizaciones

                        WHERE id_vendedor =
                            :id_usuario
                    ) AS cotizaciones_usuario,

                    (
                        SELECT COUNT(*)

                        FROM ventas v

                        INNER JOIN boletas b
                            ON b.id_venta =
                               v.id_venta

                        WHERE v.id_vendedor =
                            :id_usuario
                    ) AS boletas_usuario
                """
            ),

            {
                "id_usuario":
                    id_usuario
            }
        )
        .mappings()
        .one()
    )

    clientes_usuario = (
        indicadores[
            "clientes_usuario"
        ]
        or 0
    )

    cotizaciones_usuario = (
        indicadores[
            "cotizaciones_usuario"
        ]
        or 0
    )

    boletas_usuario = (
        indicadores[
            "boletas_usuario"
        ]
        or 0
    )

    return render_template(
        "vendedor/inicio.html",

        clientes_usuario=(
            clientes_usuario
        ),

        cotizaciones_usuario=(
            cotizaciones_usuario
        ),

        boletas_usuario=(
            boletas_usuario
        )
    )


# =========================================================
# PLACEHOLDER ANTIGUO COTIZACIONES
# =========================================================

@bp.get(
    "/vendedor/cotizaciones"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_cotizaciones():

    return redirect(
        url_for(
            "cotizaciones_vendedor.lista"
        )
    )


# =========================================================
# PLACEHOLDER ANTIGUO BOLETAS
# =========================================================

@bp.get(
    "/vendedor/boletas"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_boletas():

    return redirect(
        url_for(
            "boletas_vendedor.lista"
        )
    )


# =========================================================
# HISTORIAL DE OPERACIONES
#
# TODOS LOS VENDEDORES PUEDEN CONSULTAR
# OPERACIONES DE TODOS LOS VENDEDORES.
#
# SOLO LECTURA.
#
# OPTIMIZADO:
#
# - 20 OPERACIONES POR PAGINA
# - MAXIMO 21 REGISTROS POR CONSULTA
# - SIN COUNT(*)
# - FILTROS EN POSTGRESQL
# =========================================================

@bp.get(
    "/vendedor/historial"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_historial():

    # =====================================================
    # ACTUALIZAR VENCIDAS
    # =====================================================

    actualizar_cotizaciones_vencidas()

    # =====================================================
    # FILTROS
    # =====================================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    tipo = request.args.get(
        "tipo",
        ""
    ).strip().upper()

    estado = request.args.get(
        "estado",
        ""
    ).strip().upper()

    origen = request.args.get(
        "origen",
        ""
    ).strip().upper()

    pagina = request.args.get(
        "pagina",
        1,
        type=int
    )

    if pagina < 1:

        pagina = 1

    offset = (
        pagina - 1
    ) * HISTORIAL_POR_PAGINA

    parametros = {
        "limite":
            HISTORIAL_POR_PAGINA
            + 1,

        "offset":
            offset
    }

    # =====================================================
    # CONSULTA
    # =====================================================

    consulta = """
        SELECT
            h.id_vendedor,
            h.tipo_operacion,
            h.id_operacion,
            h.numero_operacion,
            h.fecha_operacion,
            h.cliente,
            h.estado,
            h.moneda,
            h.total,
            h.url_documento,

            BTRIM(
                COALESCE(
                    u.nombres,
                    ''
                )
                || ' ' ||
                COALESCE(
                    u.apellidos,
                    ''
                )
            ) AS vendedor,

            CASE
                WHEN
                    h.tipo_operacion = 'COTIZACION'
                    AND h.estado = 'VENCIDA'
                THEN TRUE
                ELSE FALSE
            END AS cotizacion_vencida

        FROM vista_historial_operaciones_vendedor h

        LEFT JOIN usuarios u
            ON u.id_usuario =
               h.id_vendedor

        WHERE 1 = 1
    """

    # =====================================================
    # BUSCAR
    # =====================================================

    if buscar:

        consulta += """
            AND (
                h.numero_operacion
                    ILIKE :buscar

                OR h.cliente
                    ILIKE :buscar

                OR u.nombres
                    ILIKE :buscar

                OR u.apellidos
                    ILIKE :buscar

                OR BTRIM(
                    COALESCE(
                        u.nombres,
                        ''
                    )
                    || ' ' ||
                    COALESCE(
                        u.apellidos,
                        ''
                    )
                )
                    ILIKE :buscar
            )
        """

        parametros[
            "buscar"
        ] = (
            f"%{buscar}%"
        )

    # =====================================================
    # TIPO
    # =====================================================

    if tipo in (
        "COTIZACION",
        "VENTA",
        "BOLETA"
    ):

        consulta += """
            AND h.tipo_operacion =
                :tipo
        """

        parametros[
            "tipo"
        ] = tipo

    # =====================================================
    # ESTADO
    # =====================================================

    if estado:

        consulta += """
            AND h.estado =
                :estado
        """

        parametros[
            "estado"
        ] = estado

    # =====================================================
    # MIS OPERACIONES
    # =====================================================

    if origen == "MIAS":

        consulta += """
            AND h.id_vendedor =
                :id_usuario
        """

        parametros[
            "id_usuario"
        ] = (
            current_user.id_usuario
        )

    # =====================================================
    # ORDEN + PAGINACION
    # =====================================================

    consulta += """
        ORDER BY
            h.fecha_operacion DESC,
            h.id_operacion DESC

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
        HISTORIAL_POR_PAGINA
    )

    operaciones = filas[
        :HISTORIAL_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not operaciones
    ):

        return redirect(
            url_for(
                "dashboard.vendedor_historial",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar,

                tipo=tipo,

                estado=estado,

                origen=origen
            )
        )

    # =====================================================
    # ESTADOS
    # =====================================================

    estados = [
        "BORRADOR",
        "EMITIDA",
        "ENVIADA",
        "APROBADA",
        "RECHAZADA",
        "VENCIDA",
        "CONVERTIDA_VENTA",
        "ANULADA",
        "PENDIENTE_BOLETA",
        "FACTURADA",
        "PENDIENTE",
        "GENERADA",
        "ERROR"
    ]

    return render_template(
        "vendedor/historial/lista.html",

        operaciones=(
            operaciones
        ),

        buscar=buscar,

        tipo=tipo,

        estado=estado,

        origen=origen,

        estados=estados,

        pagina=pagina,

        por_pagina=(
            HISTORIAL_POR_PAGINA
        ),

        hay_anterior=(
            hay_anterior
        ),

        hay_siguiente=(
            hay_siguiente
        )
    )


# =========================================================
# HISTORIAL - DETALLE COTIZACION
# =========================================================

@bp.get(
    "/vendedor/historial/cotizacion/<int:id_cotizacion>"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_historial_cotizacion(
    id_cotizacion
):

    actualizar_cotizaciones_vencidas()

    cotizacion = (
        db.session.execute(
            text(
                """
                SELECT
                    c.id_cotizacion,
                    c.numero_cotizacion,
                    c.fecha_emision,
                    c.fecha_vigencia,
                    c.estado::TEXT
                        AS estado,
                    c.moneda::TEXT
                        AS moneda,
                    c.tipo_cambio_soles_por_dolar,
                    c.subtotal,
                    c.total,
                    c.total_equivalente,
                    c.observaciones,
                    c.pdf_url,
                    c.pdf_generado_en,
                    c.enviada_correo_en,
                    c.aprobada_en,
                    c.creado_en,

                    cl.id_cliente,

                    COALESCE(
                        cl.razon_social,
                        BTRIM(
                            COALESCE(
                                cl.nombres,
                                ''
                            )
                            || ' ' ||
                            COALESCE(
                                cl.apellidos,
                                ''
                            )
                        )
                    ) AS cliente,

                    cl.tipo_documento::TEXT
                        AS tipo_documento,

                    cl.numero_documento,
                    cl.correo,
                    cl.celular,
                    cl.direccion,

                    u.id_usuario
                        AS id_vendedor,

                    BTRIM(
                        COALESCE(
                            u.nombres,
                            ''
                        )
                        || ' ' ||
                        COALESCE(
                            u.apellidos,
                            ''
                        )
                    ) AS vendedor

                FROM cotizaciones c

                INNER JOIN clientes cl
                    ON cl.id_cliente =
                       c.id_cliente

                INNER JOIN usuarios u
                    ON u.id_usuario =
                       c.id_vendedor

                WHERE c.id_cotizacion =
                    :id_cotizacion
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

        abort(
            404
        )

    detalles = (
        db.session.execute(
            text(
                """
                SELECT
                    id_detalle_cotizacion,
                    codigo_producto,
                    nombre_producto,
                    cantidad,
                    precio_unitario,
                    subtotal

                FROM detalle_cotizaciones

                WHERE id_cotizacion =
                    :id_cotizacion

                ORDER BY
                    id_detalle_cotizacion
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

    estados = (
        db.session.execute(
            text(
                """
                SELECT
                    h.id_historial_estado,
                    h.estado_anterior::TEXT
                        AS estado_anterior,
                    h.estado_nuevo::TEXT
                        AS estado_nuevo,
                    h.observacion,
                    h.cambiado_en,

                    BTRIM(
                        COALESCE(
                            u.nombres,
                            ''
                        )
                        || ' ' ||
                        COALESCE(
                            u.apellidos,
                            ''
                        )
                    ) AS usuario

                FROM historial_estados_cotizacion h

                LEFT JOIN usuarios u
                    ON u.id_usuario =
                       h.cambiado_por

                WHERE h.id_cotizacion =
                    :id_cotizacion

                ORDER BY
                    h.cambiado_en ASC,
                    h.id_historial_estado ASC
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

    igv = dos_decimales(
        Decimal(
            cotizacion[
                "total"
            ]
            or 0
        )
        -
        Decimal(
            cotizacion[
                "subtotal"
            ]
            or 0
        )
    )

    return render_template(
        "vendedor/historial/detalle_cotizacion.html",

        cotizacion=(
            cotizacion
        ),

        detalles=(
            detalles
        ),

        estados=(
            estados
        ),

        igv=igv
    )


# =========================================================
# HISTORIAL - DETALLE VENTA
# =========================================================

@bp.get(
    "/vendedor/historial/venta/<int:id_venta>"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_historial_venta(
    id_venta
):

    venta = (
        db.session.execute(
            text(
                """
                SELECT
                    v.id_venta,
                    v.numero_venta,
                    v.fecha_venta,
                    v.moneda::TEXT
                        AS moneda,
                    v.tipo_cambio_soles_por_dolar,
                    v.subtotal,
                    v.total,
                    v.estado::TEXT
                        AS estado,
                    v.creado_en,

                    c.id_cotizacion,
                    c.numero_cotizacion,
                    c.estado::TEXT
                        AS estado_cotizacion,

                    cl.id_cliente,

                    COALESCE(
                        cl.razon_social,
                        BTRIM(
                            COALESCE(
                                cl.nombres,
                                ''
                            )
                            || ' ' ||
                            COALESCE(
                                cl.apellidos,
                                ''
                            )
                        )
                    ) AS cliente,

                    cl.tipo_documento::TEXT
                        AS tipo_documento,

                    cl.numero_documento,

                    u.id_usuario
                        AS id_vendedor,

                    BTRIM(
                        COALESCE(
                            u.nombres,
                            ''
                        )
                        || ' ' ||
                        COALESCE(
                            u.apellidos,
                            ''
                        )
                    ) AS vendedor,

                    b.id_boleta,
                    b.estado::TEXT
                        AS estado_boleta,
                    b.serie,
                    b.numero
                        AS numero_boleta

                FROM ventas v

                INNER JOIN cotizaciones c
                    ON c.id_cotizacion =
                       v.id_cotizacion

                INNER JOIN clientes cl
                    ON cl.id_cliente =
                       v.id_cliente

                INNER JOIN usuarios u
                    ON u.id_usuario =
                       v.id_vendedor

                LEFT JOIN boletas b
                    ON b.id_venta =
                       v.id_venta

                WHERE v.id_venta =
                    :id_venta
                """
            ),

            {
                "id_venta":
                    id_venta
            }
        )
        .mappings()
        .first()
    )

    if venta is None:

        abort(
            404
        )

    detalles = (
        db.session.execute(
            text(
                """
                SELECT
                    id_detalle_venta,
                    codigo_producto,
                    nombre_producto,
                    cantidad,
                    precio_unitario,
                    subtotal

                FROM detalle_ventas

                WHERE id_venta =
                    :id_venta

                ORDER BY
                    id_detalle_venta
                """
            ),

            {
                "id_venta":
                    id_venta
            }
        )
        .mappings()
        .all()
    )

    igv = dos_decimales(
        Decimal(
            venta[
                "total"
            ]
            or 0
        )
        -
        Decimal(
            venta[
                "subtotal"
            ]
            or 0
        )
    )

    return render_template(
        "vendedor/historial/detalle_venta.html",

        venta=venta,

        detalles=detalles,

        igv=igv
    )


# =========================================================
# HISTORIAL - DETALLE BOLETA
# =========================================================

@bp.get(
    "/vendedor/historial/boleta/<int:id_boleta>"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_historial_boleta(
    id_boleta
):

    boleta = (
        db.session.execute(
            text(
                """
                SELECT
                    b.id_boleta,
                    b.estado::TEXT
                        AS estado,
                    b.tipo_comprobante,
                    b.serie,
                    b.numero,
                    b.fecha_emision,
                    b.moneda::TEXT
                        AS moneda,
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
                    b.creada_en,

                    v.id_venta,
                    v.numero_venta,
                    v.subtotal,
                    v.estado::TEXT
                        AS estado_venta,
                    v.tipo_cambio_soles_por_dolar,

                    c.id_cotizacion,
                    c.numero_cotizacion,
                    c.estado::TEXT
                        AS estado_cotizacion,

                    BTRIM(
                        COALESCE(
                            u.nombres,
                            ''
                        )
                        || ' ' ||
                        COALESCE(
                            u.apellidos,
                            ''
                        )
                    ) AS vendedor

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
                    dv.id_detalle_venta,
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

    igv = dos_decimales(
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
        "vendedor/historial/detalle_boleta.html",

        boleta=boleta,

        detalles=detalles,

        igv=igv
    )


# =========================================================
# HISTORIAL - VISUALIZAR / DESCARGAR COTIZACION
# =========================================================

@bp.get(
    "/vendedor/historial/cotizacion/<int:id_cotizacion>/pdf"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_historial_cotizacion_pdf(
    id_cotizacion
):

    cotizacion = (
        db.session.execute(
            text(
                """
                SELECT
                    id_cotizacion,
                    numero_cotizacion

                FROM cotizaciones

                WHERE id_cotizacion =
                    :id_cotizacion
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

        abort(
            404
        )

    try:

        contenido = (
            generar_pdf_cotizacion(
                id_cotizacion
            )
        )

    except Exception as error:

        print(
            "ERROR GENERANDO PDF HISTORICO:",
            error
        )

        flash(
            (
                "No fue posible obtener "
                "el PDF de la cotización."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "dashboard.vendedor_historial_cotizacion",

                id_cotizacion=(
                    id_cotizacion
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

    disposicion = (
        "attachment"
        if descargar
        else "inline"
    )

    nombre_archivo = (
        f"{cotizacion['numero_cotizacion']}.pdf"
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
                    f'filename="{nombre_archivo}"'
                )
        }
    )


# =========================================================
# HISTORIAL - VISUALIZAR / DESCARGAR BOLETA
# =========================================================

@bp.get(
    "/vendedor/historial/boleta/<int:id_boleta>/pdf"
)
@rol_requerido(
    "VENDEDOR"
)
def vendedor_historial_boleta_pdf(
    id_boleta
):

    boleta = (
        db.session.execute(
            text(
                """
                SELECT
                    estado::TEXT
                        AS estado,
                    serie,
                    numero,
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

        flash(
            (
                "La boleta no tiene un "
                "PDF disponible."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "dashboard.vendedor_historial_boleta",

                id_boleta=(
                    id_boleta
                )
            )
        )

    try:

        contenido = (
            descargar_pdf(
                boleta[
                    "enlace_pdf"
                ]
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
                "dashboard.vendedor_historial_boleta",

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

    disposicion = (
        "attachment"
        if descargar
        else "inline"
    )

    nombre_archivo = (
        f"{boleta['serie']}-"
        f"{boleta['numero']}.pdf"
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
                    f'filename="{nombre_archivo}"'
                )
        }
    )