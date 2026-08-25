from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    url_for
)

from sqlalchemy import or_

from app.extensiones import db

from app.modelos import (
    ImagenProducto,
    Producto,
    Proveedor
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "productos_vendedor",
    __name__,
    url_prefix="/vendedor/productos"
)


# =========================================================
# CONFIGURACION
# =========================================================

PRODUCTOS_POR_PAGINA = 12


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


# =========================================================
# OBTENER IMAGENES PRINCIPALES
#
# SOLO CONSULTA:
#
# - ID PRODUCTO
# - URL IMAGEN
#
# Y SOLO PARA LOS PRODUCTOS DE LA PAGINA ACTUAL.
# =========================================================

def obtener_imagenes_principales(
    ids_productos
):

    if not ids_productos:
        return {}

    filas = (
        db.session.execute(
            db.select(
                ImagenProducto.id_producto,
                ImagenProducto.url_imagen
            )
            .where(
                ImagenProducto.id_producto.in_(
                    ids_productos
                ),

                ImagenProducto.es_principal.is_(
                    True
                ),

                ImagenProducto.activa.is_(
                    True
                )
            )
            .order_by(
                ImagenProducto.id_imagen_producto.asc()
            )
        )
        .mappings()
        .all()
    )

    imagenes = {}

    for fila in filas:

        id_producto = fila[
            "id_producto"
        ]

        # =================================================
        # SI POR ALGUN MOTIVO EXISTE MAS DE UNA
        # PRINCIPAL, CONSERVAMOS SOLO LA PRIMERA.
        # =================================================

        if id_producto not in imagenes:

            imagenes[
                id_producto
            ] = fila[
                "url_imagen"
            ]

    return imagenes


# =========================================================
# LISTAR CATALOGO
#
# OPTIMIZADO PARA RENDER:
#
# - 12 PRODUCTOS POR PAGINA
# - SOLO COLUMNAS NECESARIAS
# - SIN OBJETOS ORM COMPLETOS
# - IMAGENES SOLO DE LA PAGINA ACTUAL
# - PROVEEDORES EN CONSULTA LIGERA
# =========================================================

