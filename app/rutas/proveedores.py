from datetime import (
    datetime,
    timezone
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
    Proveedor,
    TipoDocumentoEnum
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "proveedores",
    __name__,
    url_prefix="/administrador/proveedores"
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

    consulta = (
        db.select(
            Proveedor
        )
        .order_by(
            Proveedor.creado_en.desc()
        )
    )

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        consulta = consulta.where(
            or_(
                Proveedor.razon_social.ilike(
                    patron
                ),

                Proveedor.nombre_comercial.ilike(
                    patron
                ),

                Proveedor.numero_documento.ilike(
                    patron
                ),

                Proveedor.correo.ilike(
                    patron
                )
            )
        )

    proveedores = (
        db.session.execute(
            consulta
        )
        .scalars()
        .all()
    )

    return render_template(
        "administrador/proveedores/lista.html",
        proveedores=proveedores,
        buscar=buscar
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_proveedor>"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def detalle(
    id_proveedor
):

    proveedor = db.get_or_404(
        Proveedor,
        id_proveedor
    )

    return render_template(
        "administrador/proveedores/detalle.html",
        proveedor=proveedor
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

    if request.method == "POST":

        datos = obtener_datos_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "administrador/proveedores/formulario.html",
                proveedor=None
            )

        if datos[
            "numero_documento"
        ]:

            existe = (
                db.session.execute(
                    db.select(
                        Proveedor
                    )
                    .where(
                        Proveedor.numero_documento
                        == datos[
                            "numero_documento"
                        ]
                    )
                )
                .scalar_one_or_none()
            )

            if existe:

                flash(
                    "Ya existe un proveedor "
                    "registrado con ese RUC.",
                    "danger"
                )

                return render_template(
                    "administrador/proveedores/formulario.html",
                    proveedor=None
                )

        proveedor = Proveedor(
            tipo_documento=(
                TipoDocumentoEnum(
                    datos[
                        "tipo_documento"
                    ]
                )
            ),

            numero_documento=(
                datos[
                    "numero_documento"
                ]
            ),

            razon_social=(
                datos[
                    "razon_social"
                ]
            ),

            nombre_comercial=(
                datos[
                    "nombre_comercial"
                ]
            ),

            correo=(
                datos[
                    "correo"
                ]
            ),

            celular=(
                datos[
                    "celular"
                ]
            ),

            telefono=(
                datos[
                    "telefono"
                ]
            ),

            direccion_fiscal=(
                datos[
                    "direccion_fiscal"
                ]
            ),

            datos_obtenidos_api=(
                datos[
                    "datos_obtenidos_api"
                ]
            ),

            api_consultada_en=(
                datetime.now(
                    timezone.utc
                )
                if datos[
                    "datos_obtenidos_api"
                ]
                else None
            ),

            activo=True,

            creado_por=(
                current_user.id_usuario
            ),

            actualizado_por=None
        )

        try:

            db.session.add(
                proveedor
            )

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR REGISTRANDO PROVEEDOR:",
                error_bd
            )

            flash(
                "No se pudo registrar el proveedor.",
                "danger"
            )

            return render_template(
                "administrador/proveedores/formulario.html",
                proveedor=None
            )

        flash(
            "Proveedor registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "proveedores.lista"
            )
        )

    return render_template(
        "administrador/proveedores/formulario.html",
        proveedor=None
    )


# =========================================================
# EDITAR
# =========================================================

