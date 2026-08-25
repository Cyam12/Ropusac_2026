import os

import requests


class ErrorGeoapify(Exception):
    pass


def buscar_direcciones(texto):

    texto = (
        texto
        or ""
    ).strip()

    if len(texto) < 3:

        return []

    api_key = os.getenv(
        "GEOAPIFY_API_KEY"
    )

    if not api_key:

        raise ErrorGeoapify(
            "No se ha configurado GEOAPIFY_API_KEY."
        )

    url = (
        "https://api.geoapify.com/"
        "v1/geocode/autocomplete"
    )

    try:

        respuesta = requests.get(
            url,

            params={
                "text": texto,
                "format": "json",
                "filter": "countrycode:pe",
                "lang": "es",
                "limit": 6,
                "apiKey": api_key
            },

            timeout=10
        )

    except requests.RequestException as error:

        raise ErrorGeoapify(
            "No fue posible conectar con Geoapify."
        ) from error

    if respuesta.status_code != 200:

        raise ErrorGeoapify(
            "Geoapify no pudo procesar la consulta."
        )

    try:

        datos = respuesta.json()

    except ValueError as error:

        raise ErrorGeoapify(
            "Geoapify devolvió una respuesta inválida."
        ) from error

    resultados = []

    for resultado in datos.get(
        "results",
        []
    ):

        direccion = resultado.get(
            "formatted"
        )

        if not direccion:
            continue

        resultados.append({
            "direccion":
                direccion,

            "place_id":
                resultado.get(
                    "place_id"
                ),

            "latitud":
                resultado.get(
                    "lat"
                ),

            "longitud":
                resultado.get(
                    "lon"
                )
        })

    return resultados