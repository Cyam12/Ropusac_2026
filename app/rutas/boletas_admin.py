import requests

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for
)

from sqlalchemy import or_

from app.extensiones import db

from app.modelos import (
    Boleta,
    Cotizacion,
    DetalleVenta,
    Rol,
    Usuario,
    Venta
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "boletas_admin",
    __name__,
    url_prefix="/administrador/boletas"
)


# =========================================================
# CONFIGURACION
# =========================================================

BOLETAS_POR_PAGINA = 20


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


def obtener_valor(
    objeto,
    campo
):

    if objeto is None:
        return None

    if isinstance(
        objeto,
        dict
    ):

        return objeto.get(
            campo
        )

    return getattr(
        objeto,
        campo,
        None
    )


def nombre_usuario(
    usuario
):

    if usuario is None:
        return ""

    nombres = obtener_valor(
        usuario,
        "nombres"
    )

    apellidos = obtener_valor(
        usuario,
        "apellidos"
    )

    return " ".join(
        parte
        for parte in [
            nombres,
            apellidos
        ]
        if parte
    ).strip()


def numero_boleta(
    boleta
):

    serie = obtener_valor(
        boleta,
        "serie"
    )

    numero = obtener_valor(
        boleta,
        "numero"
    )

    id_boleta = obtener_valor(
        boleta,
        "id_boleta"
    )

    if (
        serie
        and numero
    ):

        return (
            f"{serie}-"
            f"{numero}"
        )

    return (
        f"BOLETA-"
        f"{id_boleta}"
    )


# =========================================================
# LISTAR
#
# OPTIMIZADO PARA RENDER:
#
# - 20 BOLETAS POR PAGINA
# - SOLO COLUMNAS NECESARIAS
# - NO CREA OBJETOS ORM COMPLETOS
# - NO CARGA TODAS LAS BOLETAS EN RAM
# =========================================================

