from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    request
)

from itsdangerous import (
    BadSignature,
    URLSafeSerializer
)

from app.extensiones import db

from app.modelos import Cotizacion

from app.servicios.pdf_cotizacion import (
    generar_pdf_cotizacion
)


bp = Blueprint(
    "documentos",
    __name__,
    url_prefix="/documentos"
)


# =========================================================
# SERIALIZADOR
# =========================================================

def obtener_serializador():

    return URLSafeSerializer(
        current_app.config[
            "SECRET_KEY"
        ],
        salt="ropusac-cotizacion-pdf"
    )


# =========================================================
# CREAR TOKEN
# =========================================================

def crear_token_cotizacion(
    id_cotizacion
):

    return (
        obtener_serializador()
        .dumps({
            "id_cotizacion":
                id_cotizacion
        })
    )


# =========================================================
# PDF COTIZACION
# =========================================================

@bp.get(
    "/cotizaciones/<token>"
)
def cotizacion_pdf(
    token
):

    try:

        datos = (
            obtener_serializador()
            .loads(
                token
            )
        )

    except BadSignature:

        abort(
            404
        )

    id_cotizacion = datos.get(
        "id_cotizacion"
    )

    if not id_cotizacion:

        abort(
            404
        )

    cotizacion = db.session.get(
        Cotizacion,
        id_cotizacion
    )

    if cotizacion is None:

        abort(
            404
        )

    try:

        contenido = (
            generar_pdf_cotizacion(
                cotizacion.id_cotizacion
            )
        )

    except Exception as error:

        print(
            "ERROR GENERANDO PDF:",
            error
        )

        abort(
            500
        )

    nombre_archivo = (
        cotizacion.pdf_nombre_archivo
        or
        f"{cotizacion.numero_cotizacion}.pdf"
    )

    descargar = (
        request.args.get(
            "descargar",
            ""
        )
        == "1"
    )

    disposicion = (
        "attachment"
        if descargar
        else "inline"
    )

    return Response(
        contenido,

        status=200,

        headers={
            "Content-Type":
                "application/pdf",

            "Content-Disposition":
                (
                    f'{disposicion}; '
                    f'filename="{nombre_archivo}"'
                )
        }
    )