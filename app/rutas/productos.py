from datetime import (
    datetime,
    timezone
)

from decimal import (
    Decimal,
    InvalidOperation
)

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user
)

from sqlalchemy import (
    or_
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
    "productos",
    __name__,
    url_prefix="/administrador/productos"
)


# =========================================================
# AUXILIARES
# =========================================================

def decimal_o_none(
    valor
):

    if valor is None:

        return None

    valor = str(
        valor
    ).strip()

    if not valor:

        return None

    try:

        return Decimal(
            valor
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return None


# =========================================================
# NOMBRE DE USUARIO
# =========================================================

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


# =========================================================
# PROVEEDORES
# =========================================================

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


# =========================================================
# IMAGEN PRINCIPAL
# =========================================================

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


# =========================================================
# REGISTRAR API IMGBB
# =========================================================

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
# LISTAR
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

    id_proveedor = request.args.get(
        "id_proveedor",
        type=int
    )

    consulta = (
        db.select(
            Producto
        )
        .order_by(
            Producto.creado_en.desc()
        )
    )

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
                )
            )
        )

    if id_proveedor:

        consulta = consulta.where(
            Producto.id_proveedor
            == id_proveedor
        )

    productos = (
        db.session.execute(
            consulta
        )
        .scalars()
        .all()
    )

    imagenes = {}

    for producto in productos:

        imagenes[
            producto.id_producto
        ] = obtener_imagen_principal(
            producto.id_producto
        )

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
        "administrador/productos/lista.html",

        productos=productos,

        proveedores=proveedores,

        imagenes=imagenes,

        buscar=buscar,

        id_proveedor=id_proveedor
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_producto>"
)
@rol_requerido(
    "ADMINISTRADOR"
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

    registrado_por = nombre_usuario(
        creador
    )

    return render_template(
        "administrador/productos/detalle.html",

        producto=producto,

        imagen=imagen,

        registrado_por=(
            registrado_por
        )
    )


# =========================================================
# NUEVO
# =========================================================

@bp.route(
    "/nuevo",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "ADMINISTRADOR"
)
def nuevo():

    proveedores = (
        obtener_proveedores()
    )

    if request.method == "POST":

        datos = obtener_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "administrador/productos/formulario.html",

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
                "administrador/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        existente = (
            db.session.execute(
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
            .scalar_one_or_none()
        )

        if existente:

            flash(
                "Ya existe un producto "
                "con ese código.",
                "danger"
            )

            return render_template(
                "administrador/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        archivo = request.files.get(
            "imagen"
        )

        # =================================================
        # SUBIR IMAGEN
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
                "administrador/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        # =================================================
        # PRODUCTO
        # =================================================

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

            # =============================================
            # IMAGEN
            # =============================================

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
                "ERROR REGISTRANDO PRODUCTO:",
                error_bd
            )

            flash(
                "No se pudo registrar el producto.",
                "danger"
            )

            return render_template(
                "administrador/productos/formulario.html",

                producto=None,

                proveedores=proveedores
            )

        flash(
            "Producto registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "productos.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    return render_template(
        "administrador/productos/formulario.html",

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
    "ADMINISTRADOR"
)
def editar(
    id_producto
):

    producto = db.get_or_404(
        Producto,
        id_producto
    )

    proveedores = obtener_proveedores(
        producto.id_proveedor
    )

    if request.method == "POST":

        datos = obtener_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "administrador/productos/formulario.html",

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
                "administrador/productos/formulario.html",

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
                "administrador/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        existente = (
            db.session.execute(
                db.select(
                    Producto
                )
                .where(
                    Producto.codigo_producto
                    == datos[
                        "codigo_producto"
                    ],

                    Producto.id_producto
                    != producto.id_producto
                )
            )
            .scalar_one_or_none()
        )

        if existente:

            flash(
                "Ya existe otro producto "
                "con ese código.",
                "danger"
            )

            return render_template(
                "administrador/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        # =================================================
        # ACTUALIZAR
        # =================================================

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
                "ERROR ACTUALIZANDO PRODUCTO:",
                error_bd
            )

            flash(
                "No se pudo actualizar el producto.",
                "danger"
            )

            return render_template(
                "administrador/productos/formulario.html",

                producto=producto,

                proveedores=proveedores
            )

        flash(
            "Producto actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "productos.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    return render_template(
        "administrador/productos/formulario.html",

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
    "ADMINISTRADOR"
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

    # =====================================================
    # SUBIR NUEVA IMAGEN A IMGBB
    # =====================================================

    try:

        resultado_imagen = subir_imagen(
            archivo
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
                "productos.detalle",

                id_producto=(
                    producto.id_producto
                )
            )
        )

    # =====================================================
    # IMAGEN ACTUAL
    # =====================================================

    imagen_anterior = (
        obtener_imagen_principal(
            producto.id_producto
        )
    )

    # =====================================================
    # GUARDAR
    # =====================================================

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

            # =============================================
            # NECESARIO PARA LIBERAR EL INDICE UNICO
            # DE IMAGEN PRINCIPAL ACTIVA ANTES DE INSERTAR
            # LA NUEVA IMAGEN.
            # =============================================

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
            "No se pudo reemplazar la imagen.",
            "danger"
        )

        return redirect(
            url_for(
                "productos.detalle",

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
            "productos.detalle",

            id_producto=(
                producto.id_producto
            )
        )
    )