@bp.get("/")
@rol_requerido(
    "ADMINISTRADOR"
)
def lista():

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
    # CONSULTA LIGERA
    #
    # SOLO TRAEMOS LOS CAMPOS QUE USA lista.html
    # =====================================================

    consulta = (
        db.select(

            # =================================================
            # BOLETA
            # =================================================

            Boleta.id_boleta.label(
                "id_boleta"
            ),

            Boleta.estado.label(
                "estado_boleta"
            ),

            Boleta.serie.label(
                "serie"
            ),

            Boleta.numero.label(
                "numero"
            ),

            Boleta.fecha_emision.label(
                "fecha_emision"
            ),

            Boleta.moneda.label(
                "moneda"
            ),

            Boleta.total.label(
                "total"
            ),

            Boleta.cliente_nombre.label(
                "cliente_nombre"
            ),

            Boleta.cliente_numero_documento.label(
                "cliente_numero_documento"
            ),

            Boleta.enlace_pdf.label(
                "enlace_pdf"
            ),

            # =================================================
            # VENTA
            # =================================================

            Venta.numero_venta.label(
                "numero_venta"
            ),

            # =================================================
            # VENDEDOR
            # =================================================

            Usuario.nombres.label(
                "vendedor_nombres"
            ),

            Usuario.apellidos.label(
                "vendedor_apellidos"
            )
        )
        .select_from(
            Boleta
        )
        .join(
            Venta,
            Boleta.id_venta
            == Venta.id_venta
        )
        .join(
            Usuario,
            Venta.id_vendedor
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
                Boleta.serie.ilike(
                    patron
                ),

                Boleta.numero.ilike(
                    patron
                ),

                Boleta.cliente_nombre.ilike(
                    patron
                ),

                Boleta.cliente_numero_documento.ilike(
                    patron
                ),

                Venta.numero_venta.ilike(
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
            Boleta.estado
            == estado
        )

    # =====================================================
    # VENDEDOR
    # =====================================================

    if id_vendedor:

        consulta = consulta.where(
            Venta.id_vendedor
            == id_vendedor
        )

    # =====================================================
    # PAGINACION
    #
    # 20 VISIBLES
    # + 1 PARA SABER SI EXISTE SIGUIENTE PAGINA
    #
    # ORDENAMOS POR PK.
    # =====================================================

    offset = (
        pagina - 1
    ) * BOLETAS_POR_PAGINA

    consulta = (
        consulta
        .order_by(
            Boleta.id_boleta.desc()
        )
        .offset(
            offset
        )
        .limit(
            BOLETAS_POR_PAGINA
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
    # SIGUIENTE PAGINA
    # =====================================================

    hay_siguiente = (
        len(
            filas
        )
        >
        BOLETAS_POR_PAGINA
    )

    filas = filas[
        :BOLETAS_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # PREPARAR DATOS
    # =====================================================

    boletas = []

    for fila in filas:

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

        boletas.append({

            "boleta": {

                "id_boleta":
                    fila[
                        "id_boleta"
                    ],

                "estado":
                    texto_enum(
                        fila[
                            "estado_boleta"
                        ]
                    ),

                "serie":
                    fila[
                        "serie"
                    ],

                "numero":
                    fila[
                        "numero"
                    ],

                "fecha_emision":
                    fila[
                        "fecha_emision"
                    ],

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

                "cliente_nombre":
                    fila[
                        "cliente_nombre"
                    ],

                "cliente_numero_documento":
                    fila[
                        "cliente_numero_documento"
                    ],

                "enlace_pdf":
                    fila[
                        "enlace_pdf"
                    ]
            },

            "venta": {

                "numero_venta":
                    fila[
                        "numero_venta"
                    ]
            },

            "vendedor":
                vendedor
        })

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not boletas
    ):

        return redirect(
            url_for(
                "boletas_admin.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar,

                estado=estado,

                id_vendedor=(
                    id_vendedor
                    or ""
                )
            )
        )

    # =====================================================
    # VENDEDORES
    #
    # ANTES:
    #
    # TODOS LOS USUARIOS ACTIVOS
    #       ↓
    # OBJETOS ORM
    #       ↓
    # FILTRAR EN PYTHON
    #
    # AHORA:
    #
    # SOLO VENDEDORES DESDE POSTGRESQL.
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

    vendedores = []

    for fila in filas_vendedores:

        vendedores.append({

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
                ],

            "nombre_mostrar":
                " ".join(
                    parte
                    for parte in [
                        fila[
                            "nombres"
                        ],

                        fila[
                            "apellidos"
                        ]
                    ]
                    if parte
                ).strip()
        })

    # =====================================================
    # ESTADOS
    # =====================================================

    estados = [
        "PENDIENTE",
        "GENERADA",
        "ERROR",
        "ANULADA"
    ]

    return render_template(
        "administrador/boletas/lista.html",

        boletas=boletas,

        vendedores=vendedores,

        estados=estados,

        buscar=buscar,

        estado=estado,

        id_vendedor=id_vendedor,

        pagina=pagina,

        hay_anterior=(
            hay_anterior
        ),

        hay_siguiente=(
            hay_siguiente
        ),

        por_pagina=(
            BOLETAS_POR_PAGINA
        ),

        texto_enum=texto_enum,

        numero_boleta=numero_boleta,

        nombre_usuario=nombre_usuario
    )


# =========================================================
# DETALLE
#
# SOLO ES UNA BOLETA, POR LO QUE AQUI SI PODEMOS
# TRABAJAR CON LOS OBJETOS ORM NORMALES.
# =========================================================

@bp.get(
    "/<int:id_boleta>"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def detalle(
    id_boleta
):

    boleta = db.get_or_404(
        Boleta,
        id_boleta
    )

    venta = db.session.get(
        Venta,
        boleta.id_venta
    )

    if venta is None:

        abort(
            404
        )

    vendedor = db.session.get(
        Usuario,
        venta.id_vendedor
    )

    cotizacion = db.session.get(
        Cotizacion,
        venta.id_cotizacion
    )

    detalles = (
        db.session.execute(
            db.select(
                DetalleVenta
            )
            .where(
                DetalleVenta.id_venta
                == venta.id_venta
            )
            .order_by(
                DetalleVenta.id_detalle_venta.asc()
            )
        )
        .scalars()
        .all()
    )

    return render_template(
        "administrador/boletas/detalle.html",

        boleta=boleta,

        venta=venta,

        vendedor=vendedor,

        cotizacion=cotizacion,

        detalles=detalles,

        estado=texto_enum(
            boleta.estado
        ),

        moneda=texto_enum(
            boleta.moneda
        ),

        nombre_vendedor=(
            nombre_usuario(
                vendedor
            )
        ),

        numero_boleta=(
            numero_boleta(
                boleta
            )
        )
    )


# =========================================================
# DESCARGAR DOCUMENTO
#
# OPTIMIZADO PARA MEMORIA:
#
# ANTES:
#
# respuesta.content
#
# ESO CARGABA TODO EL PDF/XML/ZIP EN RAM.
#
# AHORA:
#
# NUBEFACT
#   ↓
# STREAM
#   ↓
# USUARIO
#
# SIN GUARDAR TODO EL ARCHIVO EN MEMORIA.
# =========================================================

@bp.get(
    "/<int:id_boleta>/descargar/<tipo>"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def descargar(
    id_boleta,
    tipo
):

    boleta = db.get_or_404(
        Boleta,
        id_boleta
    )

    documentos = {

        "pdf": {

            "url":
                boleta.enlace_pdf,

            "extension":
                "pdf",

            "content_type":
                "application/pdf"
        },

        "xml": {

            "url":
                boleta.enlace_xml,

            "extension":
                "xml",

            "content_type":
                "application/xml"
        },

        "cdr": {

            "url":
                boleta.enlace_cdr,

            "extension":
                "zip",

            "content_type":
                "application/zip"
        }
    }

    documento = documentos.get(
        tipo.lower()
    )

    if documento is None:

        abort(
            404
        )

    if not documento[
        "url"
    ]:

        flash(
            (
                "El documento solicitado "
                "no está disponible."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "boletas_admin.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    # =====================================================
    # CONEXION STREAM
    # =====================================================

    try:

        respuesta = requests.get(
            documento[
                "url"
            ],

            timeout=(
                10,
                30
            ),

            stream=True
        )

        respuesta.raise_for_status()

    except requests.RequestException as error:

        print(
            "ERROR DESCARGANDO DOCUMENTO NUBEFACT:",
            error
        )

        flash(
            (
                "No fue posible descargar "
                "el documento."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "boletas_admin.detalle",

                id_boleta=(
                    id_boleta
                )
            )
        )

    # =====================================================
    # NOMBRE
    # =====================================================

    nombre = numero_boleta(
        boleta
    )

    # =====================================================
    # GENERADOR
    #
    # ENVIA BLOQUES DE 64 KB.
    # =====================================================

    def generar_archivo():

        try:

            for bloque in respuesta.iter_content(
                chunk_size=(
                    64
                    * 1024
                )
            ):

                if bloque:

                    yield bloque

        finally:

            respuesta.close()

    # =====================================================
    # RESPUESTA
    # =====================================================

    return Response(
        stream_with_context(
            generar_archivo()
        ),

        status=200,

        headers={

            "Content-Type":
                respuesta.headers.get(
                    "Content-Type",
                    documento[
                        "content_type"
                    ]
                ),

            "Content-Disposition":
                (
                    f'attachment; '
                    f'filename="{nombre}.'
                    f'{documento["extension"]}"'
                )
        }
    )