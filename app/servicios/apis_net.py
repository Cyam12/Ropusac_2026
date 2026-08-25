import requests

from flask import current_app


class ErrorApisNet(Exception):
    pass


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def _primer_valor(
    datos,
    *claves
):

    if not isinstance(
        datos,
        dict
    ):

        return None

    for clave in claves:

        if clave not in datos:
            continue

        valor = datos.get(
            clave
        )

        if valor is None:
            continue

        if isinstance(
            valor,
            str
        ):

            valor = valor.strip()

            if not valor:
                continue

        return valor

    return None


def _texto(
    valor
):

    if valor is None:
        return ""

    return " ".join(
        str(valor)
        .strip()
        .split()
    )


def _extraer_data(
    respuesta
):

    if not isinstance(
        respuesta,
        dict
    ):

        raise ErrorApisNet(
            "La API devolvió una respuesta no válida."
        )

    data = respuesta.get(
        "data"
    )

    if isinstance(
        data,
        dict
    ):

        return data

    resultado = respuesta.get(
        "resultado"
    )

    if isinstance(
        resultado,
        dict
    ):

        return resultado

    result = respuesta.get(
        "result"
    )

    if isinstance(
        result,
        dict
    ):

        return result

    return respuesta


def _consultar_api(
    endpoint,
    numero,
    tipo_documento
):

    token = current_app.config.get(
        "APIS_NET_PE_TOKEN"
    )

    base_url = current_app.config.get(
        "APIS_NET_PE_BASE_URL"
    )

    if not token:

        raise ErrorApisNet(
            "APIS_NET_PE_TOKEN no está configurado."
        )

    if not base_url:

        raise ErrorApisNet(
            "APIS_NET_PE_BASE_URL no está configurado."
        )

    token = token.strip()

    base_url = base_url.rstrip(
        "/"
    )

    url = (
        f"{base_url}{endpoint}"
    )

    headers = {
        "Accept":
            "application/json",

        "Authorization":
            f"Bearer {token}"
    }

    try:

        respuesta_http = requests.get(
            url,

            params={
                "numero": numero
            },

            headers=headers,

            timeout=15
        )

    except requests.Timeout as error:

        raise ErrorApisNet(
            f"La consulta de {tipo_documento} "
            "excedió el tiempo de espera."
        ) from error

    except requests.ConnectionError as error:

        raise ErrorApisNet(
            "No fue posible conectar con APIS.NET."
        ) from error

    except requests.RequestException as error:

        raise ErrorApisNet(
            "Ocurrió un error al consultar APIS.NET."
        ) from error

    try:

        respuesta_json = (
            respuesta_http.json()
        )

    except ValueError:

        respuesta_json = {}

    if respuesta_http.status_code in (
        401,
        403
    ):

        raise ErrorApisNet(
            "El token de APIS.NET no está autorizado."
        )

    if respuesta_http.status_code == 404:

        mensaje = _primer_valor(
            respuesta_json,
            "message",
            "mensaje",
            "error",
            "detail"
        )

        raise ErrorApisNet(
            _texto(
                mensaje
            )
            if mensaje
            else
            (
                "No se encontró información "
                f"para el {tipo_documento}."
            )
        )

    if respuesta_http.status_code == 422:

        mensaje = _primer_valor(
            respuesta_json,
            "message",
            "mensaje",
            "error",
            "detail"
        )

        raise ErrorApisNet(
            _texto(
                mensaje
            )
            if mensaje
            else
            (
                f"El {tipo_documento} "
                "ingresado no es válido."
            )
        )

    if not respuesta_http.ok:

        mensaje = _primer_valor(
            respuesta_json,
            "message",
            "mensaje",
            "error",
            "detail"
        )

        if mensaje:

            raise ErrorApisNet(
                _texto(
                    mensaje
                )
            )

        raise ErrorApisNet(
            "APIS.NET respondió con código "
            f"{respuesta_http.status_code}."
        )

    return _extraer_data(
        respuesta_json
    )


# =========================================================
# CONSULTAR DNI
# =========================================================

