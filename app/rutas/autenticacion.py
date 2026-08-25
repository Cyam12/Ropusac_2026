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

from flask_login import (
    current_user,
    login_user,
    logout_user
)

from sqlalchemy import func

from app.extensiones import db

from app.modelos import Usuario


bp = Blueprint(
    "autenticacion",
    __name__
)


# =========================================================
# REDIRECCIÓN SEGÚN ROL
# =========================================================

def redirigir_segun_rol(
    usuario
):

    rutas = {

        "ADMINISTRADOR":
            "administrador.inicio",

        "AREA_COMERCIAL":
            "dashboard.area_comercial",

        "VENDEDOR":
            "dashboard.vendedor"
    }

    endpoint = rutas.get(
        usuario.codigo_rol
    )

    if endpoint is None:

        logout_user()

        flash(
            "El usuario no tiene un rol válido.",
            "danger"
        )

        return redirect(
            url_for(
                "autenticacion.login"
            )
        )

    return redirect(
        url_for(
            endpoint
        )
    )


# =========================================================
# LOGIN
# =========================================================

@bp.route(
    "/",
    methods=[
        "GET",
        "POST"
    ]
)
@bp.route(
    "/login",
    methods=[
        "GET",
        "POST"
    ]
)
def login():

    if current_user.is_authenticated:

        return redirigir_segun_rol(
            current_user
        )

    if request.method == "POST":

        correo = (
            request.form.get(
                "correo",
                ""
            )
            .strip()
            .lower()
        )

        contrasena = request.form.get(
            "contrasena",
            ""
        )

        if (
            not correo
            or not contrasena
        ):

            flash(
                "Ingrese correo y contraseña.",
                "warning"
            )

            return render_template(
                "autenticacion/login.html",
                correo=correo
            )

        usuario = db.session.execute(
            db.select(Usuario)
            .where(
                func.lower(
                    Usuario.correo
                ) == correo
            )
        ).scalar_one_or_none()

        if (
            usuario is None
            or not usuario.activo
            or not usuario.verificar_contrasena(
                contrasena
            )
        ):

            flash(
                "Correo o contraseña incorrectos.",
                "danger"
            )

            return render_template(
                "autenticacion/login.html",
                correo=correo
            ), 401

        login_user(
            usuario,
            remember=False
        )

        usuario.ultimo_acceso_en = (
            datetime.now(
                timezone.utc
            )
        )

        db.session.commit()

        return redirigir_segun_rol(
            usuario
        )

    return render_template(
        "autenticacion/login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@bp.post("/logout")
def logout():

    if current_user.is_authenticated:

        logout_user()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "autenticacion.login"
        )
    )