@bp.route(
    "/<int:id_proveedor>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "ADMINISTRADOR"
)
def editar(
    id_proveedor
):

    proveedor = db.get_or_404(
        Proveedor,
        id_proveedor
    )

    if request.method == "POST":

        datos = obtener_datos_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "administrador/proveedores/formulario.html",
                proveedor=proveedor
            )

        if datos[
            "numero_documento"
        ]:

            existe = (
                db.session.execute(
                    db.select(
                        Proveedor
                    )
                    .where(
                        Proveedor.numero_documento
                        == datos[
                            "numero_documento"
                        ],

                        Proveedor.id_proveedor
                        != proveedor.id_proveedor
                    )
                )
                .scalar_one_or_none()
            )

            if existe:

                flash(
                    "Ya existe otro proveedor "
                    "registrado con ese RUC.",
                    "danger"
                )

                return render_template(
                    "administrador/proveedores/formulario.html",
                    proveedor=proveedor
                )

        documento_anterior = (
            proveedor.numero_documento
        )

        api_anterior = (
            proveedor.datos_obtenidos_api
        )

        proveedor.tipo_documento = (
            TipoDocumentoEnum(
                datos[
                    "tipo_documento"
                ]
            )
        )

        proveedor.numero_documento = (
            datos[
                "numero_documento"
            ]
        )

        proveedor.razon_social = (
            datos[
                "razon_social"
            ]
        )

        proveedor.nombre_comercial = (
            datos[
                "nombre_comercial"
            ]
        )

        proveedor.correo = (
            datos[
                "correo"
            ]
        )

        proveedor.celular = (
            datos[
                "celular"
            ]
        )

        proveedor.telefono = (
            datos[
                "telefono"
            ]
        )

        proveedor.direccion_fiscal = (
            datos[
                "direccion_fiscal"
            ]
        )

        proveedor.datos_obtenidos_api = (
            datos[
                "datos_obtenidos_api"
            ]
        )

        proveedor.actualizado_por = (
            current_user.id_usuario
        )

        if not datos[
            "datos_obtenidos_api"
        ]:

            proveedor.api_consultada_en = (
                None
            )

        elif (
            not api_anterior
            or documento_anterior
            != datos[
                "numero_documento"
            ]
        ):

            proveedor.api_consultada_en = (
                datetime.now(
                    timezone.utc
                )
            )

        try:

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR ACTUALIZANDO PROVEEDOR:",
                error_bd
            )

            flash(
                "No se pudo actualizar el proveedor.",
                "danger"
            )

            return render_template(
                "administrador/proveedores/formulario.html",
                proveedor=proveedor
            )

        flash(
            "Proveedor actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "proveedores.detalle",
                id_proveedor=(
                    proveedor.id_proveedor
                )
            )
        )

    return render_template(
        "administrador/proveedores/formulario.html",
        proveedor=proveedor
    )


# =========================================================
# DAR DE BAJA / REACTIVAR
# =========================================================

@bp.post(
    "/<int:id_proveedor>/cambiar-estado"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def cambiar_estado(
    id_proveedor
):

    proveedor = db.get_or_404(
        Proveedor,
        id_proveedor
    )

    proveedor.activo = (
        not proveedor.activo
    )

    proveedor.actualizado_por = (
        current_user.id_usuario
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "No se pudo cambiar el estado "
            "del proveedor.",
            "danger"
        )

        return redirect(
            url_for(
                "proveedores.lista"
            )
        )

    if proveedor.activo:

        flash(
            "Proveedor reactivado correctamente.",
            "success"
        )

    else:

        flash(
            "Proveedor dado de baja correctamente.",
            "success"
        )

    return redirect(
        url_for(
            "proveedores.lista"
        )
    )


# =========================================================
# OBTENER FORMULARIO
# =========================================================

def obtener_datos_formulario():

    tipo_documento = (
        request.form.get(
            "tipo_documento",
            ""
        )
        .strip()
    )

    numero_documento = (
        request.form.get(
            "numero_documento",
            ""
        )
        .strip()
    )

    razon_social = (
        request.form.get(
            "razon_social",
            ""
        )
        .strip()
    )

    nombre_comercial = (
        request.form.get(
            "nombre_comercial",
            ""
        )
        .strip()
    )

    correo = (
        request.form.get(
            "correo",
            ""
        )
        .strip()
        .lower()
    )

    celular = (
        request.form.get(
            "celular",
            ""
        )
        .strip()
    )

    telefono = (
        request.form.get(
            "telefono",
            ""
        )
        .strip()
    )

    direccion_fiscal = (
        request.form.get(
            "direccion_fiscal",
            ""
        )
        .strip()
    )

    datos_obtenidos_api = (
        request.form.get(
            "datos_obtenidos_api",
            "0"
        )
        == "1"
    )

    if (
        tipo_documento
        == "SIN_DOCUMENTO"
    ):

        numero_documento = None

        datos_obtenidos_api = False

    return {
        "tipo_documento":
            tipo_documento,

        "numero_documento":
            numero_documento,

        "razon_social":
            razon_social,

        "nombre_comercial":
            (
                nombre_comercial
                or None
            ),

        "correo":
            (
                correo
                or None
            ),

        "celular":
            (
                celular
                or None
            ),

        "telefono":
            (
                telefono
                or None
            ),

        "direccion_fiscal":
            (
                direccion_fiscal
                or None
            ),

        "datos_obtenidos_api":
            datos_obtenidos_api
    }


# =========================================================
# VALIDAR
# =========================================================

def validar_datos(
    datos
):

    if datos[
        "tipo_documento"
    ] not in (
        "RUC",
        "SIN_DOCUMENTO"
    ):

        return (
            "Tipo de documento inválido."
        )

    if (
        datos[
            "tipo_documento"
        ]
        == "RUC"
    ):

        ruc = (
            datos[
                "numero_documento"
            ]
            or ""
        )

        if (
            not ruc.isdigit()
            or len(ruc) != 11
        ):

            return (
                "El RUC debe contener "
                "exactamente 11 dígitos."
            )

    if not datos[
        "razon_social"
    ]:

        return (
            "La razón social es obligatoria."
        )

    return None