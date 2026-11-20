from decimal import (
    Decimal,
    InvalidOperation
)

import requests

from urllib.parse import urlsplit, urlunsplit

from flask import current_app


# =========================================================
# ERROR
# =========================================================

class ErrorExchangeRate(
    Exception
):

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
# OBTENER SOLES POR DOLAR
#
# 1 USD = X PEN
# =========================================================

def obtener_soles_por_dolar():

    api_key = current_app.config.get(
        "EXCHANGE_RATE_API_KEY"
    )

    base_url = current_app.config.get(
        "EXCHANGE_RATE_BASE_URL"
    )

    if not api_key or not str(api_key).strip():

        raise ErrorExchangeRate(
            (
                "EXCHANGE_RATE_API_KEY "
                "no está configurada."
            )
        )

    if not base_url or not str(base_url).strip():

        raise ErrorExchangeRate(
            (
                "EXCHANGE_RATE_BASE_URL "
                "no está configurada."
            )
        )

    api_key = str(api_key).strip()
    base_url = str(base_url).strip().rstrip("/")

    try:

        partes_url = urlsplit(
            base_url
        )

        if (
            partes_url.scheme not in ("https", "http")
            or not partes_url.netloc
        ):

            raise ValueError(
                "La URL base no es válida."
            )

        segmentos = [
            segmento
            for segmento in partes_url.path.split("/")
            if segmento
        ]

        # Acepta tanto la URL base /v6 como una URL que
        # ya contenga la clave o el endpoint completo.
        # La clave se envía exclusivamente por Bearer.
        indice_version = next(
            (
                indice
                for indice, segmento in enumerate(segmentos)
                if segmento.lower() in ("v6", "v7")
            ),
            None
        )

        if indice_version is not None:

            ruta_base = (
                "/"
                + "/".join(
                    segmentos[:indice_version + 1]
                )
            )

        else:

            ruta_base = (
                partes_url.path.rstrip("/")
            )

        url = urlunsplit(
            (
                partes_url.scheme,
                partes_url.netloc,
                ruta_base + "/pair/USD/PEN",
                "",
                ""
            )
        )

    except ValueError as error:

        raise ErrorExchangeRate(
            (
                "EXCHANGE_RATE_BASE_URL no tiene "
                "un formato válido."
            )
        ) from error

    headers = {
        "Accept":
            "application/json",

        "Authorization":
            f"Bearer {api_key}"
    }

    try:

        respuesta = requests.get(
            url,
            headers=headers,
            timeout=(4, 8)
        )

    except requests.RequestException as error:

        current_app.logger.warning(
            "ExchangeRate-API: fallo de conexión (%s).",
            type(error).__name__
        )

        raise ErrorExchangeRate(
            (
                "No fue posible conectar con "
                "ExchangeRate-API. "
                f"Detalle: {type(error).__name__}."
            )
        ) from error

    codigo_http = (
        respuesta.status_code
    )

    try:

        datos = respuesta.json()

    except ValueError as error:

        raise ErrorExchangeRate(
            (
                "ExchangeRate-API devolvió "
                "una respuesta no válida."
            ),
            codigo_http=codigo_http
        ) from error

    if not isinstance(datos, dict):

        raise ErrorExchangeRate(
            (
                "ExchangeRate-API devolvió "
                "un formato de respuesta inesperado."
            ),
            codigo_http=codigo_http
        )

    if not respuesta.ok:

        mensaje = (
            datos.get(
                "error-type"
            )
            or
            "Error consultando ExchangeRate-API."
        )

        current_app.logger.warning(
            "ExchangeRate-API respondió HTTP %s: %s.",
            codigo_http,
            mensaje
        )

        raise ErrorExchangeRate(
            mensaje,
            codigo_http=codigo_http
        )

    if (
        datos.get(
            "result"
        )
        != "success"
    ):

        mensaje = (
            datos.get(
                "error-type"
            )
            or
            "ExchangeRate-API rechazó la consulta."
        )

        current_app.logger.warning(
            "ExchangeRate-API rechazó la consulta: %s.",
            mensaje
        )

        raise ErrorExchangeRate(
            mensaje,
            codigo_http=codigo_http
        )

    tasa = datos.get(
        "conversion_rate"
    )

    try:

        tasa = Decimal(
            str(
                tasa
            )
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ) as error:

        raise ErrorExchangeRate(
            (
                "ExchangeRate-API no devolvió "
                "un tipo de cambio válido."
            ),
            codigo_http=codigo_http
        ) from error

    if (
        not tasa.is_finite()
        or tasa <= 0
    ):

        raise ErrorExchangeRate(
            (
                "El tipo de cambio obtenido "
                "no es válido."
            ),
            codigo_http=codigo_http
        )

    identificador = (
        str(
            datos.get(
                "time_last_update_unix"
            )
        )
        if datos.get(
            "time_last_update_unix"
        )
        else None
    )

    return {
        "soles_por_dolar":
            tasa,

        "codigo_http":
            codigo_http,

        "identificador":
            identificador,

        "actualizado_en":
            datos.get(
                "time_last_update_utc"
            )
    }