def consultar_dni(
    dni
):

    dni = str(
        dni or ""
    ).strip()

    if (
        not dni.isdigit()
        or len(dni) != 8
    ):

        raise ValueError(
            "El DNI debe contener exactamente 8 dígitos."
        )

    datos = _consultar_api(
        endpoint="/reniec/dni",
        numero=dni,
        tipo_documento="DNI"
    )

    numero_documento = (
        _primer_valor(
            datos,
            "numero_documento",
            "numeroDocumento",
            "document_number",
            "dni",
            "numero"
        )
        or dni
    )

    nombres = (
        _primer_valor(
            datos,
            "first_name",
            "first_names",
            "nombres",
            "nombre_nombres",
            "given_names",
            "names"
        )
        or ""
    )

    apellido_paterno = (
        _primer_valor(
            datos,
            "first_last_name",
            "apellido_paterno",
            "apellidoPaterno",
            "primer_apellido",
            "first_surname",
            "paternal_surname"
        )
        or ""
    )

    apellido_materno = (
        _primer_valor(
            datos,
            "second_last_name",
            "apellido_materno",
            "apellidoMaterno",
            "segundo_apellido",
            "second_surname",
            "maternal_surname"
        )
        or ""
    )

    nombres = _texto(
        nombres
    )

    apellido_paterno = _texto(
        apellido_paterno
    )

    apellido_materno = _texto(
        apellido_materno
    )

    apellidos = " ".join(
        parte
        for parte in [
            apellido_paterno,
            apellido_materno
        ]
        if parte
    ).strip()

    nombre_completo = " ".join(
        parte
        for parte in [
            nombres,
            apellido_paterno,
            apellido_materno
        ]
        if parte
    ).strip()

    if not nombre_completo:

        nombre_completo_api = (
            _primer_valor(
                datos,
                "full_name",
                "nombre_completo",
                "nombreCompleto",
                "nombre"
            )
        )

        if nombre_completo_api:

            nombre_completo = (
                _texto(
                    nombre_completo_api
                )
            )

    encontrado = bool(
        nombres
        or apellido_paterno
        or apellido_materno
        or nombre_completo
    )

    if not encontrado:

        raise ErrorApisNet(
            "La consulta fue procesada, pero "
            "la API no devolvió datos de la persona."
        )

    return {
        "encontrado":
            True,

        "numero_documento":
            _texto(
                numero_documento
            ),

        "nombres":
            nombres,

        "apellido_paterno":
            apellido_paterno,

        "apellido_materno":
            apellido_materno,

        "apellidos":
            apellidos,

        "nombre_completo":
            nombre_completo,

        "direccion":
            _primer_valor(
                datos,
                "direccion",
                "domicilio",
                "address"
            ),

        "ubigeo":
            _primer_valor(
                datos,
                "ubigeo"
            ),

        "distrito":
            _primer_valor(
                datos,
                "distrito",
                "district"
            ),

        "provincia":
            _primer_valor(
                datos,
                "provincia",
                "province"
            ),

        "departamento":
            _primer_valor(
                datos,
                "departamento",
                "department"
            ),

        "respuesta":
            datos
    }


# =========================================================
# CONSULTAR RUC
# =========================================================

def consultar_ruc(
    ruc
):

    ruc = str(
        ruc or ""
    ).strip()

    if (
        not ruc.isdigit()
        or len(ruc) != 11
    ):

        raise ValueError(
            "El RUC debe contener exactamente 11 dígitos."
        )

    datos = _consultar_api(
        endpoint="/sunat/ruc",
        numero=ruc,
        tipo_documento="RUC"
    )

    numero_documento = (
        _primer_valor(
            datos,
            "numero_documento",
            "numeroDocumento",
            "document_number",
            "ruc"
        )
        or ruc
    )

    razon_social = (
        _primer_valor(
            datos,
            "razon_social",
            "razonSocial",
            "business_name",
            "nombre"
        )
        or ""
    )

    nombre_comercial = (
        _primer_valor(
            datos,
            "nombre_comercial",
            "nombreComercial",
            "trade_name"
        )
    )

    estado = (
        _primer_valor(
            datos,
            "estado",
            "status"
        )
    )

    condicion = (
        _primer_valor(
            datos,
            "condicion",
            "condition"
        )
    )

    direccion = (
        _primer_valor(
            datos,
            "direccion",
            "address"
        )
    )

    ubigeo = (
        _primer_valor(
            datos,
            "ubigeo"
        )
    )

    distrito = (
        _primer_valor(
            datos,
            "distrito",
            "district"
        )
    )

    provincia = (
        _primer_valor(
            datos,
            "provincia",
            "province"
        )
    )

    departamento = (
        _primer_valor(
            datos,
            "departamento",
            "department"
        )
    )

    razon_social = _texto(
        razon_social
    )

    nombre_comercial = (
        _texto(
            nombre_comercial
        )
        if nombre_comercial
        else None
    )

    direccion = (
        _texto(
            direccion
        )
        if direccion
        else None
    )

    if not razon_social:

        raise ErrorApisNet(
            "La consulta fue procesada, pero "
            "la API no devolvió la razón social."
        )

    return {
        "encontrado":
            True,

        "ruc":
            _texto(
                numero_documento
            ),

        "razon_social":
            razon_social,

        "nombre_comercial":
            nombre_comercial,

        "estado":
            _texto(
                estado
            )
            if estado
            else None,

        "condicion":
            _texto(
                condicion
            )
            if condicion
            else None,

        "direccion":
            direccion,

        "ubigeo":
            _texto(
                ubigeo
            )
            if ubigeo
            else None,

        "distrito":
            _texto(
                distrito
            )
            if distrito
            else None,

        "provincia":
            _texto(
                provincia
            )
            if provincia
            else None,

        "departamento":
            _texto(
                departamento
            )
            if departamento
            else None,

        "respuesta":
            datos
    }