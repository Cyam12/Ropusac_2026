import json

from datetime import date

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP
)

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import current_user

from sqlalchemy import (
    or_,
    text
)

from app.extensiones import db

from app.modelos import (
    Cliente,
    Cotizacion,
    DetalleCotizacion,
    Producto,
    RegistroApi,
    ServicioApiEnum,
    Usuario
)

from app.rutas.documentos import (
    crear_token_cotizacion
)

from app.servicios.correo import (
    ErrorCorreo,
    enviar_correo
)

from app.servicios.exchange_rate import (
    ErrorExchangeRate,
    obtener_soles_por_dolar
)

from app.servicios.pdf_cotizacion import (
    generar_pdf_cotizacion
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "cotizaciones_vendedor",
    __name__,
    url_prefix="/vendedor/cotizaciones"
)


# =========================================================
# CONFIGURACION
# =========================================================

COTIZACIONES_POR_PAGINA = 20


# =========================================================
# IGV
#
# LOS PRECIOS FINALES YA INCLUYEN IGV.
#
# TOTAL = PRECIO FINAL
# SUBTOTAL = TOTAL / 1.18
# IGV = TOTAL - SUBTOTAL
# =========================================================

FACTOR_IGV = Decimal(
    "1.18"
)


# =========================================================
# AUXILIARES
# =========================================================

def decimal_o_none(
    valor
):

    if valor is None:
        return None

    try:

        numero = Decimal(
            str(
                valor
            )
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return None

    if not numero.is_finite():
        return None

    return numero


def dos_decimales(
    valor
):

    return Decimal(
        valor
    ).quantize(
        Decimal(
            "0.01"
        ),
        rounding=ROUND_HALF_UP
    )


def texto_enum(
    valor
):

    if valor is None:
        return ""

    if hasattr(
        valor,
        "value"
    ):

        return valor.value

    return str(
        valor
    )


def nombre_cliente(
    cliente
):

    if cliente.razon_social:

        return cliente.razon_social

    return " ".join(
        parte
        for parte in [
            cliente.nombres,
            cliente.apellidos
        ]
        if parte
    ).strip()


def nombre_usuario(
    usuario
):

    if usuario is None:

        return (
            "Usuario no disponible"
        )

    nombre = " ".join(
        parte
        for parte in [
            usuario.nombres,
            usuario.apellidos
        ]
        if parte
    ).strip()

    return (
        nombre
        or usuario.correo
        or "Usuario"
    )


def obtener_subtotal_sin_igv(
    total_con_igv
):

    total_con_igv = Decimal(
        total_con_igv
        or 0
    )

    return dos_decimales(
        total_con_igv
        / FACTOR_IGV
    )


def obtener_igv_incluido(
    total_con_igv
):

    total_con_igv = dos_decimales(
        Decimal(
            total_con_igv
            or 0
        )
    )

    subtotal = (
        obtener_subtotal_sin_igv(
            total_con_igv
        )
    )

    return dos_decimales(
        total_con_igv
        -
        subtotal
    )


# =========================================================
# SERIALIZAR CLIENTE
# =========================================================

def serializar_cliente(
    cliente
):

    return {
        "id":
            cliente.id_cliente,

        "nombre":
            nombre_cliente(
                cliente
            ),

        "documento":
            (
                cliente.numero_documento
                or "SIN DOCUMENTO"
            ),

        "tipo_documento":
            texto_enum(
                cliente.tipo_documento
            ),

        "correo":
            cliente.correo
            or "",

        "direccion":
            cliente.direccion
            or ""
    }


# =========================================================
# SERIALIZAR PRODUCTO
# =========================================================

def serializar_producto(
    producto,
    soles_por_dolar
):

    precio_pen = (
        precio_producto_pen(
            producto,
            soles_por_dolar
        )
    )

    return {
        "id":
            producto.id_producto,

        "codigo":
            producto.codigo_producto,

        "nombre":
            producto.nombre,

        "marca":
            producto.marca
            or "",

        "modelo":
            producto.modelo
            or "",

        "unidad":
            producto.unidad_medida,

        "stock":
            float(
                producto.stock_disponible
            ),

        "precio_pen":
            float(
                precio_pen
            )
    }


# =========================================================
# ULTIMOS 3 CLIENTES
# =========================================================

def obtener_clientes_recientes():

    clientes = (
        db.session.execute(
            db.select(
                Cliente
            )
            .where(
                Cliente.activo.is_(
                    True
                )
            )
            .order_by(
                Cliente.creado_en.desc(),
                Cliente.id_cliente.desc()
            )
            .limit(
                3
            )
        )
        .scalars()
        .all()
    )

    return [
        serializar_cliente(
            cliente
        )
        for cliente in clientes
    ]


# =========================================================
# ULTIMOS 3 PRODUCTOS
# =========================================================

def obtener_productos_recientes(
    soles_por_dolar
):

    productos = (
        db.session.execute(
            db.select(
                Producto
            )
            .where(
                Producto.activo.is_(
                    True
                ),

                Producto.precio_venta_actual.is_not(
                    None
                ),

                Producto.stock_disponible > 0
            )
            .order_by(
                Producto.creado_en.desc(),
                Producto.id_producto.desc()
            )
            .limit(
                3
            )
        )
        .scalars()
        .all()
    )

    return [
        serializar_producto(
            producto,
            soles_por_dolar
        )
        for producto in productos
    ]


# =========================================================
# ACTUALIZAR COTIZACIONES VENCIDAS
# =========================================================

def actualizar_vencidas():

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
            "ERROR ACTUALIZANDO "
            "COTIZACIONES VENCIDAS:",
            error
        )


