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

from sqlalchemy import (
    func,
    or_,
    text
)

from app.extensiones import db

from app.modelos import (
    Cliente,
    Cotizacion,
    DetalleCotizacion,
    Rol,
    Usuario
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "cotizaciones_admin",
    __name__,
    url_prefix="/administrador/cotizaciones"
)


# =========================================================
# CONFIGURACION
# =========================================================

COTIZACIONES_POR_PAGINA = 20


# =========================================================
# AUXILIARES
# =========================================================

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

    if cliente is None:
        return ""

    if isinstance(
        cliente,
        dict
    ):

        razon_social = cliente.get(
            "razon_social"
        )

        nombres = cliente.get(
            "nombres"
        )

        apellidos = cliente.get(
            "apellidos"
        )

    else:

        razon_social = (
            cliente.razon_social
        )

        nombres = (
            cliente.nombres
        )

        apellidos = (
            cliente.apellidos
        )

    if razon_social:
        return razon_social

    return " ".join(
        parte
        for parte in [
            nombres,
            apellidos
        ]
        if parte
    ).strip()


def nombre_usuario(
    usuario
):

    if usuario is None:
        return ""

    if isinstance(
        usuario,
        dict
    ):

        nombres = usuario.get(
            "nombres"
        )

        apellidos = usuario.get(
            "apellidos"
        )

    else:

        nombres = (
            usuario.nombres
        )

        apellidos = (
            usuario.apellidos
        )

    return " ".join(
        parte
        for parte in [
            nombres,
            apellidos
        ]
        if parte
    ).strip()


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
            "ERROR ACTUALIZANDO COTIZACIONES VENCIDAS:",
            error
        )


# =========================================================
# LISTAR
#
# OPTIMIZADO PARA RENDER:
#
# - PAGINACION
# - SOLO COLUMNAS NECESARIAS
# - NO CARGA TODAS LAS FILAS A MEMORIA
# - NO CREA OBJETOS ORM COMPLETOS
# =========================================================

