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

from flask_login import current_user

from sqlalchemy import or_

from app.extensiones import db

from app.modelos import (
    Producto,
    Proveedor
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "precios_venta",
    __name__,
    url_prefix="/administrador/precios-venta"
)


# =========================================================
# CONVERTIR DECIMAL
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

    # =====================================================
    # LIMPIAR SIMBOLOS
    # =====================================================

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
        .strip()
    )

    # =====================================================
    # ACEPTAR COMA DECIMAL
    #
    # 150,50 -> 150.50
    # =====================================================

    if (
        "," in valor
        and "." not in valor
    ):

        valor = valor.replace(
            ",",
            "."
        )

    # Si vienen coma y punto juntos,
    # no aceptamos el formato para evitar
    # interpretar incorrectamente miles.

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

    estado_precio = request.args.get(
        "estado_precio",
        ""
    ).strip()

    consulta = (
        db.select(
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
            )
        )
        .order_by(
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

                Producto.nombre.ilike(
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
    # FILTRAR PROVEEDOR
    # =====================================================

    if id_proveedor:

        consulta = consulta.where(
            Producto.id_proveedor
            == id_proveedor
        )

    # =====================================================
    # FILTRAR PRECIO
    # =====================================================

    if (
        estado_precio
        == "CON_PRECIO"
    ):

        consulta = consulta.where(
            Producto.precio_venta_actual.is_not(
                None
            )
        )

    elif (
        estado_precio
        == "SIN_PRECIO"
    ):

        consulta = consulta.where(
            Producto.precio_venta_actual.is_(
                None
            )
        )

    productos = (
        db.session.execute(
            consulta
        )
        .scalars()
        .unique()
        .all()
    )

    proveedores = (
        db.session.execute(
            db.select(
                Proveedor
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
        .scalars()
        .all()
    )

    return render_template(
        "administrador/precios_venta/lista.html",

        productos=productos,

        proveedores=proveedores,

        buscar=buscar,

        id_proveedor=id_proveedor,

        estado_precio=estado_precio
    )


# =========================================================
# ACTUALIZAR PRECIO Y STOCK
# =========================================================

@bp.post(
    "/<int:id_producto>/actualizar"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def actualizar(
    id_producto
):

    producto = db.get_or_404(
        Producto,
        id_producto
    )

    # =====================================================
    # PRODUCTO ACTIVO
    # =====================================================

    if not producto.activo:

        flash(
            "No se puede modificar un producto inactivo.",
            "warning"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    # =====================================================
    # RECIBIR DATOS
    # =====================================================

    precio_texto = request.form.get(
        "precio_venta_actual",
        ""
    )

    stock_texto = request.form.get(
        "stock_disponible",
        ""
    )

    precio_venta = convertir_decimal(
        precio_texto
    )

    stock_disponible = convertir_decimal(
        stock_texto
    )

    # =====================================================
    # VALIDAR PRECIO
    # =====================================================

    if precio_venta is None:

        flash(
            (
                "Ingrese un precio de venta válido "
                f"para {producto.nombre}. "
                "Ejemplo: 150.50 o 150,50."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    if precio_venta < 0:

        flash(
            "El precio de venta no puede ser negativo.",
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    # =====================================================
    # VALIDAR MAXIMO PRECIO
    # NUMERIC(14,2)
    # =====================================================

    if precio_venta > Decimal(
        "999999999999.99"
    ):

        flash(
            "El precio ingresado es demasiado grande.",
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    # =====================================================
    # REDONDEAR PRECIO
    # =====================================================

    precio_venta = (
        precio_venta.quantize(
            Decimal(
                "0.01"
            )
        )
    )

    # =====================================================
    # VALIDAR STOCK
    # =====================================================

    if stock_disponible is None:

        flash(
            (
                "Ingrese un stock válido "
                f"para {producto.nombre}."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    if stock_disponible < 0:

        flash(
            "El stock disponible no puede ser negativo.",
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    # =====================================================
    # VALIDAR MAXIMO STOCK
    # NUMERIC(14,3)
    # =====================================================

    if stock_disponible > Decimal(
        "99999999999.999"
    ):

        flash(
            "El stock ingresado es demasiado grande.",
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    # =====================================================
    # REDONDEAR STOCK
    # =====================================================

    stock_disponible = (
        stock_disponible.quantize(
            Decimal(
                "0.001"
            )
        )
    )

    # =====================================================
    # ACTUALIZAR
    # =====================================================

    producto.precio_venta_actual = (
        precio_venta
    )

    producto.stock_disponible = (
        stock_disponible
    )

    producto.actualizado_por = (
        current_user.id_usuario
    )

    # =====================================================
    # GUARDAR
    # =====================================================

    try:

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR ACTUALIZANDO PRECIO Y STOCK:",
            error
        )

        flash(
            "No se pudo actualizar el precio y stock del producto.",
            "danger"
        )

        return redirect(
            url_for(
                "precios_venta.lista"
            )
        )

    flash(
        (
            f"Precio y stock de "
            f"{producto.nombre} "
            "actualizados correctamente."
        ),
        "success"
    )

    return redirect(
        url_for(
            "precios_venta.lista"
        )
    )