# =========================================================
# REGISTRAR API
# =========================================================

def registrar_api(
    servicio,
    operacion,
    exitoso,
    codigo_http=None,
    identificador_externo=None,
    mensaje=None,
    id_entidad=None,
    respuesta=None
):

    registro = RegistroApi(
        servicio=servicio,

        operacion=operacion,

        id_usuario=(
            current_user.id_usuario
        ),

        entidad_relacionada=(
            "cotizaciones"
        ),

        id_entidad_relacionada=(
            id_entidad
        ),

        codigo_http=(
            codigo_http
        ),

        exitoso=(
            exitoso
        ),

        identificador_externo=(
            identificador_externo
        ),

        mensaje=(
            mensaje
        ),

        respuesta_resumida=(
            respuesta
        )
    )

    db.session.add(
        registro
    )


# =========================================================
# =========================================================
# OBTENER ULTIMO TIPO DE CAMBIO GUARDADO
#
# Esta consulta nunca llama a servicios externos. Permite
# renderizar la pantalla usando el último valor persistido
# mientras el navegador actualiza la tasa en segundo plano.
# =========================================================

def obtener_tipo_cambio_guardado():

    existente = (
        db.session.execute(
            text(
                """
                SELECT
                    id_tipo_cambio,
                    soles_por_dolar,
                    fecha_tipo_cambio,
                    identificador_consulta

                FROM tipos_cambio

                WHERE proveedor = 'ExchangeRate-API'

                ORDER BY
                    obtenido_en DESC,
                    id_tipo_cambio DESC

                LIMIT 1
                """
            )
        )
        .mappings()
        .first()
    )

    if not existente:
        return None

    return {
        "id_tipo_cambio":
            existente["id_tipo_cambio"],

        "soles_por_dolar":
            Decimal(
                existente["soles_por_dolar"]
            ),

        "fecha_tipo_cambio":
            existente["fecha_tipo_cambio"],

        "identificador_consulta":
            existente["identificador_consulta"]
    }


# PRECIO PRODUCTO EN PEN
# =========================================================

def precio_producto_pen(
    producto,
    soles_por_dolar
):

    precio = Decimal(
        producto.precio_venta_actual
    )

    moneda_producto = texto_enum(
        producto.moneda_precio
    )

    if moneda_producto == "PEN":

        return dos_decimales(
            precio
        )

    return dos_decimales(
        precio
        *
        soles_por_dolar
    )


# =========================================================
# LISTAR COTIZACIONES
#
# OPTIMIZADO:
#
# - 20 COTIZACIONES POR PAGINA
# - SOLO COLUMNAS NECESARIAS
# - SIN OBJETOS ORM COMPLETOS
# - UNA SOLA CONSULTA
# =========================================================

