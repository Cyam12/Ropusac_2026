from decimal import (
    Decimal,
    InvalidOperation
)

import requests

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

    if not api_key:

        raise ErrorExchangeRate(
            (
                "EXCHANGE_RATE_API_KEY "
                "no está configurada."
            )
        )

    if not base_url:

        raise ErrorExchangeRate(
            (
                "EXCHANGE_RATE_BASE_URL "
                "no está configurada."
            )
        )

    url = (
        f"{base_url.rstrip('/')}"
        "/pair/USD/PEN"
    )

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
            timeout=15
        )

    except requests.RequestException as error:

        raise ErrorExchangeRate(
            (
                "No fue posible conectar "
                "con ExchangeRate-API."
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

    if not respuesta.ok:

        mensaje = (
            datos.get(
                "error-type"
            )
            or
            "Error consultando ExchangeRate-API."
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

        raise ErrorExchangeRate(
            (
                datos.get(
                    "error-type"
                )
                or
                "ExchangeRate-API rechazó la consulta."
            ),
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

    if tasa <= 0:

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