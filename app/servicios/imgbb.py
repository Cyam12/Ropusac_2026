from pathlib import Path

import requests

from flask import current_app

from werkzeug.utils import secure_filename


class ErrorImgBB(Exception):

    def __init__(
        self,
        mensaje,
        codigo_http=None
    ):

        super().__init__(
            mensaje
        )

        self.codigo_http = (
            codigo_http
        )


# =========================================================
# CONFIGURACION
# =========================================================

EXTENSIONES_PERMITIDAS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif"
}


TAMANO_MAXIMO = (
    32
    * 1024
    * 1024
)


# =========================================================
# VALIDAR IMAGEN
# =========================================================

def validar_imagen(
    archivo
):

    if (
        archivo is None
        or not archivo.filename
    ):

        raise ErrorImgBB(
            "Debe seleccionar una imagen."
        )

    nombre_archivo = (
        secure_filename(
            archivo.filename
        )
    )

    if not nombre_archivo:

        raise ErrorImgBB(
            "El nombre del archivo no es válido."
        )

    extension = (
        Path(
            nombre_archivo
        )
        .suffix
        .lower()
    )

    if (
        extension
        not in EXTENSIONES_PERMITIDAS
    ):

        raise ErrorImgBB(
            "Formato de imagen no permitido. "
            "Use JPG, JPEG, PNG, WEBP o GIF."
        )

    if (
        not archivo.mimetype
        or not archivo.mimetype.startswith(
            "image/"
        )
    ):

        raise ErrorImgBB(
            "El archivo seleccionado no es una imagen válida."
        )

    contenido = archivo.read()

    archivo.seek(
        0
    )

    if not contenido:

        raise ErrorImgBB(
            "La imagen está vacía."
        )

    if (
        len(contenido)
        > TAMANO_MAXIMO
    ):

        raise ErrorImgBB(
            "La imagen no puede superar los 32 MB."
        )

    return {
        "nombre_archivo":
            nombre_archivo,

        "contenido":
            contenido,

        "mimetype":
            archivo.mimetype
    }


# =========================================================
# SUBIR A IMGBB
# =========================================================

def subir_imagen(
    archivo
):

    api_key = current_app.config.get(
        "IMGBB_API_KEY"
    )

    host = current_app.config.get(
        "IMGBB_HOST"
    )

    if not api_key:

        raise ErrorImgBB(
            "IMGBB_API_KEY no está configurado."
        )

    if not host:

        raise ErrorImgBB(
            "IMGBB_HOST no está configurado."
        )

    imagen = validar_imagen(
        archivo
    )

    url = (
        f"https://{host}/1/upload"
    )

    try:

        respuesta = requests.post(
            url,

            params={
                "key":
                    api_key.strip()
            },

            files={
                "image": (
                    imagen[
                        "nombre_archivo"
                    ],
                    imagen[
                        "contenido"
                    ],
                    imagen[
                        "mimetype"
                    ]
                )
            },

            timeout=40
        )

    except requests.Timeout as error:

        raise ErrorImgBB(
            "La subida a ImgBB excedió "
            "el tiempo de espera."
        ) from error

    except requests.ConnectionError as error:

        raise ErrorImgBB(
            "No fue posible conectar con ImgBB."
        ) from error

    except requests.RequestException as error:

        raise ErrorImgBB(
            "Ocurrió un error al subir "
            "la imagen a ImgBB."
        ) from error

    try:

        respuesta_json = (
            respuesta.json()
        )

    except ValueError as error:

        raise ErrorImgBB(
            "ImgBB devolvió una respuesta inválida.",
            respuesta.status_code
        ) from error

    if (
        not respuesta.ok
        or not respuesta_json.get(
            "success"
        )
    ):

        error_api = (
            respuesta_json.get(
                "error"
            )
            or {}
        )

        mensaje = (
            error_api.get(
                "message"
            )
            if isinstance(
                error_api,
                dict
            )
            else None
        )

        raise ErrorImgBB(
            mensaje
            or
            "ImgBB no pudo subir la imagen.",
            respuesta.status_code
        )

    datos = respuesta_json.get(
        "data"
    )

    if not isinstance(
        datos,
        dict
    ):

        raise ErrorImgBB(
            "ImgBB no devolvió los datos "
            "de la imagen.",
            respuesta.status_code
        )

    url_imagen = (
        datos.get(
            "url"
        )
        or (
            datos.get(
                "image"
            )
            or {}
        ).get(
            "url"
        )
    )

    if not url_imagen:

        raise ErrorImgBB(
            "ImgBB no devolvió la URL "
            "de la imagen.",
            respuesta.status_code
        )

    return {
        "codigo_http":
            respuesta.status_code,

        "id_imagen_externa":
            datos.get(
                "id"
            ),

        "url_imagen":
            url_imagen,

        "url_visualizacion":
            datos.get(
                "url_viewer"
            )
            or datos.get(
                "display_url"
            ),

        "url_eliminacion":
            datos.get(
                "delete_url"
            ),

        "nombre_archivo_original":
            imagen[
                "nombre_archivo"
            ]
    }