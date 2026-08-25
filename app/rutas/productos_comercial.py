import json

from datetime import (
    datetime,
    timezone
)

from decimal import (
    Decimal,
    InvalidOperation
)

from io import BytesIO

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for
)

from flask_login import (
    current_user
)

from openpyxl import (
    Workbook,
    load_workbook
)

from openpyxl.styles import (
    Alignment,
    Font,
    PatternFill
)

from openpyxl.worksheet.datavalidation import (
    DataValidation
)

from sqlalchemy import (
    or_,
    text
)

from werkzeug.utils import (
    secure_filename
)

from app.extensiones import db

from app.modelos import (
    ImagenProducto,
    MonedaEnum,
    Producto,
    Proveedor,
    RegistroApi,
    ServicioApiEnum,
    Usuario
)

from app.servicios.imgbb import (
    ErrorImgBB,
    subir_imagen
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "productos_comercial",
    __name__,
    url_prefix="/area-comercial/productos"
)


# =========================================================
# CONFIGURACION EXCEL
# =========================================================

TAMANO_MAXIMO_EXCEL = (
    5
    * 1024
    * 1024
)


COLUMNAS_EXCEL = [
    "codigo_producto",
    "codigo_proveedor",
    "nombre",
    "descripcion",
    "categoria",
    "marca",
    "modelo",
    "unidad_medida",
    "precio_base",
    "moneda"
]


# =========================================================
# CATEGORIAS PERMITIDAS
# =========================================================

CATEGORIAS_PERMITIDAS = [
    "Seguridad (EPP)",
    "Herramientas",
    "Tornillería",
    "Izaje",
    "Abrasivos",
    "Soldadura",
    "Lubricantes",
    "Rodamientos",
    "Válvulas",
    "Señalización",
    "Otros"
]


# =========================================================
# UNIDADES DE MEDIDA PERMITIDAS
# =========================================================

UNIDADES_MEDIDA_PERMITIDAS = [
    "Unidad",
    "Caja",
    "Kilogramo",
    "Metro Lineal",
    "Galón",
    "Rollo",
    "Millar",
    "Otros"
]


# =========================================================
# MONEDAS PERMITIDAS EN EXCEL
#
# CLAVE:
#     Texto visible en Excel
#
# VALOR:
#     Valor utilizado por PostgreSQL
# =========================================================

MONEDAS_EXCEL = {
    "Soles (PEN)": "PEN",
    "Dólares (USD)": "USD"
}


# =========================================================
# AUXILIARES
# =========================================================