@bp.get("/")
@rol_requerido(
    "VENDEDOR"
)
def lista():

    # =====================================================
    # FILTROS
    # =====================================================

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    categoria = request.args.get(
        "categoria",
        ""
    ).strip()

    id_proveedor = request.args.get(
        "id_proveedor",
        type=int
    )

    disponibilidad = request.args.get(
        "disponibilidad",
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
    # PRODUCTOS DISPONIBLES PARA VENTA
    #
    # SOLO CAMPOS NECESARIOS PARA lista.html
    # =====================================================

    consulta = (
        db.select(

            # =================================================
            # PRODUCTO
            # =================================================

            Producto.id_producto.label(
                "id_producto"
            ),

            Producto.codigo_producto.label(
                "codigo_producto"
            ),

            Producto.nombre.label(
                "nombre"
            ),

            Producto.categoria.label(
                "categoria"
            ),

            Producto.marca.label(
                "marca"
            ),

            Producto.modelo.label(
                "modelo"
            ),

            Producto.unidad_medida.label(
                "unidad_medida"
            ),

            Producto.precio_venta_actual.label(
                "precio_venta_actual"
            ),

            Producto.moneda_precio.label(
                "moneda_precio"
            ),

            Producto.stock_disponible.label(
                "stock_disponible"
            ),

            # =================================================
            # PROVEEDOR
            # =================================================

            Proveedor.id_proveedor.label(
                "proveedor_id"
            ),

            Proveedor.razon_social.label(
                "proveedor_razon_social"
            )
        )
        .select_from(
            Producto
        )
        .join(
            Proveedor,
            Producto.id_proveedor
            == Proveedor.id_proveedor
        )
        .where(
            Producto.activo.is_(
                True
            ),

            Proveedor.activo.is_(
                True
            ),

            Producto.precio_venta_actual.is_not(
                None
            )
        )
    )

    # =====================================================
    # BUSCADOR
    # =====================================================

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        consulta = consulta.where(
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
                ),

                Proveedor.razon_social.ilike(
                    patron
                )
            )
        )

    # =====================================================
    # CATEGORIA
    # =====================================================

    if categoria:

        consulta = consulta.where(
            Producto.categoria
            == categoria
        )

    # =====================================================
    # PROVEEDOR
    # =====================================================

    if id_proveedor:

        consulta = consulta.where(
            Producto.id_proveedor
            == id_proveedor
        )

    # =====================================================
    # STOCK
    # =====================================================

    if (
        disponibilidad
        == "CON_STOCK"
    ):

        consulta = consulta.where(
            Producto.stock_disponible
            > 0
        )

    elif (
        disponibilidad
        == "SIN_STOCK"
    ):

        consulta = consulta.where(
            Producto.stock_disponible
            <= 0
        )

    # =====================================================
    # PAGINACION
    #
    # 12 PRODUCTOS VISIBLES
    # + 1 PARA SABER SI EXISTE PAGINA SIGUIENTE
    #
    # USAMOS LA PK PARA EVITAR ORDENAR TODA
    # LA TABLA POR NOMBRE.
    # =====================================================

    offset = (
        pagina - 1
    ) * PRODUCTOS_POR_PAGINA

    consulta = (
        consulta
        .order_by(
            Producto.id_producto.desc()
        )
        .offset(
            offset
        )
        .limit(
            PRODUCTOS_POR_PAGINA
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
        PRODUCTOS_POR_PAGINA
    )

    filas = filas[
        :PRODUCTOS_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not filas
    ):

        return redirect(
            url_for(
                "productos_vendedor.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar,

                categoria=categoria,

                id_proveedor=(
                    id_proveedor
                    or ""
                ),

                disponibilidad=(
                    disponibilidad
                )
            )
        )

    # =====================================================
    # IDS SOLO DE ESTA PAGINA
    # =====================================================

    ids_productos = [
        fila[
            "id_producto"
        ]
        for fila in filas
    ]

    # =====================================================
    # IMAGENES SOLO PARA MAXIMO 12 PRODUCTOS
    # =====================================================

    imagenes = (
        obtener_imagenes_principales(
            ids_productos
        )
    )

    # =====================================================
    # PREPARAR PRODUCTOS
    # =====================================================

    productos = []

    for fila in filas:

        producto = {

            "id_producto":
                fila[
                    "id_producto"
                ],

            "codigo_producto":
                fila[
                    "codigo_producto"
                ],

            "nombre":
                fila[
                    "nombre"
                ],

            "categoria":
                fila[
                    "categoria"
                ],

            "marca":
                fila[
                    "marca"
                ],

            "modelo":
                fila[
                    "modelo"
                ],

            "unidad_medida":
                fila[
                    "unidad_medida"
                ],

            "precio_venta_actual":
                fila[
                    "precio_venta_actual"
                ],

            "moneda_precio":
                texto_enum(
                    fila[
                        "moneda_precio"
                    ]
                ),

            "stock_disponible":
                fila[
                    "stock_disponible"
                ]
        }

        proveedor = {

            "id_proveedor":
                fila[
                    "proveedor_id"
                ],

            "razon_social":
                fila[
                    "proveedor_razon_social"
                ]
        }

        productos.append({

            "producto":
                producto,

            "proveedor":
                proveedor,

            "imagen_url":
                imagenes.get(
                    fila[
                        "id_producto"
                    ]
                )
        })

    # =====================================================
    # PROVEEDORES
    #
    # SOLO ID + RAZON SOCIAL.
    # =====================================================

    filas_proveedores = (
        db.session.execute(
            db.select(
                Proveedor.id_proveedor,
                Proveedor.razon_social
            )
            .where(
                Proveedor.activo.is_(
                    True
                )
            )
            .order_by(
                Proveedor.razon_social.asc()
            )
        )
        .mappings()
        .all()
    )

    proveedores = [
        {
            "id_proveedor":
                fila[
                    "id_proveedor"
                ],

            "razon_social":
                fila[
                    "razon_social"
                ]
        }
        for fila in filas_proveedores
    ]

    # =====================================================
    # CATEGORIAS EXISTENTES
    #
    # ESTA CONSULTA SOLO DEVUELVE STRINGS.
    # =====================================================

    categorias = (
        db.session.execute(
            db.select(
                Producto.categoria
            )
            .where(
                Producto.activo.is_(
                    True
                ),

                Producto.precio_venta_actual.is_not(
                    None
                ),

                Producto.categoria.is_not(
                    None
                )
            )
            .distinct()
            .order_by(
                Producto.categoria.asc()
            )
        )
        .scalars()
        .all()
    )

    return render_template(
        "vendedor/productos/lista.html",

        productos=productos,

        proveedores=proveedores,

        categorias=categorias,

        buscar=buscar,

        categoria=categoria,

        id_proveedor=id_proveedor,

        disponibilidad=disponibilidad,

        pagina=pagina,

        hay_anterior=(
            hay_anterior
        ),

        hay_siguiente=(
            hay_siguiente
        ),

        por_pagina=(
            PRODUCTOS_POR_PAGINA
        )
    )


# =========================================================
# DETALLE PRODUCTO
#
# AQUI SOLO SE CONSULTA UN PRODUCTO,
# POR LO QUE PODEMOS CONSERVAR OBJETOS ORM.
# =========================================================

@bp.get(
    "/<int:id_producto>"
)
@rol_requerido(
    "VENDEDOR"
)
def detalle(
    id_producto
):

    fila = (
        db.session.execute(
            db.select(
                Producto,
                Proveedor
            )
            .join(
                Proveedor,
                Producto.id_proveedor
                == Proveedor.id_proveedor
            )
            .where(
                Producto.id_producto
                == id_producto,

                Producto.activo.is_(
                    True
                ),

                Proveedor.activo.is_(
                    True
                ),

                Producto.precio_venta_actual.is_not(
                    None
                )
            )
        )
        .first()
    )

    if fila is None:

        abort(
            404
        )

    producto, proveedor = (
        fila
    )

    imagen = (
        db.session.execute(
            db.select(
                ImagenProducto
            )
            .where(
                ImagenProducto.id_producto
                == producto.id_producto,

                ImagenProducto.es_principal.is_(
                    True
                ),

                ImagenProducto.activa.is_(
                    True
                )
            )
            .order_by(
                ImagenProducto.id_imagen_producto.asc()
            )
            .limit(
                1
            )
        )
        .scalars()
        .first()
    )

    return render_template(
        "vendedor/productos/detalle.html",

        producto=producto,

        proveedor=proveedor,

        imagen=imagen
    )