# =========================================================
# ELIMINAR IMAGEN DEL PRODUCTO
#
# IMPORTANTE:
#
# MANTIENE LA MISMA LOGICA EXISTENTE DEL SISTEMA.
# LA IMAGEN SE DESACTIVA EN LA BD Y DEJA DE SER
# LA IMAGEN PRINCIPAL.
# =========================================================

@bp.post(
    "/<int:id_producto>/imagen/eliminar"
)
@rol_requerido(
    "ADMINISTRADOR"
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
                "productos.detalle",

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
                "productos.detalle",

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
            "productos.detalle",

            id_producto=(
                producto.id_producto
            )
        )
    )


# =========================================================
# OBTENER FORMULARIO
# =========================================================

def obtener_formulario():

    id_proveedor = request.form.get(
        "id_proveedor",
        type=int
    )

    codigo_producto = (
        request.form.get(
            "codigo_producto",
            ""
        )
        .strip()
    )

    codigo_proveedor = (
        request.form.get(
            "codigo_proveedor",
            ""
        )
        .strip()
    )

    nombre = (
        request.form.get(
            "nombre",
            ""
        )
        .strip()
    )

    descripcion = (
        request.form.get(
            "descripcion",
            ""
        )
        .strip()
    )

    categoria = (
        request.form.get(
            "categoria",
            ""
        )
        .strip()
    )

    marca = (
        request.form.get(
            "marca",
            ""
        )
        .strip()
    )

    modelo = (
        request.form.get(
            "modelo",
            ""
        )
        .strip()
    )

    unidad_medida = (
        request.form.get(
            "unidad_medida",
            "UNIDAD"
        )
        .strip()
    )

    precio_base_actual = (
        decimal_o_none(
            request.form.get(
                "precio_base_actual"
            )
        )
    )

    moneda_precio = (
        request.form.get(
            "moneda_precio",
            "PEN"
        )
        .strip()
    )

    return {
        "id_proveedor":
            id_proveedor,

        "codigo_producto":
            codigo_producto,

        "codigo_proveedor":
            (
                codigo_proveedor
                or None
            ),

        "nombre":
            nombre,

        "descripcion":
            (
                descripcion
                or None
            ),

        "categoria":
            (
                categoria
                or None
            ),

        "marca":
            (
                marca
                or None
            ),

        "modelo":
            (
                modelo
                or None
            ),

        "unidad_medida":
            unidad_medida
            or "UNIDAD",

        "precio_base_actual":
            precio_base_actual,

        "moneda_precio":
            moneda_precio
    }


# =========================================================
# VALIDAR
# =========================================================

def validar_datos(
    datos
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

    if not datos[
        "nombre"
    ]:

        return (
            "El nombre del producto es obligatorio."
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
            "La moneda seleccionada no es válida."
        )

    return None