def convertir_decimal(
    valor
):

    if valor is None:

        return None

    valor = str(
        valor
    ).strip()

    if not valor:

        return None

    valor = (
        valor
        .replace(
            "S/",
            ""
        )
        .replace(
            "US$",
            ""
        )
        .replace(
            "$",
            ""
        )
        .replace(
            " ",
            ""
        )
    )

    if (
        "," in valor
        and "." not in valor
    ):

        valor = valor.replace(
            ",",
            "."
        )

    elif (
        "," in valor
        and "." in valor
    ):

        return None

    try:

        numero = Decimal(
            valor
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


def texto_celda(
    valor
):

    if valor is None:

        return ""

    return str(
        valor
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


def obtener_proveedores(
    id_proveedor_actual=None
):

    consulta = (
        db.select(
            Proveedor
        )
        .order_by(
            Proveedor.razon_social.asc()
        )
    )

    if id_proveedor_actual:

        consulta = consulta.where(
            or_(
                Proveedor.activo.is_(
                    True
                ),

                Proveedor.id_proveedor
                == id_proveedor_actual
            )
        )

    else:

        consulta = consulta.where(
            Proveedor.activo.is_(
                True
            )
        )

    return (
        db.session.execute(
            consulta
        )
        .scalars()
        .all()
    )


def obtener_imagen_principal(
    id_producto
):

    return (
        db.session.execute(
            db.select(
                ImagenProducto
            )
            .where(
                ImagenProducto.id_producto
                == id_producto,

                ImagenProducto.es_principal.is_(
                    True
                ),

                ImagenProducto.activa.is_(
                    True
                )
            )
        )
        .scalar_one_or_none()
    )


def registrar_api_imgbb(
    *,
    exitoso,
    operacion,
    id_producto=None,
    codigo_http=None,
    identificador_externo=None,
    mensaje=None,
    url_imagen=None
):

    registro = RegistroApi(
        servicio=(
            ServicioApiEnum.IMGBB
        ),

        operacion=operacion,

        id_usuario=(
            current_user.id_usuario
        ),

        entidad_relacionada=(
            "productos"
        ),

        id_entidad_relacionada=(
            id_producto
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
            {
                "url_imagen":
                    url_imagen
            }
            if url_imagen
            else None
        )
    )

    db.session.add(
        registro
    )


# =========================================================
# VALIDAR DATOS PRODUCTO INDIVIDUAL
# =========================================================

def validar_datos_producto(
    datos,
    id_producto_actual=None
):

    if not datos[
        "id_proveedor"
    ]:

        return (
            "Debe seleccionar un proveedor."
        )

    if not datos[
        "codigo_producto"
    ]:

        return (
            "El código del producto es obligatorio."
        )

    if (
        len(
            datos[
                "codigo_producto"
            ]
        )
        > 60
    ):

        return (
            "El código del producto no puede "
            "superar 60 caracteres."
        )

    if not datos[
        "nombre"
    ]:

        return (
            "El nombre del producto es obligatorio."
        )

    if (
        len(
            datos[
                "nombre"
            ]
        )
        > 200
    ):

        return (
            "El nombre no puede superar "
            "200 caracteres."
        )

    if (
        datos[
            "codigo_proveedor"
        ]
        and len(
            datos[
                "codigo_proveedor"
            ]
        ) > 100
    ):

        return (
            "El código del proveedor no puede "
            "superar 100 caracteres."
        )

    if (
        datos[
            "categoria"
        ]
        and len(
            datos[
                "categoria"
            ]
        ) > 150
    ):

        return (
            "La categoría no puede superar "
            "150 caracteres."
        )

    if (
        datos[
            "marca"
        ]
        and len(
            datos[
                "marca"
            ]
        ) > 120
    ):

        return (
            "La marca no puede superar "
            "120 caracteres."
        )

    if (
        datos[
            "modelo"
        ]
        and len(
            datos[
                "modelo"
            ]
        ) > 120
    ):

        return (
            "El modelo no puede superar "
            "120 caracteres."
        )

    if (
        not datos[
            "unidad_medida"
        ]
        or len(
            datos[
                "unidad_medida"
            ]
        ) > 50
    ):

        return (
            "La unidad de medida no es válida."
        )

    if (
        datos[
            "precio_base_actual"
        ]
        is None
    ):

        return (
            "Ingrese un precio base válido."
        )

    if (
        datos[
            "precio_base_actual"
        ]
        < 0
    ):

        return (
            "El precio base no puede ser negativo."
        )

    if datos[
        "moneda_precio"
    ] not in (
        "PEN",
        "USD"
    ):

        return (
            "La moneda debe ser PEN o USD."
        )

    # =====================================================
    # CODIGO GLOBAL
    # =====================================================

    consulta = (
        db.select(
            Producto
        )
        .where(
            Producto.codigo_producto
            == datos[
                "codigo_producto"
            ]
        )
    )

    if id_producto_actual:

        consulta = consulta.where(
            Producto.id_producto
            != id_producto_actual
        )

    existente = (
        db.session.execute(
            consulta
        )
        .scalar_one_or_none()
    )

    if existente:

        return (
            "Ya existe un producto registrado "
            "con ese código."
        )

    return None


# =========================================================
# OBTENER FORMULARIO
# =========================================================

def obtener_formulario():

    return {
        "id_proveedor":
            request.form.get(
                "id_proveedor",
                type=int
            ),

        "codigo_producto":
            request.form.get(
                "codigo_producto",
                ""
            ).strip(),

        "codigo_proveedor":
            (
                request.form.get(
                    "codigo_proveedor",
                    ""
                ).strip()
                or None
            ),

        "nombre":
            request.form.get(
                "nombre",
                ""
            ).strip(),

        "descripcion":
            (
                request.form.get(
                    "descripcion",
                    ""
                ).strip()
                or None
            ),

        "categoria":
            (
                request.form.get(
                    "categoria",
                    ""
                ).strip()
                or None
            ),

        "marca":
            (
                request.form.get(
                    "marca",
                    ""
                ).strip()
                or None
            ),

        "modelo":
            (
                request.form.get(
                    "modelo",
                    ""
                ).strip()
                or None
            ),

        "unidad_medida":
            (
                request.form.get(
                    "unidad_medida",
                    "UNIDAD"
                ).strip()
                or "UNIDAD"
            ),

        "precio_base_actual":
            convertir_decimal(
                request.form.get(
                    "precio_base_actual"
                )
            ),

        "moneda_precio":
            request.form.get(
                "moneda_precio",
                "PEN"
            ).strip().upper()
    }


# =========================================================
# LISTAR
# =========================================================

@bp.get("/")
@rol_requerido(
    "AREA_COMERCIAL"
)
def lista():

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    id_proveedor = request.args.get(
        "id_proveedor",
        type=int
    )

    origen = request.args.get(
        "origen",
        ""
    ).strip()

    estado_imagen = request.args.get(
        "imagen",
        ""
    ).strip()

    consulta = (
        db.select(
            Producto,
            Proveedor,
            Usuario
        )
        .join(
            Proveedor,
            Producto.id_proveedor
            == Proveedor.id_proveedor
        )
        .join(
            Usuario,
            Producto.creado_por
            == Usuario.id_usuario
        )
        .order_by(
            Producto.activo.desc(),
            Producto.nombre.asc()
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

                Producto.codigo_proveedor.ilike(
                    patron
                ),

                Producto.nombre.ilike(
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
    # PROVEEDOR
    # =====================================================

    if id_proveedor:

        consulta = consulta.where(
            Producto.id_proveedor
            == id_proveedor
        )

    # =====================================================
    # REGISTRADOS POR MI
    # =====================================================

    if origen == "MIO":

        consulta = consulta.where(
            Producto.creado_por
            == current_user.id_usuario
        )

    filas = (
        db.session.execute(
            consulta
        )
        .all()
    )

    ids_productos = [
        producto.id_producto
        for producto, _, _ in filas
    ]

    imagenes = {}

    if ids_productos:

        filas_imagen = (
            db.session.execute(
                db.select(
                    ImagenProducto
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
            )
            .scalars()
            .all()
        )

        imagenes = {
            imagen.id_producto:
                imagen
            for imagen in filas_imagen
        }

    productos = []

    for (
        producto,
        proveedor,
        usuario
    ) in filas:

        imagen = imagenes.get(
            producto.id_producto
        )

        if (
            estado_imagen
            == "CON_IMAGEN"
            and imagen is None
        ):

            continue

        if (
            estado_imagen
            == "SIN_IMAGEN"
            and imagen is not None
        ):

            continue

        productos.append({
            "producto":
                producto,

            "proveedor":
                proveedor,

            "imagen":
                imagen,

            "registrado_por":
                nombre_usuario(
                    usuario
                ),

            "es_mio":
                (
                    producto.creado_por
                    == current_user.id_usuario
                )
        })

    proveedores = (
        db.session.execute(
            db.select(
                Proveedor
            )
            .order_by(
                Proveedor.razon_social.asc()
            )
        )
        .scalars()
        .all()
    )

    return render_template(
        "area_comercial/productos/lista.html",

        productos=productos,

        proveedores=proveedores,

        buscar=buscar,

        id_proveedor=id_proveedor,

        origen=origen,

        estado_imagen=estado_imagen
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_producto>"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def detalle(
    id_producto
):

    producto = db.get_or_404(
        Producto,
        id_producto
    )

    imagen = obtener_imagen_principal(
        producto.id_producto
    )

    creador = db.session.get(
        Usuario,
        producto.creado_por
    )

    return render_template(
        "area_comercial/productos/detalle.html",

        producto=producto,

        imagen=imagen,

        registrado_por=(
            nombre_usuario(
                creador
            )
        )
    )


# =========================================================
# NUEVO PRODUCTO
# =========================================================

@bp.route(
    "/nuevo",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def nuevo():

    proveedores = (
        obtener_proveedores()
    )

    if request.method == "POST":

        datos = obtener_formulario()

        error = validar_datos_producto(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        proveedor = db.session.get(
            Proveedor,
            datos[
                "id_proveedor"
            ]
        )

        if (
            proveedor is None
            or not proveedor.activo
        ):

            flash(
                "Seleccione un proveedor activo.",
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        archivo = request.files.get(
            "imagen"
        )

        # =================================================
        # IMAGEN OBLIGATORIA REGISTRO INDIVIDUAL
        # =================================================

        try:

            resultado_imagen = (
                subir_imagen(
                    archivo
                )
            )

        except ErrorImgBB as error_imgbb:

            try:

                registrar_api_imgbb(
                    exitoso=False,

                    operacion=(
                        "SUBIR_IMAGEN_PRODUCTO"
                    ),

                    codigo_http=(
                        error_imgbb.codigo_http
                    ),

                    mensaje=str(
                        error_imgbb
                    )
                )

                db.session.commit()

            except Exception:

                db.session.rollback()

            flash(
                str(
                    error_imgbb
                ),
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        producto = Producto(
            id_proveedor=(
                proveedor.id_proveedor
            ),

            codigo_producto=(
                datos[
                    "codigo_producto"
                ]
            ),

            codigo_proveedor=(
                datos[
                    "codigo_proveedor"
                ]
            ),

            nombre=(
                datos[
                    "nombre"
                ]
            ),

            descripcion=(
                datos[
                    "descripcion"
                ]
            ),

            categoria=(
                datos[
                    "categoria"
                ]
            ),

            marca=(
                datos[
                    "marca"
                ]
            ),

            modelo=(
                datos[
                    "modelo"
                ]
            ),

            unidad_medida=(
                datos[
                    "unidad_medida"
                ]
            ),

            precio_base_actual=(
                datos[
                    "precio_base_actual"
                ]
            ),

            precio_venta_actual=None,

            moneda_precio=(
                MonedaEnum(
                    datos[
                        "moneda_precio"
                    ]
                )
            ),

            activo=True,

            creado_por=(
                current_user.id_usuario
            ),

            actualizado_por=None
        )

        try:

            db.session.add(
                producto
            )

            db.session.flush()

            imagen = ImagenProducto(
                id_producto=(
                    producto.id_producto
                ),

                id_imagen_externa=(
                    resultado_imagen[
                        "id_imagen_externa"
                    ]
                ),

                url_imagen=(
                    resultado_imagen[
                        "url_imagen"
                    ]
                ),

                url_visualizacion=(
                    resultado_imagen[
                        "url_visualizacion"
                    ]
                ),

                url_eliminacion=(
                    resultado_imagen[
                        "url_eliminacion"
                    ]
                ),

                nombre_archivo_original=(
                    resultado_imagen[
                        "nombre_archivo_original"
                    ]
                ),

                es_principal=True,

                activa=True,

                subida_por=(
                    current_user.id_usuario
                )
            )

            db.session.add(
                imagen
            )

            registrar_api_imgbb(
                exitoso=True,

                operacion=(
                    "SUBIR_IMAGEN_PRODUCTO"
                ),

                id_producto=(
                    producto.id_producto
                ),

                codigo_http=(
                    resultado_imagen[
                        "codigo_http"
                    ]
                ),

                identificador_externo=(
                    resultado_imagen[
                        "id_imagen_externa"
                    ]
                ),

                url_imagen=(
                    resultado_imagen[
                        "url_imagen"
                    ]
                )
            )

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR REGISTRANDO PRODUCTO COMERCIAL:",
                error_bd
            )

            flash(
                "No se pudo registrar el producto.",
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        flash(
            "Producto registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "productos_comercial.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    return render_template(
        "area_comercial/productos/formulario.html",

        producto=None,

        proveedores=proveedores
    )


# =========================================================
# EDITAR
# =========================================================

@bp.route(
    "/<int:id_producto>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def editar(
    id_producto
):

    producto = db.get_or_404(
        Producto,
        id_producto
    )

    proveedores = (
        obtener_proveedores(
            producto.id_proveedor
        )
    )

    if request.method == "POST":

        datos = obtener_formulario()

        error = validar_datos_producto(
            datos,

            id_producto_actual=(
                producto.id_producto
            )
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        proveedor = db.session.get(
            Proveedor,
            datos[
                "id_proveedor"
            ]
        )

        if proveedor is None:

            flash(
                "El proveedor seleccionado no existe.",
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        if (
            not proveedor.activo
            and proveedor.id_proveedor
            != producto.id_proveedor
        ):

            flash(
                "No puede asignar un proveedor inactivo.",
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        producto.id_proveedor = (
            proveedor.id_proveedor
        )

        producto.codigo_producto = (
            datos[
                "codigo_producto"
            ]
        )

        producto.codigo_proveedor = (
            datos[
                "codigo_proveedor"
            ]
        )

        producto.nombre = (
            datos[
                "nombre"
            ]
        )

        producto.descripcion = (
            datos[
                "descripcion"
            ]
        )

        producto.categoria = (
            datos[
                "categoria"
            ]
        )

        producto.marca = (
            datos[
                "marca"
            ]
        )

        producto.modelo = (
            datos[
                "modelo"
            ]
        )

        producto.unidad_medida = (
            datos[
                "unidad_medida"
            ]
        )

        producto.precio_base_actual = (
            datos[
                "precio_base_actual"
            ]
        )

        producto.moneda_precio = (
            MonedaEnum(
                datos[
                    "moneda_precio"
                ]
            )
        )

        producto.actualizado_por = (
            current_user.id_usuario
        )

        try:

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR ACTUALIZANDO PRODUCTO COMERCIAL:",
                error_bd
            )

            flash(
                "No se pudo actualizar el producto.",
                "danger"
            )

            return render_template(
                "area_comercial/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        flash(
            "Producto actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "productos_comercial.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    return render_template(
        "area_comercial/productos/formulario.html",

        producto=producto,

        proveedores=proveedores
    )


# =========================================================
# REEMPLAZAR / AGREGAR IMAGEN
# =========================================================

@bp.post(
    "/<int:id_producto>/imagen/reemplazar"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def reemplazar_imagen(
    id_producto
):

    producto = db.get_or_404(
        Producto,
        id_producto
    )

    archivo = request.files.get(
        "imagen"
    )

    try:

        resultado_imagen = (
            subir_imagen(
                archivo
            )
        )

    except ErrorImgBB as error_imgbb:

        try:

            registrar_api_imgbb(
                exitoso=False,

                operacion=(
                    "REEMPLAZAR_IMAGEN_PRODUCTO"
                ),

                id_producto=(
                    producto.id_producto
                ),

                codigo_http=(
                    error_imgbb.codigo_http
                ),

                mensaje=str(
                    error_imgbb
                )
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

        flash(
            str(
                error_imgbb
            ),
            "danger"
        )

        return redirect(
            url_for(
                "productos_comercial.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    imagen_anterior = (
        obtener_imagen_principal(
            producto.id_producto
        )
    )

    try:

        if imagen_anterior:

            imagen_anterior.activa = (
                False
            )

            imagen_anterior.es_principal = (
                False
            )

            imagen_anterior.eliminada_en = (
                datetime.now(
                    timezone.utc
                )
            )

            db.session.flush()

        nueva_imagen = ImagenProducto(
            id_producto=(
                producto.id_producto
            ),

            id_imagen_externa=(
                resultado_imagen[
                    "id_imagen_externa"
                ]
            ),

            url_imagen=(
                resultado_imagen[
                    "url_imagen"
                ]
            ),

            url_visualizacion=(
                resultado_imagen[
                    "url_visualizacion"
                ]
            ),

            url_eliminacion=(
                resultado_imagen[
                    "url_eliminacion"
                ]
            ),

            nombre_archivo_original=(
                resultado_imagen[
                    "nombre_archivo_original"
                ]
            ),

            es_principal=True,

            activa=True,

            subida_por=(
                current_user.id_usuario
            )
        )

        db.session.add(
            nueva_imagen
        )

        registrar_api_imgbb(
            exitoso=True,

            operacion=(
                "REEMPLAZAR_IMAGEN_PRODUCTO"
            ),

            id_producto=(
                producto.id_producto
            ),

            codigo_http=(
                resultado_imagen[
                    "codigo_http"
                ]
            ),

            identificador_externo=(
                resultado_imagen[
                    "id_imagen_externa"
                ]
            ),

            url_imagen=(
                resultado_imagen[
                    "url_imagen"
                ]
            )
        )

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR REEMPLAZANDO IMAGEN:",
            error_bd
        )

        flash(
            "No se pudo guardar la nueva imagen.",
            "danger"
        )

        return redirect(
            url_for(
                "productos_comercial.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    flash(
        "Imagen actualizada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "productos_comercial.detalle",

            id_producto=(
                producto.id_producto
            )
        )
    )


# =========================================================
# ELIMINAR IMAGEN
# =========================================================

@bp.post(
    "/<int:id_producto>/imagen/eliminar"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def eliminar_imagen(
    id_producto
):

    producto = db.get_or_404(
        Producto,
        id_producto
    )

    imagen = obtener_imagen_principal(
        producto.id_producto
    )

    if imagen is None:

        flash(
            "El producto no tiene una imagen activa.",
            "warning"
        )

        return redirect(
            url_for(
                "productos_comercial.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    imagen.activa = False

    imagen.es_principal = False

    imagen.eliminada_en = (
        datetime.now(
            timezone.utc
        )
    )

    try:

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR ELIMINANDO IMAGEN:",
            error_bd
        )

        flash(
            "No se pudo eliminar la imagen.",
            "danger"
        )

        return redirect(
            url_for(
                "productos_comercial.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    flash(
        "Imagen eliminada del producto.",
        "success"
    )

    return redirect(
        url_for(
            "productos_comercial.detalle",

            id_producto=(
                producto.id_producto
            )
        )
    )


# =========================================================
# DESCARGAR PLANTILLA EXCEL
# =========================================================

@bp.get(
    "/importar/plantilla"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def descargar_plantilla():

    libro = Workbook()

    hoja = libro.active

    hoja.title = (
        "PRODUCTOS"
    )

    # =====================================================
    # ENCABEZADOS
    # =====================================================

    for columna, titulo in enumerate(
        COLUMNAS_EXCEL,
        start=1
    ):

        celda = hoja.cell(
            row=1,
            column=columna,
            value=titulo
        )

        celda.font = Font(
            bold=True,
            color="FFFFFF"
        )

        celda.fill = PatternFill(
            fill_type="solid",
            fgColor="1F4E78"
        )

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    hoja.freeze_panes = (
        "A2"
    )

    hoja.auto_filter.ref = (
        "A1:J1"
    )

    # =====================================================
    # ANCHOS
    # =====================================================

    anchos = {
        "A": 20,
        "B": 22,
        "C": 35,
        "D": 45,
        "E": 25,
        "F": 20,
        "G": 20,
        "H": 20,
        "I": 18,
        "J": 20
    }

    for columna, ancho in anchos.items():

        hoja.column_dimensions[
            columna
        ].width = ancho

    # =====================================================
    # FORMATO PRECIO
    # =====================================================

    for fila in range(
        2,
        5001
    ):

        hoja[
            f"I{fila}"
        ].number_format = (
            "0.00"
        )

    # =====================================================
    # HOJA OCULTA CON LISTAS
    # =====================================================

    hoja_listas = (
        libro.create_sheet(
            "LISTAS"
        )
    )

    # =====================================================
    # CATEGORIAS
    # =====================================================

    for fila, categoria in enumerate(
        CATEGORIAS_PERMITIDAS,
        start=1
    ):

        hoja_listas.cell(
            row=fila,
            column=1,
            value=categoria
        )

    # =====================================================
    # UNIDADES DE MEDIDA
    # =====================================================

    for fila, unidad in enumerate(
        UNIDADES_MEDIDA_PERMITIDAS,
        start=1
    ):

        hoja_listas.cell(
            row=fila,
            column=2,
            value=unidad
        )

    # =====================================================
    # MONEDAS
    # =====================================================

    for fila, moneda in enumerate(
        MONEDAS_EXCEL.keys(),
        start=1
    ):

        hoja_listas.cell(
            row=fila,
            column=3,
            value=moneda
        )

    # =====================================================
    # LISTA DESPLEGABLE CATEGORIA
    #
    # COLUMNA E
    # =====================================================

    validacion_categoria = (
        DataValidation(
            type="list",

            formula1=(
                "'LISTAS'!$A$1:$A$"
                f"{len(CATEGORIAS_PERMITIDAS)}"
            ),

            allow_blank=True
        )
    )

    validacion_categoria.error = (
        "Seleccione una categoría "
        "de la lista permitida."
    )

    validacion_categoria.errorTitle = (
        "Categoría no permitida"
    )

    validacion_categoria.prompt = (
        "Seleccione una categoría "
        "del listado."
    )

    validacion_categoria.promptTitle = (
        "Categoría"
    )

    validacion_categoria.showErrorMessage = (
        True
    )

    validacion_categoria.showInputMessage = (
        True
    )

    hoja.add_data_validation(
        validacion_categoria
    )

    validacion_categoria.add(
        "E2:E5000"
    )

    # =====================================================
    # LISTA DESPLEGABLE UNIDAD DE MEDIDA
    #
    # COLUMNA H
    # =====================================================

    validacion_unidad = (
        DataValidation(
            type="list",

            formula1=(
                "'LISTAS'!$B$1:$B$"
                f"{len(UNIDADES_MEDIDA_PERMITIDAS)}"
            ),

            allow_blank=False
        )
    )

    validacion_unidad.error = (
        "Seleccione una unidad de medida "
        "de la lista permitida."
    )

    validacion_unidad.errorTitle = (
        "Unidad no permitida"
    )

    validacion_unidad.prompt = (
        "Seleccione la unidad de medida."
    )

    validacion_unidad.promptTitle = (
        "Unidad de medida"
    )

    validacion_unidad.showErrorMessage = (
        True
    )

    validacion_unidad.showInputMessage = (
        True
    )

    hoja.add_data_validation(
        validacion_unidad
    )

    validacion_unidad.add(
        "H2:H5000"
    )

    # =====================================================
    # LISTA DESPLEGABLE MONEDA
    #
    # COLUMNA J
    # =====================================================

    validacion_moneda = (
        DataValidation(
            type="list",

            formula1=(
                "'LISTAS'!$C$1:$C$"
                f"{len(MONEDAS_EXCEL)}"
            ),

            allow_blank=False
        )
    )

    validacion_moneda.error = (
        "Seleccione Soles (PEN) "
        "o Dólares (USD)."
    )

    validacion_moneda.errorTitle = (
        "Moneda no permitida"
    )

    validacion_moneda.prompt = (
        "Seleccione la moneda "
        "del producto."
    )

    validacion_moneda.promptTitle = (
        "Moneda"
    )

    validacion_moneda.showErrorMessage = (
        True
    )

    validacion_moneda.showInputMessage = (
        True
    )

    hoja.add_data_validation(
        validacion_moneda
    )

    validacion_moneda.add(
        "J2:J5000"
    )

    # =====================================================
    # OCULTAR HOJA DE LISTAS
    # =====================================================

    hoja_listas.sheet_state = (
        "hidden"
    )

    # =====================================================
    # HOJA DE INSTRUCCIONES
    # =====================================================

    instrucciones = (
        libro.create_sheet(
            "INSTRUCCIONES"
        )
    )

    instrucciones[
        "A1"
    ] = (
        "PLANTILLA DE IMPORTACIÓN DE PRODUCTOS"
    )

    instrucciones[
        "A1"
    ].font = Font(
        bold=True,
        size=14
    )

    instrucciones[
        "A3"
    ] = (
        "Campos obligatorios"
    )

    instrucciones[
        "A3"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B3"
    ] = (
        "codigo_producto, nombre, "
        "unidad_medida, precio_base y moneda."
    )

    # =====================================================
    # CATEGORIA
    # =====================================================

    instrucciones[
        "A5"
    ] = "Categoría"

    instrucciones[
        "A5"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B5"
    ] = (
        "Debe seleccionarse desde la lista "
        "desplegable de la plantilla."
    )

    instrucciones[
        "B6"
    ] = (
        "Seguridad (EPP), Herramientas, "
        "Tornillería, Izaje, Abrasivos, "
        "Soldadura, Lubricantes, Rodamientos, "
        "Válvulas, Señalización u Otros."
    )

    # =====================================================
    # UNIDAD
    # =====================================================

    instrucciones[
        "A8"
    ] = "Unidad de medida"

    instrucciones[
        "A8"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B8"
    ] = (
        "Debe seleccionarse desde la lista "
        "desplegable."
    )

    instrucciones[
        "B9"
    ] = (
        "Unidad, Caja, Kilogramo, "
        "Metro Lineal, Galón, Rollo, "
        "Millar u Otros."
    )

    # =====================================================
    # MONEDA
    # =====================================================

    instrucciones[
        "A11"
    ] = "Moneda"

    instrucciones[
        "A11"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B11"
    ] = (
        "Debe seleccionarse desde la lista "
        "desplegable."
    )

    instrucciones[
        "B12"
    ] = (
        "Soles (PEN) o Dólares (USD)."
    )

    # =====================================================
    # PROVEEDOR
    # =====================================================

    instrucciones[
        "A14"
    ] = "Proveedor"

    instrucciones[
        "A14"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B14"
    ] = (
        "El proveedor se selecciona en el sistema "
        "antes de subir el archivo."
    )

    # =====================================================
    # IMAGENES
    # =====================================================

    instrucciones[
        "A16"
    ] = "Imágenes"

    instrucciones[
        "A16"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B16"
    ] = (
        "Los productos importados se crean sin imagen. "
        "Después deberá cargar la imagen individualmente."
    )

    # =====================================================
    # CODIGO PRODUCTO
    # =====================================================

    instrucciones[
        "A18"
    ] = "Código del producto"

    instrucciones[
        "A18"
    ].font = Font(
        bold=True
    )

    instrucciones[
        "B18"
    ] = (
        "codigo_producto debe ser único "
        "en todo el sistema."
    )

    instrucciones.column_dimensions[
        "A"
    ].width = 28

    instrucciones.column_dimensions[
        "B"
    ].width = 95

    # =====================================================
    # GENERAR ARCHIVO
    # =====================================================

    memoria = BytesIO()

    libro.save(
        memoria
    )

    memoria.seek(
        0
    )

    return send_file(
        memoria,

        as_attachment=True,

        download_name=(
            "plantilla_importacion_productos.xlsx"
        ),

        mimetype=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )


# =========================================================
# IMPORTAR EXCEL
# =========================================================

@bp.route(
    "/importar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def importar_excel():

    proveedores = (
        obtener_proveedores()
    )

    if request.method == "GET":

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    # =====================================================
    # PROVEEDOR
    # =====================================================

    id_proveedor = request.form.get(
        "id_proveedor",
        type=int
    )

    proveedor = db.session.get(
        Proveedor,
        id_proveedor
    )

    if (
        proveedor is None
        or not proveedor.activo
    ):

        flash(
            "Seleccione un proveedor activo.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    # =====================================================
    # ARCHIVO
    # =====================================================

    archivo = request.files.get(
        "archivo_excel"
    )

    if (
        archivo is None
        or not archivo.filename
    ):

        flash(
            "Seleccione un archivo Excel.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    nombre_archivo = (
        secure_filename(
            archivo.filename
        )
    )

    if not nombre_archivo.lower().endswith(
        ".xlsx"
    ):

        flash(
            "La plantilla debe estar en formato .xlsx.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    contenido = archivo.read()

    if (
        len(
            contenido
        )
        > TAMANO_MAXIMO_EXCEL
    ):

        flash(
            "El archivo Excel no puede superar 5 MB.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    # =====================================================
    # REGISTRAR INICIO IMPORTACION
    # =====================================================

    try:

        id_importacion = (
            db.session.execute(
                text(
                    """
                    INSERT INTO importaciones_productos (
                        nombre_archivo,
                        estado,
                        importado_por
                    )
                    VALUES (
                        :nombre_archivo,
                        'PROCESANDO',
                        :importado_por
                    )
                    RETURNING id_importacion
                    """
                ),

                {
                    "nombre_archivo":
                        nombre_archivo,

                    "importado_por":
                        current_user.id_usuario
                }
            )
            .scalar_one()
        )

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR CREANDO IMPORTACION:",
            error_bd
        )

        flash(
            "No se pudo iniciar la importación.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    # =====================================================
    # LEER EXCEL
    # =====================================================

    try:

        libro = load_workbook(
            filename=BytesIO(
                contenido
            ),

            read_only=True,

            data_only=True
        )

        if (
            "PRODUCTOS"
            in libro.sheetnames
        ):

            hoja = libro[
                "PRODUCTOS"
            ]

        else:

            hoja = libro.active

    except Exception as error_excel:

        print(
            "ERROR LEYENDO EXCEL:",
            error_excel
        )

        marcar_importacion_fallida(
            id_importacion=id_importacion,

            errores=[
                {
                    "fila": None,

                    "error":
                        "No fue posible leer el archivo Excel."
                }
            ]
        )

        flash(
            "No fue posible leer el archivo Excel.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    # =====================================================
    # VALIDAR ENCABEZADOS
    # =====================================================

    encabezados = [
        texto_celda(
            hoja.cell(
                row=1,
                column=columna
            ).value
        ).lower()

        for columna in range(
            1,
            len(
                COLUMNAS_EXCEL
            ) + 1
        )
    ]

    if (
        encabezados
        != COLUMNAS_EXCEL
    ):

        errores = [
            {
                "fila": 1,

                "error": (
                    "Los encabezados no corresponden "
                    "a la plantilla oficial."
                )
            }
        ]

        marcar_importacion_fallida(
            id_importacion=id_importacion,

            errores=errores
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado={
                "total": 0,
                "correctas": 0,
                "errores": 1
            },

            errores=errores
        )

    # =====================================================
    # CODIGOS YA REGISTRADOS
    # =====================================================

    codigos_existentes = set(
        db.session.execute(
            db.select(
                Producto.codigo_producto
            )
        )
        .scalars()
        .all()
    )

    codigos_archivo = set()

    productos_validos = []

    errores = []

    total_filas = 0

    # =====================================================
    # RECORRER FILAS
    # =====================================================

    for numero_fila, fila in enumerate(
        hoja.iter_rows(
            min_row=2,
            max_col=10,
            values_only=True
        ),
        start=2
    ):

        # =================================================
        # IGNORAR FILAS VACIAS
        # =================================================

        if not any(
            valor is not None
            and str(
                valor
            ).strip()

            for valor in fila
        ):

            continue

        total_filas += 1

        # =================================================
        # MONEDA EXCEL
        # =================================================

        moneda_excel = (
            texto_celda(
                fila[
                    9
                ]
            )
        )

        moneda_interna = (
            MONEDAS_EXCEL.get(
                moneda_excel
            )
        )

        # =================================================
        # DATOS
        # =================================================

        datos = {
            "codigo_producto":
                texto_celda(
                    fila[
                        0
                    ]
                ),

            "codigo_proveedor":
                (
                    texto_celda(
                        fila[
                            1
                        ]
                    )
                    or None
                ),

            "nombre":
                texto_celda(
                    fila[
                        2
                    ]
                ),

            "descripcion":
                (
                    texto_celda(
                        fila[
                            3
                        ]
                    )
                    or None
                ),

            "categoria":
                (
                    texto_celda(
                        fila[
                            4
                        ]
                    )
                    or None
                ),

            "marca":
                (
                    texto_celda(
                        fila[
                            5
                        ]
                    )
                    or None
                ),

            "modelo":
                (
                    texto_celda(
                        fila[
                            6
                        ]
                    )
                    or None
                ),

            "unidad_medida":
                texto_celda(
                    fila[
                        7
                    ]
                ),

            "precio_base_actual":
                convertir_decimal(
                    fila[
                        8
                    ]
                ),

            "moneda_excel":
                moneda_excel,

            "moneda_precio":
                moneda_interna
        }

        # =================================================
        # VALIDACIONES
        # =================================================

        error_fila = None

        # =================================================
        # CODIGO
        # =================================================

        if not datos[
            "codigo_producto"
        ]:

            error_fila = (
                "El código del producto es obligatorio."
            )

        elif (
            len(
                datos[
                    "codigo_producto"
                ]
            ) > 60
        ):

            error_fila = (
                "El código supera 60 caracteres."
            )

        elif (
            datos[
                "codigo_producto"
            ]
            in codigos_existentes
        ):

            error_fila = (
                "El código ya se encuentra "
                "registrado en el sistema."
            )

        elif (
            datos[
                "codigo_producto"
            ]
            in codigos_archivo
        ):

            error_fila = (
                "El código está repetido "
                "dentro del archivo Excel."
            )

        # =================================================
        # NOMBRE
        # =================================================

        elif not datos[
            "nombre"
        ]:

            error_fila = (
                "El nombre es obligatorio."
            )

        elif (
            len(
                datos[
                    "nombre"
                ]
            ) > 200
        ):

            error_fila = (
                "El nombre supera 200 caracteres."
            )

        # =================================================
        # CODIGO PROVEEDOR
        # =================================================

        elif (
            datos[
                "codigo_proveedor"
            ]
            and len(
                datos[
                    "codigo_proveedor"
                ]
            ) > 100
        ):

            error_fila = (
                "El código del proveedor "
                "supera 100 caracteres."
            )

        # =================================================
        # CATEGORIA
        # =================================================

        elif (
            datos[
                "categoria"
            ]
            and datos[
                "categoria"
            ]
            not in CATEGORIAS_PERMITIDAS
        ):

            error_fila = (
                "La categoría no pertenece "
                "a la lista permitida."
            )

        # =================================================
        # MARCA
        # =================================================

        elif (
            datos[
                "marca"
            ]
            and len(
                datos[
                    "marca"
                ]
            ) > 120
        ):

            error_fila = (
                "La marca supera 120 caracteres."
            )

        # =================================================
        # MODELO
        # =================================================

        elif (
            datos[
                "modelo"
            ]
            and len(
                datos[
                    "modelo"
                ]
            ) > 120
        ):

            error_fila = (
                "El modelo supera 120 caracteres."
            )

        # =================================================
        # UNIDAD DE MEDIDA
        # =================================================

        elif not datos[
            "unidad_medida"
        ]:

            error_fila = (
                "Debe seleccionar una unidad de medida."
            )

        elif (
            datos[
                "unidad_medida"
            ]
            not in UNIDADES_MEDIDA_PERMITIDAS
        ):

            error_fila = (
                "La unidad de medida no pertenece "
                "a la lista permitida."
            )

        # =================================================
        # PRECIO BASE
        # =================================================

        elif (
            datos[
                "precio_base_actual"
            ]
            is None
        ):

            error_fila = (
                "El precio base no es válido."
            )

        elif (
            datos[
                "precio_base_actual"
            ]
            < 0
        ):

            error_fila = (
                "El precio base no puede ser negativo."
            )

        # =================================================
        # MONEDA
        # =================================================

        elif not datos[
            "moneda_excel"
        ]:

            error_fila = (
                "Debe seleccionar una moneda."
            )

        elif (
            datos[
                "moneda_precio"
            ]
            is None
        ):

            error_fila = (
                "La moneda no pertenece "
                "a la lista permitida. "
                "Seleccione Soles (PEN) "
                "o Dólares (USD)."
            )

        # =================================================
        # ERROR
        # =================================================

        if error_fila:

            errores.append({
                "fila":
                    numero_fila,

                "codigo_producto":
                    datos[
                        "codigo_producto"
                    ],

                "error":
                    error_fila
            })

            continue

        # =================================================
        # PRODUCTO VALIDO
        # =================================================

        codigos_archivo.add(
            datos[
                "codigo_producto"
            ]
        )

        producto = Producto(
            id_proveedor=(
                proveedor.id_proveedor
            ),

            codigo_producto=(
                datos[
                    "codigo_producto"
                ]
            ),

            codigo_proveedor=(
                datos[
                    "codigo_proveedor"
                ]
            ),

            nombre=(
                datos[
                    "nombre"
                ]
            ),

            descripcion=(
                datos[
                    "descripcion"
                ]
            ),

            categoria=(
                datos[
                    "categoria"
                ]
            ),

            marca=(
                datos[
                    "marca"
                ]
            ),

            modelo=(
                datos[
                    "modelo"
                ]
            ),

            unidad_medida=(
                datos[
                    "unidad_medida"
                ]
            ),

            precio_base_actual=(
                datos[
                    "precio_base_actual"
                ]
            ),

            precio_venta_actual=None,

            moneda_precio=(
                MonedaEnum(
                    datos[
                        "moneda_precio"
                    ]
                )
            ),

            activo=True,

            creado_por=(
                current_user.id_usuario
            ),

            actualizado_por=None
        )

        productos_validos.append(
            producto
        )

    # =====================================================
    # ARCHIVO SIN PRODUCTOS
    # =====================================================

    if total_filas == 0:

        errores = [
            {
                "fila": None,

                "error": (
                    "La plantilla no contiene "
                    "productos para importar."
                )
            }
        ]

        marcar_importacion_fallida(
            id_importacion=id_importacion,

            errores=errores
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado={
                "total": 0,
                "correctas": 0,
                "errores": 1
            },

            errores=errores
        )

    # =====================================================
    # NINGUNA FILA VALIDA
    # =====================================================

    if not productos_validos:

        marcar_importacion_fallida(
            id_importacion=id_importacion,

            errores=errores,

            total_filas=total_filas
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado={
                "total":
                    total_filas,

                "correctas":
                    0,

                "errores":
                    len(
                        errores
                    )
            },

            errores=errores
        )

    # =====================================================
    # GUARDAR PRODUCTOS
    # =====================================================

    try:

        db.session.add_all(
            productos_validos
        )

        estado_final = (
            "COMPLETADA"
            if not errores
            else
            "COMPLETADA_CON_ERRORES"
        )

        db.session.execute(
            text(
                """
                UPDATE importaciones_productos

                SET
                    estado = :estado,
                    total_filas = :total_filas,
                    filas_correctas = :filas_correctas,
                    filas_con_error = :filas_con_error,
                    detalle_errores =
                        CAST(:detalle_errores AS JSONB),
                    finalizado_en = NOW()

                WHERE id_importacion = :id_importacion
                """
            ),

            {
                "estado":
                    estado_final,

                "total_filas":
                    total_filas,

                "filas_correctas":
                    len(
                        productos_validos
                    ),

                "filas_con_error":
                    len(
                        errores
                    ),

                "detalle_errores":
                    json.dumps(
                        errores,
                        ensure_ascii=False
                    ),

                "id_importacion":
                    id_importacion
            }
        )

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR IMPORTANDO PRODUCTOS:",
            error_bd
        )

        marcar_importacion_fallida(
            id_importacion=id_importacion,

            errores=[
                {
                    "fila": None,

                    "error": (
                        "Ocurrió un error al guardar "
                        "los productos."
                    )
                }
            ],

            total_filas=total_filas
        )

        flash(
            "No fue posible completar la importación.",
            "danger"
        )

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=None,

            errores=None
        )

    # =====================================================
    # RESULTADO
    # =====================================================

    resultado = {
        "total":
            total_filas,

        "correctas":
            len(
                productos_validos
            ),

        "errores":
            len(
                errores
            )
    }

    if errores:

        return render_template(
            "area_comercial/productos/importar.html",

            proveedores=proveedores,

            resultado=resultado,

            errores=errores
        )

    flash(
        (
            f"Se importaron "
            f"{len(productos_validos)} productos "
            "correctamente. Ahora puede agregar "
            "sus imágenes."
        ),
        "success"
    )

    return redirect(
        url_for(
            "productos_comercial.lista",

            origen="MIO",

            imagen="SIN_IMAGEN"
        )
    )


# =========================================================
# MARCAR IMPORTACION FALLIDA
# =========================================================

def marcar_importacion_fallida(
    id_importacion,
    errores,
    total_filas=0
):

    try:

        db.session.execute(
            text(
                """
                UPDATE importaciones_productos

                SET
                    estado = 'FALLIDA',
                    total_filas = :total_filas,
                    filas_correctas = 0,
                    filas_con_error = :filas_con_error,
                    detalle_errores =
                        CAST(:detalle_errores AS JSONB),
                    finalizado_en = NOW()

                WHERE id_importacion = :id_importacion
                """
            ),

            {
                "total_filas":
                    total_filas,

                "filas_con_error":
                    len(
                        errores
                    ),

                "detalle_errores":
                    json.dumps(
                        errores,
                        ensure_ascii=False
                    ),

                "id_importacion":
                    id_importacion
            }
        )

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR MARCANDO IMPORTACION FALLIDA:",
            error_bd
        )