@bp.get("/")
@rol_requerido(
    "VENDEDOR"
)
def lista():

    actualizar_vencidas()

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    estado = request.args.get(
        "estado",
        ""
    ).strip()

    origen = request.args.get(
        "origen",
        ""
    ).strip()

    pagina = request.args.get(
        "pagina",
        1,
        type=int
    )

    if pagina < 1:
        pagina = 1

    # =====================================================
    # CONSULTA LIGERA
    # =====================================================

    consulta = (
        db.select(

            # COTIZACION

            Cotizacion.id_cotizacion.label(
                "id_cotizacion"
            ),

            Cotizacion.numero_cotizacion.label(
                "numero_cotizacion"
            ),

            Cotizacion.id_vendedor.label(
                "id_vendedor"
            ),

            Cotizacion.fecha_emision.label(
                "fecha_emision"
            ),

            Cotizacion.fecha_vigencia.label(
                "fecha_vigencia"
            ),

            Cotizacion.estado.label(
                "estado_cotizacion"
            ),

            Cotizacion.moneda.label(
                "moneda"
            ),

            Cotizacion.total.label(
                "total"
            ),

            Cotizacion.pdf_url.label(
                "pdf_url"
            ),

            # CLIENTE

            Cliente.nombres.label(
                "cliente_nombres"
            ),

            Cliente.apellidos.label(
                "cliente_apellidos"
            ),

            Cliente.razon_social.label(
                "cliente_razon_social"
            ),

            # VENDEDOR

            Usuario.nombres.label(
                "vendedor_nombres"
            ),

            Usuario.apellidos.label(
                "vendedor_apellidos"
            ),

            Usuario.correo.label(
                "vendedor_correo"
            )
        )
        .select_from(
            Cotizacion
        )
        .join(
            Cliente,
            Cotizacion.id_cliente
            == Cliente.id_cliente
        )
        .join(
            Usuario,
            Cotizacion.id_vendedor
            == Usuario.id_usuario
        )
    )

    # =====================================================
    # BUSCAR
    # =====================================================

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        consulta = consulta.where(
            or_(
                Cotizacion.numero_cotizacion.ilike(
                    patron
                ),

                Cliente.nombres.ilike(
                    patron
                ),

                Cliente.apellidos.ilike(
                    patron
                ),

                Cliente.razon_social.ilike(
                    patron
                ),

                Cliente.numero_documento.ilike(
                    patron
                ),

                Usuario.nombres.ilike(
                    patron
                ),

                Usuario.apellidos.ilike(
                    patron
                )
            )
        )

    # =====================================================
    # ESTADO
    # =====================================================

    if estado:

        consulta = consulta.where(
            Cotizacion.estado
            == estado
        )

    # =====================================================
    # CREADAS POR MI
    # =====================================================

    if origen == "MIAS":

        consulta = consulta.where(
            Cotizacion.id_vendedor
            == current_user.id_usuario
        )

    # =====================================================
    # PAGINACION
    #
    # 20 VISIBLES + 1 PARA SABER SI HAY SIGUIENTE.
    #
    # ORDENAMOS POR PRIMARY KEY PARA EVITAR
    # CARGAR Y ORDENAR TODA LA TABLA.
    # =====================================================

    offset = (
        pagina - 1
    ) * COTIZACIONES_POR_PAGINA

    consulta = (
        consulta
        .order_by(
            Cotizacion.id_cotizacion.desc()
        )
        .offset(
            offset
        )
        .limit(
            COTIZACIONES_POR_PAGINA
            + 1
        )
    )

    filas = (
        db.session.execute(
            consulta
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

    filas = filas[
        :COTIZACIONES_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # PREPARAR COTIZACIONES
    # =====================================================

    cotizaciones = []

    for fila in filas:

        cliente = (
            fila[
                "cliente_razon_social"
            ]
            or
            " ".join(
                parte
                for parte in [
                    fila[
                        "cliente_nombres"
                    ],

                    fila[
                        "cliente_apellidos"
                    ]
                ]
                if parte
            ).strip()
        )

        vendedor = " ".join(
            parte
            for parte in [
                fila[
                    "vendedor_nombres"
                ],

                fila[
                    "vendedor_apellidos"
                ]
            ]
            if parte
        ).strip()

        if not vendedor:

            vendedor = (
                fila[
                    "vendedor_correo"
                ]
                or
                "Usuario"
            )

        cotizaciones.append({

            "cotizacion": {

                "id_cotizacion":
                    fila[
                        "id_cotizacion"
                    ],

                "numero_cotizacion":
                    fila[
                        "numero_cotizacion"
                    ],

                "id_vendedor":
                    fila[
                        "id_vendedor"
                    ],

                "fecha_emision":
                    fila[
                        "fecha_emision"
                    ],

                "fecha_vigencia":
                    fila[
                        "fecha_vigencia"
                    ],

                "estado":
                    texto_enum(
                        fila[
                            "estado_cotizacion"
                        ]
                    ),

                "moneda":
                    texto_enum(
                        fila[
                            "moneda"
                        ]
                    ),

                "total":
                    fila[
                        "total"
                    ],

                "pdf_url":
                    fila[
                        "pdf_url"
                    ]
            },

            "cliente":
                cliente,

            "vendedor":
                vendedor,

            "es_mia":
                (
                    fila[
                        "id_vendedor"
                    ]
                    ==
                    current_user.id_usuario
                )
        })

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not cotizaciones
    ):

        return redirect(
            url_for(
                "cotizaciones_vendedor.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar,

                estado=estado,

                origen=origen
            )
        )

    estados = [
        "BORRADOR",
        "EMITIDA",
        "ENVIADA",
        "APROBADA",
        "RECHAZADA",
        "VENCIDA",
        "CONVERTIDA_VENTA",
        "ANULADA"
    ]

    return render_template(
        "vendedor/cotizaciones/lista.html",

        cotizaciones=cotizaciones,

        buscar=buscar,

        estado=estado,

        origen=origen,

        estados=estados,

        texto_enum=texto_enum,

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
# BUSCAR CLIENTES
# =========================================================

@bp.get(
    "/clientes/buscar"
)
@rol_requerido(
    "VENDEDOR"
)
def buscar_clientes():

    q = request.args.get(
        "q",
        ""
    ).strip()

    if not q:

        return jsonify({
            "exito":
                True,

            "resultados":
                obtener_clientes_recientes()
        })

    prefijo = (
        f"{q}%"
    )

    patron = (
        f"%{q}%"
    )

    clientes = (
        db.session.execute(
            db.select(
                Cliente
            )
            .where(
                Cliente.activo.is_(
                    True
                ),

                or_(
                    Cliente.numero_documento.ilike(
                        prefijo
                    ),

                    Cliente.razon_social.ilike(
                        prefijo
                    ),

                    Cliente.nombres.ilike(
                        prefijo
                    ),

                    Cliente.apellidos.ilike(
                        prefijo
                    ),

                    Cliente.correo.ilike(
                        prefijo
                    )
                )
            )
            .order_by(
                Cliente.creado_en.desc(),
                Cliente.id_cliente.desc()
            )
            .limit(
                3
            )
        )
        .scalars()
        .all()
    )

    if len(
        clientes
    ) < 3:

        ids_encontrados = [
            cliente.id_cliente
            for cliente in clientes
        ]

        consulta_parcial = (
            db.select(
                Cliente
            )
            .where(
                Cliente.activo.is_(
                    True
                ),

                or_(
                    Cliente.numero_documento.ilike(
                        patron
                    ),

                    Cliente.razon_social.ilike(
                        patron
                    ),

                    Cliente.nombres.ilike(
                        patron
                    ),

                    Cliente.apellidos.ilike(
                        patron
                    ),

                    Cliente.correo.ilike(
                        patron
                    )
                )
            )
        )

        if ids_encontrados:

            consulta_parcial = (
                consulta_parcial.where(
                    Cliente.id_cliente.notin_(
                        ids_encontrados
                    )
                )
            )

        consulta_parcial = (
            consulta_parcial
            .order_by(
                Cliente.creado_en.desc(),
                Cliente.id_cliente.desc()
            )
            .limit(
                3
                -
                len(
                    clientes
                )
            )
        )

        adicionales = (
            db.session.execute(
                consulta_parcial
            )
            .scalars()
            .all()
        )

        clientes.extend(
            adicionales
        )

    return jsonify({
        "exito":
            True,

        "resultados": [
            serializar_cliente(
                cliente
            )
            for cliente in clientes
        ]
    })


# =========================================================
# BUSCAR PRODUCTOS
# =========================================================

@bp.get(
    "/productos/buscar"
)
@rol_requerido(
    "VENDEDOR"
)
def buscar_productos():

    q = request.args.get(
        "q",
        ""
    ).strip()

    id_tipo_cambio = request.args.get(
        "id_tipo_cambio",
        type=int
    )

    if not id_tipo_cambio:

        return jsonify({
            "exito":
                False,

            "mensaje":
                "El tipo de cambio no es válido."
        }), 400

    tipo_cambio = (
        db.session.execute(
            text(
                """
                SELECT soles_por_dolar

                FROM tipos_cambio

                WHERE id_tipo_cambio =
                    :id_tipo_cambio
                """
            ),

            {
                "id_tipo_cambio":
                    id_tipo_cambio
            }
        )
        .scalar_one_or_none()
    )

    if tipo_cambio is None:

        return jsonify({
            "exito":
                False,

            "mensaje":
                "El tipo de cambio no es válido."
        }), 400

    soles_por_dolar = Decimal(
        tipo_cambio
    )

    if not q:

        return jsonify({
            "exito":
                True,

            "resultados":
                obtener_productos_recientes(
                    soles_por_dolar
                )
        })

    prefijo = (
        f"{q}%"
    )

    patron = (
        f"%{q}%"
    )

    productos = (
        db.session.execute(
            db.select(
                Producto
            )
            .where(
                Producto.activo.is_(
                    True
                ),

                Producto.precio_venta_actual.is_not(
                    None
                ),

                Producto.stock_disponible > 0,

                or_(
                    Producto.codigo_producto.ilike(
                        prefijo
                    ),

                    Producto.nombre.ilike(
                        prefijo
                    ),

                    Producto.marca.ilike(
                        prefijo
                    ),

                    Producto.modelo.ilike(
                        prefijo
                    )
                )
            )
            .order_by(
                Producto.creado_en.desc(),
                Producto.id_producto.desc()
            )
            .limit(
                3
            )
        )
        .scalars()
        .all()
    )

    if len(
        productos
    ) < 3:

        ids_encontrados = [
            producto.id_producto
            for producto in productos
        ]

        consulta_parcial = (
            db.select(
                Producto
            )
            .where(
                Producto.activo.is_(
                    True
                ),

                Producto.precio_venta_actual.is_not(
                    None
                ),

                Producto.stock_disponible > 0,

                or_(
                    Producto.codigo_producto.ilike(
                        patron
                    ),

                    Producto.nombre.ilike(
                        patron
                    ),

                    Producto.descripcion.ilike(
                        patron
                    ),

                    Producto.categoria.ilike(
                        patron
                    ),

                    Producto.marca.ilike(
                        patron
                    ),

                    Producto.modelo.ilike(
                        patron
                    )
                )
            )
        )

        if ids_encontrados:

            consulta_parcial = (
                consulta_parcial.where(
                    Producto.id_producto.notin_(
                        ids_encontrados
                    )
                )
            )

        consulta_parcial = (
            consulta_parcial
            .order_by(
                Producto.creado_en.desc(),
                Producto.id_producto.desc()
            )
            .limit(
                3
                -
                len(
                    productos
                )
            )
        )

        adicionales = (
            db.session.execute(
                consulta_parcial
            )
            .scalars()
            .all()
        )

        productos.extend(
            adicionales
        )

    return jsonify({
        "exito":
            True,

        "resultados": [
            serializar_producto(
                producto,
                soles_por_dolar
            )
            for producto in productos
        ]
    })


# =========================================================
# =========================================================
# ACTUALIZAR TIPO DE CAMBIO
#
# La consulta externa se ejecuta mediante AJAX para que
# nunca retrase la apertura de la pantalla de cotización.
# =========================================================

@bp.post(
    "/tipo-cambio/actualizar"
)
@rol_requerido(
    "VENDEDOR"
)
def actualizar_tipo_cambio():

    try:

        resultado = (
            obtener_soles_por_dolar()
        )

        # Si ExchangeRate-API devuelve el mismo identificador
        # de actualización, reutilizamos el registro existente.
        # Así evitamos duplicar filas en Neon.
        existente = None

        if resultado["identificador"]:

            existente = (
                db.session.execute(
                    text(
                        """
                        SELECT
                            id_tipo_cambio

                        FROM tipos_cambio

                        WHERE proveedor = 'ExchangeRate-API'
                          AND identificador_consulta =
                              :identificador

                        ORDER BY obtenido_en DESC

                        LIMIT 1
                        """
                    ),
                    {
                        "identificador":
                            resultado["identificador"]
                    }
                )
                .mappings()
                .first()
            )

        if existente:

            id_tipo_cambio = (
                existente["id_tipo_cambio"]
            )

        else:

            id_tipo_cambio = (
                db.session.execute(
                    text(
                        """
                        INSERT INTO tipos_cambio (
                            soles_por_dolar,
                            proveedor,
                            fecha_tipo_cambio,
                            identificador_consulta
                        )
                        VALUES (
                            :soles_por_dolar,
                            'ExchangeRate-API',
                            CURRENT_DATE,
                            :identificador
                        )
                        RETURNING id_tipo_cambio
                        """
                    ),
                    {
                        "soles_por_dolar":
                            resultado["soles_por_dolar"],

                        "identificador":
                            resultado["identificador"]
                    }
                )
                .scalar_one()
            )

        registrar_api(
            servicio=(
                ServicioApiEnum.EXCHANGE_RATE
            ),

            operacion=(
                "CONSULTAR_USD_PEN"
            ),

            exitoso=True,

            codigo_http=(
                resultado["codigo_http"]
            ),

            identificador_externo=(
                resultado["identificador"]
            ),

            respuesta={
                "soles_por_dolar":
                    str(
                        resultado["soles_por_dolar"]
                    )
            }
        )

        db.session.commit()

        return jsonify({
            "exito": True,

            "id_tipo_cambio":
                id_tipo_cambio,

            "soles_por_dolar":
                str(
                    resultado["soles_por_dolar"]
                ),

            "actualizado_en":
                resultado.get(
                    "actualizado_en"
                )
        })

    except ErrorExchangeRate as error:

        db.session.rollback()

        try:

            registrar_api(
                servicio=(
                    ServicioApiEnum.EXCHANGE_RATE
                ),

                operacion=(
                    "CONSULTAR_USD_PEN"
                ),

                exitoso=False,

                codigo_http=(
                    error.codigo_http
                ),

                mensaje=str(
                    error
                )
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

        return jsonify({
            "exito": False,
            "mensaje": str(error)
        }), 502

    except Exception as error:

        db.session.rollback()

        bp.logger.exception(
            "ERROR ACTUALIZANDO TIPO DE CAMBIO"
        )

        return jsonify({
            "exito": False,
            "mensaje": (
                "No fue posible guardar el tipo de cambio. "
                "Revise los logs de Render para ver el detalle."
            )
        }), 500


# NUEVA COTIZACION
# =========================================================

@bp.route(
    "/nueva",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "VENDEDOR"
)
def nueva():

    # =====================================================
    # GET
    # =====================================================

    if request.method == "GET":

        # Leer Neon es suficiente para mostrar la pantalla.
        # La consulta a ExchangeRate-API se realiza después,
        # desde el navegador y sin bloquear esta respuesta.
        tipo_cambio = (
            obtener_tipo_cambio_guardado()
        )

        soles_por_dolar = (
            tipo_cambio["soles_por_dolar"]
            if tipo_cambio
            else None
        )

        id_tipo_cambio = (
            tipo_cambio["id_tipo_cambio"]
            if tipo_cambio
            else None
        )

        clientes_recientes = (
            obtener_clientes_recientes()
        )

        productos_recientes = (
            obtener_productos_recientes(
                soles_por_dolar
            )
            if soles_por_dolar is not None
            else []
        )

        return render_template(
            "vendedor/cotizaciones/nueva.html",

            id_tipo_cambio=(
                id_tipo_cambio
            ),

            soles_por_dolar=(
                soles_por_dolar
            ),

            fecha_minima=(
                date.today()
                .isoformat()
            ),

            clientes_recientes=(
                clientes_recientes
            ),

            productos_recientes=(
                productos_recientes
            )
        )

    # =====================================================
    # POST
    # =====================================================

    id_cliente = request.form.get(
        "id_cliente",
        type=int
    )

    id_tipo_cambio = request.form.get(
        "id_tipo_cambio",
        type=int
    )

    moneda = request.form.get(
        "moneda",
        ""
    ).strip().upper()

    fecha_vigencia_texto = (
        request.form.get(
            "fecha_vigencia",
            ""
        ).strip()
    )

    observaciones = (
        request.form.get(
            "observaciones",
            ""
        ).strip()
        or None
    )

    productos_json = request.form.get(
        "productos_json",
        ""
    )

    # =====================================================
    # CLIENTE
    # =====================================================

    cliente = db.session.get(
        Cliente,
        id_cliente
    )

    if (
        cliente is None
        or not cliente.activo
    ):

        flash(
            "Seleccione un cliente válido.",
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    # =====================================================
    # MONEDA
    # =====================================================

    if moneda not in (
        "PEN",
        "USD"
    ):

        flash(
            "Seleccione una moneda válida.",
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    # =====================================================
    # VIGENCIA
    # =====================================================

    try:

        fecha_vigencia = (
            date.fromisoformat(
                fecha_vigencia_texto
            )
        )

    except ValueError:

        flash(
            "Ingrese una fecha de vigencia válida.",
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    if (
        fecha_vigencia
        < date.today()
    ):

        flash(
            (
                "La fecha de vigencia "
                "no puede ser anterior a hoy."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    # =====================================================
    # TIPO DE CAMBIO
    # =====================================================

    fila_tipo_cambio = (
        db.session.execute(
            text(
                """
                SELECT
                    id_tipo_cambio,
                    soles_por_dolar

                FROM tipos_cambio

                WHERE id_tipo_cambio =
                    :id_tipo_cambio
                """
            ),

            {
                "id_tipo_cambio":
                    id_tipo_cambio
            }
        )
        .mappings()
        .first()
    )

    if fila_tipo_cambio is None:

        flash(
            "El tipo de cambio utilizado no existe.",
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    soles_por_dolar = Decimal(
        fila_tipo_cambio[
            "soles_por_dolar"
        ]
    )

    # =====================================================
    # PRODUCTOS
    # =====================================================

    try:

        productos_enviados = json.loads(
            productos_json
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        productos_enviados = []

    if not isinstance(
        productos_enviados,
        list
    ):

        productos_enviados = []

    if not productos_enviados:

        flash(
            (
                "Debe agregar al menos "
                "un producto a la cotización."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    if len(
        productos_enviados
    ) > 100:

        flash(
            (
                "Una cotización no puede contener "
                "más de 100 productos."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    ids_utilizados = set()

    detalles_preparados = []

    for item in productos_enviados:

        try:

            id_producto = int(
                item.get(
                    "id_producto"
                )
            )

        except (
            ValueError,
            TypeError,
            AttributeError
        ):

            flash(
                "Existe un producto inválido.",
                "danger"
            )

            return redirect(
                url_for(
                    "cotizaciones_vendedor.nueva"
                )
            )

        if id_producto in ids_utilizados:

            flash(
                (
                    "Un mismo producto no puede "
                    "estar repetido."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "cotizaciones_vendedor.nueva"
                )
            )

        ids_utilizados.add(
            id_producto
        )

        cantidad = decimal_o_none(
            item.get(
                "cantidad"
            )
        )

        if (
            cantidad is None
            or cantidad <= 0
        ):

            flash(
                "Ingrese cantidades válidas.",
                "danger"
            )

            return redirect(
                url_for(
                    "cotizaciones_vendedor.nueva"
                )
            )

        cantidad = cantidad.quantize(
            Decimal(
                "0.001"
            ),
            rounding=ROUND_HALF_UP
        )

        producto = db.session.get(
            Producto,
            id_producto
        )

        if (
            producto is None
            or not producto.activo
            or producto.precio_venta_actual
            is None
        ):

            flash(
                (
                    "Uno de los productos ya "
                    "no está disponible para cotizar."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "cotizaciones_vendedor.nueva"
                )
            )

        stock = Decimal(
            producto.stock_disponible
            or 0
        )

        if cantidad > stock:

            flash(
                (
                    f"La cantidad solicitada de "
                    f"{producto.nombre} supera "
                    f"el stock disponible ({stock})."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "cotizaciones_vendedor.nueva"
                )
            )

        precio_pen = (
            precio_producto_pen(
                producto,
                soles_por_dolar
            )
        )

        if moneda == "PEN":

            precio_unitario = (
                precio_pen
            )

        else:

            precio_unitario = (
                dos_decimales(
                    precio_pen
                    /
                    soles_por_dolar
                )
            )

        detalles_preparados.append({
            "producto":
                producto,

            "cantidad":
                cantidad,

            "precio_pen":
                precio_pen,

            "precio_unitario":
                precio_unitario
        })

    # =====================================================
    # CREAR COTIZACION
    # =====================================================

    try:

        id_cotizacion = (
            db.session.execute(
                text(
                    """
                    INSERT INTO cotizaciones (
                        numero_cotizacion,
                        id_cliente,
                        id_vendedor,
                        id_tipo_cambio,
                        moneda,
                        tipo_cambio_soles_por_dolar,
                        fecha_emision,
                        fecha_vigencia,
                        estado,
                        observaciones,
                        actualizado_por
                    )
                    VALUES (
                        '',
                        :id_cliente,
                        :id_vendedor,
                        :id_tipo_cambio,
                        :moneda,
                        :tipo_cambio,
                        CURRENT_DATE,
                        :fecha_vigencia,
                        'EMITIDA',
                        :observaciones,
                        :actualizado_por
                    )
                    RETURNING id_cotizacion
                    """
                ),

                {
                    "id_cliente":
                        cliente.id_cliente,

                    "id_vendedor":
                        current_user.id_usuario,

                    "id_tipo_cambio":
                        id_tipo_cambio,

                    "moneda":
                        moneda,

                    "tipo_cambio":
                        soles_por_dolar,

                    "fecha_vigencia":
                        fecha_vigencia,

                    "observaciones":
                        observaciones,

                    "actualizado_por":
                        current_user.id_usuario
                }
            )
            .scalar_one()
        )

        for detalle in detalles_preparados:

            producto = detalle[
                "producto"
            ]

            db.session.execute(
                text(
                    """
                    INSERT INTO detalle_cotizaciones (
                        id_cotizacion,
                        id_producto,
                        codigo_producto,
                        nombre_producto,
                        cantidad,
                        precio_unitario_pen_referencia,
                        precio_unitario
                    )
                    VALUES (
                        :id_cotizacion,
                        :id_producto,
                        :codigo_producto,
                        :nombre_producto,
                        :cantidad,
                        :precio_pen,
                        :precio_unitario
                    )
                    """
                ),

                {
                    "id_cotizacion":
                        id_cotizacion,

                    "id_producto":
                        producto.id_producto,

                    "codigo_producto":
                        producto.codigo_producto,

                    "nombre_producto":
                        producto.nombre,

                    "cantidad":
                        detalle[
                            "cantidad"
                        ],

                    "precio_pen":
                        detalle[
                            "precio_pen"
                        ],

                    "precio_unitario":
                        detalle[
                            "precio_unitario"
                        ]
                }
            )

        db.session.flush()

        valores = (
            db.session.execute(
                text(
                    """
                    SELECT
                        subtotal,
                        total

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
            .one()
        )

        total_con_igv = dos_decimales(
            Decimal(
                valores[
                    "total"
                ]
                or 0
            )
        )

        subtotal_sin_igv = (
            obtener_subtotal_sin_igv(
                total_con_igv
            )
        )

        db.session.execute(
            text(
                """
                UPDATE cotizaciones

                SET
                    subtotal =
                        :subtotal,

                    total =
                        :total

                WHERE id_cotizacion =
                    :id_cotizacion
                """
            ),

            {
                "subtotal":
                    subtotal_sin_igv,

                "total":
                    total_con_igv,

                "id_cotizacion":
                    id_cotizacion
            }
        )

        db.session.flush()

        cotizacion = db.session.get(
            Cotizacion,
            id_cotizacion
        )

        db.session.refresh(
            cotizacion
        )

        nombre_pdf = (
            f"{cotizacion.numero_cotizacion}.pdf"
        )

        token_pdf = (
            crear_token_cotizacion(
                cotizacion.id_cotizacion
            )
        )

        pdf_url = url_for(
            "documentos.cotizacion_pdf",
            token=token_pdf,
            _external=True
        )

        generar_pdf_cotizacion(
            cotizacion.id_cotizacion
        )

        db.session.execute(
            text(
                """
                UPDATE cotizaciones

                SET
                    pdf_nombre_archivo =
                        :nombre,

                    pdf_url =
                        :pdf_url,

                    pdf_generado_en =
                        NOW()

                WHERE id_cotizacion =
                    :id_cotizacion
                """
            ),

            {
                "nombre":
                    nombre_pdf,

                "pdf_url":
                    pdf_url,

                "id_cotizacion":
                    cotizacion.id_cotizacion
            }
        )

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR CREANDO COTIZACION:",
            error_bd
        )

        flash(
            "No fue posible crear la cotización.",
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.nueva"
            )
        )

    flash(
        "Cotización creada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "cotizaciones_vendedor.detalle",

            id_cotizacion=(
                id_cotizacion
            )
        )
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_cotizacion>"
)
@rol_requerido(
    "VENDEDOR"
)
def detalle(
    id_cotizacion
):

    actualizar_vencidas()

    cotizacion = db.get_or_404(
        Cotizacion,
        id_cotizacion
    )

    cliente = db.session.get(
        Cliente,
        cotizacion.id_cliente
    )

    vendedor = db.session.get(
        Usuario,
        cotizacion.id_vendedor
    )

    detalles = (
        db.session.execute(
            db.select(
                DetalleCotizacion
            )
            .where(
                DetalleCotizacion.id_cotizacion
                == cotizacion.id_cotizacion
            )
            .order_by(
                DetalleCotizacion.id_detalle_cotizacion.asc()
            )
        )
        .scalars()
        .all()
    )

    igv = dos_decimales(
        Decimal(
            cotizacion.total
            or 0
        )
        -
        Decimal(
            cotizacion.subtotal
            or 0
        )
    )

    return render_template(
        "vendedor/cotizaciones/detalle.html",

        cotizacion=cotizacion,

        cliente=cliente,

        vendedor=vendedor,

        detalles=detalles,

        nombre_cliente=(
            nombre_cliente(
                cliente
            )
        ),

        nombre_vendedor=(
            nombre_usuario(
                vendedor
            )
        ),

        moneda=(
            texto_enum(
                cotizacion.moneda
            )
        ),

        estado=(
            texto_enum(
                cotizacion.estado
            )
        ),

        igv=igv
    )


# =========================================================
# ENVIAR POR CORREO
# =========================================================

@bp.post(
    "/<int:id_cotizacion>/enviar-correo"
)
@rol_requerido(
    "VENDEDOR"
)
def enviar_cotizacion_correo(
    id_cotizacion
):

    cotizacion = db.get_or_404(
        Cotizacion,
        id_cotizacion
    )

    cliente = db.session.get(
        Cliente,
        cotizacion.id_cliente
    )

    if not cliente.correo:

        flash(
            (
                "El cliente no tiene un "
                "correo electrónico registrado."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.detalle",

                id_cotizacion=(
                    cotizacion.id_cotizacion
                )
            )
        )

    asunto = (
        f"Cotización ROPUSAC "
        f"{cotizacion.numero_cotizacion}"
    )

    cuerpo = (
        f"Estimado(a) {nombre_cliente(cliente)},\n\n"
        f"Adjuntamos la cotización "
        f"{cotizacion.numero_cotizacion}.\n\n"
        f"Fecha de vigencia: "
        f"{cotizacion.fecha_vigencia.strftime('%d/%m/%Y')}.\n\n"
        "Saludos,\n"
        "ROPUSAC"
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

                WHERE id_cotizacion =
                    :id_cotizacion

                  AND tipo_documento =
                    'COTIZACION'
                """
            ),

            {
                "id_cotizacion":
                    cotizacion.id_cotizacion
            }
        )
        .scalar_one()
    )

    try:

        pdf = generar_pdf_cotizacion(
            cotizacion.id_cotizacion
        )

        enviar_correo(
            destinatario=(
                cliente.correo
            ),

            asunto=asunto,

            cuerpo=cuerpo,

            archivo=pdf,

            nombre_archivo=(
                cotizacion.pdf_nombre_archivo
                or
                f"{cotizacion.numero_cotizacion}.pdf"
            )
        )

    except ErrorCorreo as error:

        try:

            db.session.execute(
                text(
                    """
                    INSERT INTO envios_correo (
                        tipo_documento,
                        id_cotizacion,
                        destinatario,
                        asunto,
                        estado,
                        numero_intento,
                        mensaje_error,
                        enviado_por
                    )
                    VALUES (
                        'COTIZACION',
                        :id_cotizacion,
                        :destinatario,
                        :asunto,
                        'ERROR',
                        :numero_intento,
                        :mensaje_error,
                        :enviado_por
                    )
                    """
                ),

                {
                    "id_cotizacion":
                        cotizacion.id_cotizacion,

                    "destinatario":
                        cliente.correo,

                    "asunto":
                        asunto,

                    "numero_intento":
                        numero_intento,

                    "mensaje_error":
                        str(
                            error
                        ),

                    "enviado_por":
                        current_user.id_usuario
                }
            )

            registrar_api(
                servicio=(
                    ServicioApiEnum.SMTP
                ),

                operacion=(
                    "ENVIAR_COTIZACION"
                ),

                exitoso=False,

                mensaje=str(
                    error
                ),

                id_entidad=(
                    cotizacion.id_cotizacion
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
                "cotizaciones_vendedor.detalle",

                id_cotizacion=(
                    cotizacion.id_cotizacion
                )
            )
        )

    except Exception as error:

        print(
            "ERROR PREPARANDO PDF:",
            error
        )

        flash(
            (
                "No fue posible preparar "
                "la cotización para el envío."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_vendedor.detalle",

                id_cotizacion=(
                    cotizacion.id_cotizacion
                )
            )
        )

    try:

        db.session.execute(
            text(
                """
                INSERT INTO envios_correo (
                    tipo_documento,
                    id_cotizacion,
                    destinatario,
                    asunto,
                    estado,
                    numero_intento,
                    enviado_por,
                    enviado_en
                )
                VALUES (
                    'COTIZACION',
                    :id_cotizacion,
                    :destinatario,
                    :asunto,
                    'ENVIADO',
                    :numero_intento,
                    :enviado_por,
                    NOW()
                )
                """
            ),

            {
                "id_cotizacion":
                    cotizacion.id_cotizacion,

                "destinatario":
                    cliente.correo,

                "asunto":
                    asunto,

                "numero_intento":
                    numero_intento,

                "enviado_por":
                    current_user.id_usuario
            }
        )

        db.session.execute(
            text(
                """
                UPDATE cotizaciones

                SET
                    estado =
                        CASE

                            WHEN estado =
                                'EMITIDA'

                            THEN
                                'ENVIADA'

                            ELSE
                                estado

                        END,

                    enviada_correo_en =
                        NOW(),

                    actualizado_por =
                        :usuario

                WHERE id_cotizacion =
                    :id_cotizacion
                """
            ),

            {
                "usuario":
                    current_user.id_usuario,

                "id_cotizacion":
                    cotizacion.id_cotizacion
            }
        )

        registrar_api(
            servicio=(
                ServicioApiEnum.SMTP
            ),

            operacion=(
                "ENVIAR_COTIZACION"
            ),

            exitoso=True,

            mensaje=(
                "Cotización enviada correctamente."
            ),

            id_entidad=(
                cotizacion.id_cotizacion
            )
        )

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR REGISTRANDO ENVIO SMTP:",
            error_bd
        )

    flash(
        (
            "Cotización enviada al correo "
            f"{cliente.correo}."
        ),
        "success"
    )

    return redirect(
        url_for(
            "cotizaciones_vendedor.detalle",

            id_cotizacion=(
                cotizacion.id_cotizacion
            )
        )
    )