@bp.get("/")
@rol_requerido(
    "ADMINISTRADOR"
)
def lista():

    actualizar_vencidas()

    # =====================================================
    # FILTROS
    # =====================================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    estado = request.args.get(
        "estado",
        ""
    ).strip()

    id_vendedor = request.args.get(
        "id_vendedor",
        type=int
    )

    pagina = request.args.get(
        "pagina",
        1,
        type=int
    )

    if pagina < 1:
        pagina = 1

    # =====================================================
    # CONDICIONES
    # =====================================================

    condiciones = []

    # =====================================================
    # BUSQUEDA
    # =====================================================

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        condiciones.append(
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

        condiciones.append(
            Cotizacion.estado
            == estado
        )

    # =====================================================
    # VENDEDOR
    # =====================================================

    if id_vendedor:

        condiciones.append(
            Cotizacion.id_vendedor
            == id_vendedor
        )

    # =====================================================
    # CONTAR REGISTROS
    #
    # SOLO COUNT.
    # NO TRAEMOS COTIZACIONES A PYTHON.
    # =====================================================

    consulta_total = (
        db.select(
            func.count(
                Cotizacion.id_cotizacion
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

    if condiciones:

        consulta_total = (
            consulta_total.where(
                *condiciones
            )
        )

    total_registros = (
        db.session.scalar(
            consulta_total
        )
        or 0
    )

    # =====================================================
    # TOTAL PAGINAS
    # =====================================================

    total_paginas = max(
        1,
        (
            total_registros
            +
            COTIZACIONES_POR_PAGINA
            -
            1
        )
        //
        COTIZACIONES_POR_PAGINA
    )

    # =====================================================
    # SI PIDEN UNA PAGINA QUE YA NO EXISTE
    # =====================================================

    if pagina > total_paginas:
        pagina = total_paginas

    offset = (
        pagina - 1
    ) * COTIZACIONES_POR_PAGINA

    # =====================================================
    # CONSULTA PRINCIPAL
    #
    # IMPORTANTE:
    #
    # NO HACEMOS:
    #
    # select(Cotizacion, Cliente, Usuario)
    #
    # SOLO TRAEMOS LOS CAMPOS QUE SE MUESTRAN.
    # =====================================================

    consulta = (
        db.select(

            # =============================================
            # COTIZACION
            # =============================================

            Cotizacion.id_cotizacion.label(
                "id_cotizacion"
            ),

            Cotizacion.numero_cotizacion.label(
                "numero_cotizacion"
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

            Cotizacion.subtotal.label(
                "subtotal"
            ),

            Cotizacion.total.label(
                "total"
            ),

            Cotizacion.total_equivalente.label(
                "total_equivalente"
            ),

            Cotizacion.id_vendedor.label(
                "id_vendedor"
            ),

            Cotizacion.pdf_url.label(
                "pdf_url"
            ),

            Cotizacion.pdf_nombre_archivo.label(
                "pdf_nombre_archivo"
            ),

            Cotizacion.creado_en.label(
                "creado_en"
            ),

            # =============================================
            # CLIENTE
            # =============================================

            Cliente.razon_social.label(
                "cliente_razon_social"
            ),

            Cliente.nombres.label(
                "cliente_nombres"
            ),

            Cliente.apellidos.label(
                "cliente_apellidos"
            ),

            Cliente.numero_documento.label(
                "cliente_documento"
            ),

            # =============================================
            # VENDEDOR
            # =============================================

            Usuario.nombres.label(
                "vendedor_nombres"
            ),

            Usuario.apellidos.label(
                "vendedor_apellidos"
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

    if condiciones:

        consulta = (
            consulta.where(
                *condiciones
            )
        )

    consulta = (
        consulta
        .order_by(
            Cotizacion.creado_en.desc(),
            Cotizacion.id_cotizacion.desc()
        )
        .offset(
            offset
        )
        .limit(
            COTIZACIONES_POR_PAGINA
        )
    )

    # =====================================================
    # SOLO MAXIMO 20 FILAS
    # =====================================================

    filas = (
        db.session.execute(
            consulta
        )
        .mappings()
        .all()
    )

    # =====================================================
    # PREPARAR DATOS LIGEROS
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

                "fecha_emision":
                    fila[
                        "fecha_emision"
                    ],

                "fecha_vigencia":
                    fila[
                        "fecha_vigencia"
                    ],

                "estado":
                    fila[
                        "estado_cotizacion"
                    ],

                "moneda":
                    fila[
                        "moneda"
                    ],

                "subtotal":
                    fila[
                        "subtotal"
                    ],

                "total":
                    fila[
                        "total"
                    ],

                "total_equivalente":
                    fila[
                        "total_equivalente"
                    ],

                "id_vendedor":
                    fila[
                        "id_vendedor"
                    ],

                "pdf_url":
                    fila[
                        "pdf_url"
                    ],

                "pdf_nombre_archivo":
                    fila[
                        "pdf_nombre_archivo"
                    ],

                "creado_en":
                    fila[
                        "creado_en"
                    ]
            },

            "cliente":
                cliente,

            "cliente_documento":
                fila[
                    "cliente_documento"
                ],

            "vendedor":
                vendedor
        })

    # =====================================================
    # VENDEDORES
    #
    # ANTES:
    #
    # - cargábamos todos los Usuario ORM
    # - cargábamos relación rol
    # - filtrábamos después en Python
    #
    # AHORA:
    #
    # PostgreSQL devuelve únicamente vendedores.
    # =====================================================

    filas_vendedores = (
        db.session.execute(
            db.select(
                Usuario.id_usuario,
                Usuario.nombres,
                Usuario.apellidos
            )
            .join(
                Rol,
                Usuario.id_rol
                == Rol.id_rol
            )
            .where(
                Usuario.activo.is_(
                    True
                ),

                Rol.codigo
                == "VENDEDOR"
            )
            .order_by(
                Usuario.nombres.asc(),
                Usuario.apellidos.asc()
            )
        )
        .mappings()
        .all()
    )

    vendedores = [
        {
            "id_usuario":
                fila[
                    "id_usuario"
                ],

            "nombres":
                fila[
                    "nombres"
                ],

            "apellidos":
                fila[
                    "apellidos"
                ]
        }
        for fila in filas_vendedores
    ]

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
        "ANULADA"
    ]

    return render_template(
        "administrador/cotizaciones/lista.html",

        cotizaciones=(
            cotizaciones
        ),

        vendedores=(
            vendedores
        ),

        estados=(
            estados
        ),

        buscar=buscar,

        estado=estado,

        id_vendedor=id_vendedor,

        texto_enum=texto_enum,

        nombre_usuario=nombre_usuario,

        pagina=pagina,

        total_paginas=(
            total_paginas
        ),

        total_registros=(
            total_registros
        ),

        por_pagina=(
            COTIZACIONES_POR_PAGINA
        )
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_cotizacion>"
)
@rol_requerido(
    "ADMINISTRADOR"
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

    return render_template(
        "administrador/cotizaciones/detalle.html",

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

        estado=(
            texto_enum(
                cotizacion.estado
            )
        ),

        moneda=(
            texto_enum(
                cotizacion.moneda
            )
        )
    )


# =========================================================
# DESCARGAR PDF
#
# NO HACEMOS requests.get() A NUESTRA PROPIA APP.
#
# EN GUNICORN SYNC ESO PUEDE GENERAR BLOQUEOS:
#
# solicitud descargar
#      ↓
# Render intenta llamar nuevamente a Render
#      ↓
# único worker ocupado esperando esa respuesta
#
# GENERAMOS EL PDF DIRECTAMENTE.
# =========================================================

@bp.get(
    "/<int:id_cotizacion>/descargar"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def descargar(
    id_cotizacion
):

    cotizacion = db.session.get(
        Cotizacion,
        id_cotizacion
    )

    if cotizacion is None:

        abort(
            404
        )

    # =====================================================
    # IMPORTACION LOCAL
    #
    # REPORTLAB SOLO SE CARGA SI REALMENTE
    # SE DESCARGA UN PDF.
    # =====================================================

    try:

        from app.servicios.pdf_cotizacion import (
            generar_pdf_cotizacion
        )

        contenido = (
            generar_pdf_cotizacion(
                id_cotizacion
            )
        )

    except Exception as error:

        print(
            "ERROR GENERANDO COTIZACION PDF:",
            error
        )

        flash(
            (
                "No fue posible generar "
                "el PDF de la cotización."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "cotizaciones_admin.detalle",
                id_cotizacion=(
                    id_cotizacion
                )
            )
        )

    nombre_archivo = (
        cotizacion.pdf_nombre_archivo
        or
        f"{cotizacion.numero_cotizacion}.pdf"
    )

    return Response(
        contenido,
        status=200,
        headers={
            "Content-Type":
                "application/pdf",

            "Content-Disposition":
                (
                    f'attachment; '
                    f'filename="{nombre_archivo}"'
                )
        }
    )