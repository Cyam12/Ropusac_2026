from flask import (
    Blueprint,
    jsonify,
    request
)

from flask_login import (
    current_user,
    login_required
)

from app.extensiones import db

from app.modelos import (
    RegistroApi,
    ServicioApiEnum
)

from app.servicios.apis_net import (
    consultar_dni,
    consultar_ruc,
    ErrorApisNet
)

from app.servicios.geoapify import (
    buscar_direcciones,
    ErrorGeoapify
)


bp = Blueprint(
    "integraciones",
    __name__,
    url_prefix="/integraciones"
)


# =========================================================
# VALIDAR ENTIDAD
# =========================================================

def obtener_entidad(
    valor,
    valor_defecto
):

    entidades_validas = {
        "usuarios",
        "proveedores",
        "clientes"
    }

    entidad = (
        valor
        or valor_defecto
    ).strip().lower()

    if entidad not in entidades_validas:

        return valor_defecto

    return entidad


# =========================================================
# CONSULTAR DNI
# =========================================================

@bp.get(
    "/dni/<dni>"
)
@login_required
def consultar_dni_ruta(
    dni
):

    entidad = obtener_entidad(
        request.args.get(
            "entidad"
        ),
        "usuarios"
    )

    try:

        datos = consultar_dni(
            dni
        )

        registro = RegistroApi(
            servicio=(
                ServicioApiEnum.APIS_NET
            ),

            operacion="CONSULTAR_DNI",

            id_usuario=(
                current_user.id_usuario
            ),

            entidad_relacionada=entidad,

            exitoso=True,

            codigo_http=200,

            respuesta_resumida={
                "numero_documento":
                    datos[
                        "numero_documento"
                    ]
            }
        )

        db.session.add(
            registro
        )

        db.session.commit()

        return jsonify({
            "exito": True,

            "numero_documento":
                datos[
                    "numero_documento"
                ],

            "nombres":
                datos[
                    "nombres"
                ],

            "apellido_paterno":
                datos[
                    "apellido_paterno"
                ],

            "apellido_materno":
                datos[
                    "apellido_materno"
                ],

            "apellidos":
                datos[
                    "apellidos"
                ],

            "nombre_completo":
                datos[
                    "nombre_completo"
                ],

            "direccion":
                datos.get(
                    "direccion"
                )
        })

    except (
        ValueError,
        ErrorApisNet
    ) as error:

        db.session.rollback()

        registrar_error_api(
            operacion="CONSULTAR_DNI",
            entidad=entidad,
            mensaje=str(
                error
            )
        )

        return jsonify({
            "exito": False,
            "mensaje": str(
                error
            )
        }), 400


# =========================================================
# CONSULTAR RUC
# =========================================================

@bp.get(
    "/ruc/<ruc>"
)
@login_required
def consultar_ruc_ruta(
    ruc
):

    entidad = obtener_entidad(
        request.args.get(
            "entidad"
        ),
        "proveedores"
    )

    try:

        datos = consultar_ruc(
            ruc
        )

        registro = RegistroApi(
            servicio=(
                ServicioApiEnum.APIS_NET
            ),

            operacion="CONSULTAR_RUC",

            id_usuario=(
                current_user.id_usuario
            ),

            entidad_relacionada=entidad,

            exitoso=True,

            codigo_http=200,

            respuesta_resumida={
                "ruc":
                    datos[
                        "ruc"
                    ],

                "razon_social":
                    datos[
                        "razon_social"
                    ]
            }
        )

        db.session.add(
            registro
        )

        db.session.commit()

        return jsonify({
            "exito": True,

            "ruc":
                datos[
                    "ruc"
                ],

            "razon_social":
                datos[
                    "razon_social"
                ],

            "nombre_comercial":
                datos.get(
                    "nombre_comercial"
                ),

            "direccion":
                datos.get(
                    "direccion"
                ),

            "estado":
                datos.get(
                    "estado"
                ),

            "condicion":
                datos.get(
                    "condicion"
                ),

            "departamento":
                datos.get(
                    "departamento"
                ),

            "provincia":
                datos.get(
                    "provincia"
                ),

            "distrito":
                datos.get(
                    "distrito"
                )
        })

    except (
        ValueError,
        ErrorApisNet
    ) as error:

        db.session.rollback()

        registrar_error_api(
            operacion="CONSULTAR_RUC",
            entidad=entidad,
            mensaje=str(
                error
            )
        )

        return jsonify({
            "exito": False,
            "mensaje": str(
                error
            )
        }), 400


# =========================================================
# GEOAPIFY
# =========================================================

@bp.get(
    "/direcciones"
)
@login_required
def direcciones():

    texto = request.args.get(
        "q",
        ""
    ).strip()

    if len(texto) < 3:

        return jsonify({
            "exito": True,
            "resultados": []
        })

    try:

        resultados = buscar_direcciones(
            texto
        )

        return jsonify({
            "exito": True,
            "resultados": resultados
        })

    except ErrorGeoapify as error:

        return jsonify({
            "exito": False,
            "mensaje": str(
                error
            )
        }), 400


# =========================================================
# REGISTRAR ERROR API
# =========================================================

def registrar_error_api(
    operacion,
    entidad,
    mensaje
):

    try:

        registro = RegistroApi(
            servicio=(
                ServicioApiEnum.APIS_NET
            ),

            operacion=operacion,

            id_usuario=(
                current_user.id_usuario
            ),

            entidad_relacionada=entidad,

            exitoso=False,

            mensaje=mensaje
        )

        db.session.add(
            registro
        )

        db.session.commit()

    except Exception:

        db.session.rollback()