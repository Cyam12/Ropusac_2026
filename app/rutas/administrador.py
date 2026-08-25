from flask import (
    Blueprint,
    render_template
)

from sqlalchemy import text

from app.extensiones import db

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "administrador",
    __name__,
    url_prefix="/administrador"
)


# =========================================================
# DASHBOARD
#
# INDICADORES:
#
# - USUARIOS REGISTRADOS
# - PROVEEDORES REGISTRADOS
# - CLIENTES REGISTRADOS
# - PRODUCTOS REGISTRADOS
# - BOLETAS REGISTRADAS
#
# LOS 5 CONTEOS SE REALIZAN EN UNA SOLA CONSULTA
# A POSTGRESQL PARA EVITAR MULTIPLES VIAJES A LA BD.
# =========================================================

@bp.get("/")
@rol_requerido(
    "ADMINISTRADOR"
)
def inicio():

    # =====================================================
    # INDICADORES GENERALES
    # =====================================================

    indicadores = (
        db.session.execute(
            text(
                """
                SELECT

                    (
                        SELECT COUNT(*)
                        FROM usuarios
                    ) AS usuarios_registrados,

                    (
                        SELECT COUNT(*)
                        FROM proveedores
                    ) AS proveedores_registrados,

                    (
                        SELECT COUNT(*)
                        FROM clientes
                    ) AS clientes_registrados,

                    (
                        SELECT COUNT(*)
                        FROM productos
                    ) AS productos_registrados,

                    (
                        SELECT COUNT(*)
                        FROM boletas
                    ) AS boletas_registradas
                """
            )
        )
        .mappings()
        .one()
    )

    # =====================================================
    # VALORES
    # =====================================================

    usuarios_registrados = (
        indicadores[
            "usuarios_registrados"
        ]
        or 0
    )

    proveedores_registrados = (
        indicadores[
            "proveedores_registrados"
        ]
        or 0
    )

    clientes_registrados = (
        indicadores[
            "clientes_registrados"
        ]
        or 0
    )

    productos_registrados = (
        indicadores[
            "productos_registrados"
        ]
        or 0
    )

    boletas_registradas = (
        indicadores[
            "boletas_registradas"
        ]
        or 0
    )

    # =====================================================
    # TEMPLATE
    # =====================================================

    return render_template(
        "administrador/inicio.html",

        usuarios_registrados=(
            usuarios_registrados
        ),

        proveedores_registrados=(
            proveedores_registrados
        ),

        clientes_registrados=(
            clientes_registrados
        ),

        productos_registrados=(
            productos_registrados
        ),

        boletas_registradas=(
            boletas_registradas
        )
    )