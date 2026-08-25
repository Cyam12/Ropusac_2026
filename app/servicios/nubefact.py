from decimal import (
    Decimal,
    ROUND_HALF_UP
)

import requests

from flask import current_app

from app.utilidades.fechas import (
    fecha_hoy_peru
)


# =========================================================
# CONSTANTES
# =========================================================

FACTOR_IGV = Decimal(
    "1.18"
)


# =========================================================
# ERROR NUBEFACT
# =========================================================

class ErrorNubeFact(
    Exception
):

    def __init__(
        self,
        mensaje,
        codigo_http=None,
        respuesta=None,
        error_conexion=False
    ):

        super().__init__(
            mensaje
        )

        self.codigo_http = (
            codigo_http
        )

        self.respuesta = (
            respuesta
        )

        self.error_conexion = (
            error_conexion
        )


# =========================================================
# CONFIGURACION
# =========================================================

def obtener_configuracion():

    api_url = (
        current_app.config.get(
            "NUBEFACT_API_URL"
        )
    )

    token = (
        current_app.config.get(
            "NUBEFACT_TOKEN"
        )
    )

    serie = (
        current_app.config.get(
            "NUBEFACT_SERIE_BOLETA"
        )
    )

    auth_mode = (
        current_app.config.get(
            "NUBEFACT_AUTH_MODE",
            "TOKEN"
        )
    )

    # =====================================================
    # RUTA
    # =====================================================

    if not api_url:

        raise ErrorNubeFact(
            (
                "NUBEFACT_API_URL "
                "no está configurada."
            )
        )

    # =====================================================
    # TOKEN
    # =====================================================

    if not token:

        raise ErrorNubeFact(
            (
                "NUBEFACT_TOKEN "
                "no está configurado."
            )
        )

    # =====================================================
    # SERIE
    # =====================================================

    if not serie:

        raise ErrorNubeFact(
            (
                "NUBEFACT_SERIE_BOLETA "
                "no está configurada. "
                "Debe colocar en .env la serie "
                "habilitada para su cuenta NubeFact."
            )
        )

    serie = (
        str(
            serie
        )
        .strip()
        .upper()
    )

    if len(
        serie
    ) != 4:

        raise ErrorNubeFact(
            (
                "La serie de boleta de NubeFact "
                "debe tener exactamente "
                "4 caracteres."
            )
        )

    if not serie.startswith(
        "B"
    ):

        raise ErrorNubeFact(
            (
                "La serie configurada para "
                "la boleta debe comenzar con B."
            )
        )

    return {
        "api_url":
            str(
                api_url
            ).strip(),

        "token":
            str(
                token
            ).strip(),

        "serie":
            serie,

        "auth_mode":
            str(
                auth_mode
            ).strip().upper()
    }


# =========================================================
# OBTENER SERIE
# =========================================================

def obtener_serie_boleta():

    return (
        obtener_configuracion()[
            "serie"
        ]
    )


# =========================================================
# HEADERS
# =========================================================

def _headers():

    configuracion = (
        obtener_configuracion()
    )

    token = (
        configuracion[
            "token"
        ]
    )

    if (
        configuracion[
            "auth_mode"
        ]
        == "RAW"
    ):

        authorization = (
            token
        )

    else:

        authorization = (
            f'Token token="{token}"'
        )

    return {
        "Authorization":
            authorization,

        "Content-Type":
            "application/json",

        "Accept":
            "application/json",

        "Cache-Control":
            "no-cache"
    }


# =========================================================
# EXTRAER MENSAJE DE ERROR
# =========================================================

def _mensaje_error(
    datos,
    codigo_http
):

    if not isinstance(
        datos,
        dict
    ):

        return (
            f"NubeFact respondió con "
            f"HTTP {codigo_http}."
        )

    errores = datos.get(
        "errors"
    )

    if errores:

        if isinstance(
            errores,
            dict
        ):

            mensajes = []

            for campo, valor in errores.items():

                if isinstance(
                    valor,
                    list
                ):

                    texto = ", ".join(
                        str(
                            elemento
                        )
                        for elemento in valor
                    )

                else:

                    texto = str(
                        valor
                    )

                mensajes.append(
                    f"{campo}: {texto}"
                )

            return " | ".join(
                mensajes
            )

        return str(
            errores
        )

    return (
        datos.get(
            "mensaje"
        )
        or
        datos.get(
            "message"
        )
        or
        datos.get(
            "sunat_description"
        )
        or
        (
            f"NubeFact respondió con "
            f"HTTP {codigo_http}."
        )
    )


# =========================================================
# POST NUBEFACT
# =========================================================

def _post(
    payload,
    permitir_error_negocio=False
):

    configuracion = (
        obtener_configuracion()
    )

    try:

        respuesta = requests.post(
            configuracion[
                "api_url"
            ],

            json=payload,

            headers=(
                _headers()
            ),

            timeout=45
        )

    except requests.RequestException as error:

        raise ErrorNubeFact(
            (
                "No fue posible conectar "
                "con NubeFact."
            ),

            error_conexion=True
        ) from error

    codigo_http = (
        respuesta.status_code
    )

    try:

        datos = (
            respuesta.json()
        )

    except ValueError as error:

        raise ErrorNubeFact(
            (
                "NubeFact devolvió una "
                "respuesta no válida."
            ),

            codigo_http=(
                codigo_http
            )
        ) from error

    if not respuesta.ok:

        raise ErrorNubeFact(
            _mensaje_error(
                datos,
                codigo_http
            ),

            codigo_http=(
                codigo_http
            ),

            respuesta=(
                datos
            )
        )

    if (
        isinstance(
            datos,
            dict
        )
        and datos.get(
            "errors"
        )
        and not permitir_error_negocio
    ):

        raise ErrorNubeFact(
            _mensaje_error(
                datos,
                codigo_http
            ),

            codigo_http=(
                codigo_http
            ),

            respuesta=(
                datos
            )
        )

    return (
        datos,
        codigo_http
    )


# =========================================================
# DECIMALES
# =========================================================

def _decimal(
    valor
):

    return Decimal(
        str(
            valor
            or 0
        )
    )


def _dos_decimales(
    valor
):

    return _decimal(
        valor
    ).quantize(
        Decimal(
            "0.01"
        ),
        rounding=ROUND_HALF_UP
    )


def _diez_decimales(
    valor
):

    return _decimal(
        valor
    ).quantize(
        Decimal(
            "0.0000000001"
        ),
        rounding=ROUND_HALF_UP
    )


# =========================================================
# DOCUMENTO NUBEFACT
# =========================================================

def _tipo_documento_nubefact(
    tipo_documento
):

    tipo_documento = (
        str(
            tipo_documento
            or ""
        )
        .strip()
        .upper()
    )

    if tipo_documento == "DNI":

        return "1"

    if tipo_documento == "RUC":

        return "6"

    return "-"


def _numero_documento_nubefact(
    tipo_documento,
    numero_documento
):

    tipo_documento = (
        str(
            tipo_documento
            or ""
        )
        .strip()
        .upper()
    )

    if tipo_documento == "SIN_DOCUMENTO":

        return "-"

    return (
        str(
            numero_documento
            or "-"
        )
    )


# =========================================================
# UNIDAD DE MEDIDA
# =========================================================

def _unidad_nubefact(
    unidad
):

    unidad = (
        str(
            unidad
            or ""
        )
        .strip()
        .upper()
    )

    equivalencias = {

        "UNIDAD":
            "NIU",

        "CAJA":
            "NIU",

        "KILOGRAMO":
            "KGM",

        "METRO LINEAL":
            "MTR",

        "GALÓN":
            "GLL",

        "GALON":
            "GLL",

        "ROLLO":
            "NIU",

        "MILLAR":
            "NIU",

        "OTROS":
            "NIU"
    }

    return (
        equivalencias.get(
            unidad,
            "NIU"
        )
    )


# =========================================================
# CONSTRUIR PAYLOAD
# =========================================================

def construir_payload_boleta(
    boleta,
    venta,
    cotizacion,
    detalles
):

    # =====================================================
    # SERIE
    #
    # SIEMPRE TOMAMOS LA SERIE ACTUAL CONFIGURADA.
    #
    # ESTO PERMITE CORREGIR UNA BOLETA QUE HAYA
    # FALLADO PREVIAMENTE CON B001.
    # =====================================================

    serie_nubefact = (
        obtener_serie_boleta()
    )

    # =====================================================
    # FECHA PERU
    #
    # NO USAMOS:
    # date.today()
    # CURRENT_DATE DE UN SERVIDOR UTC
    #
    # SIEMPRE America/Lima.
    # =====================================================

    fecha_emision_peru = (
        fecha_hoy_peru()
    )

    # =====================================================
    # MONEDA
    # =====================================================

    moneda = (
        str(
            venta[
                "moneda"
            ]
        )
        .strip()
        .upper()
    )

    moneda_nubefact = (
        1
        if moneda == "PEN"
        else 2
    )

    # =====================================================
    # TOTALES
    # =====================================================

    items = []

    total_gravada = Decimal(
        "0.00"
    )

    total_igv = Decimal(
        "0.00"
    )

    total_documento = Decimal(
        "0.00"
    )

    # =====================================================
    # ITEMS
    # =====================================================

    for detalle in detalles:

        cantidad = _decimal(
            detalle[
                "cantidad"
            ]
        )

        # =================================================
        # PRECIO FINAL
        #
        # YA INCLUYE IGV
        # =================================================

        precio_final_unitario = (
            _decimal(
                detalle[
                    "precio_unitario"
                ]
            )
        )

        importe_total = (
            _dos_decimales(
                cantidad
                *
                precio_final_unitario
            )
        )

        # =================================================
        # VALOR UNITARIO SIN IGV
        # =================================================

        valor_unitario = (
            _diez_decimales(
                precio_final_unitario
                /
                FACTOR_IGV
            )
        )

        # =================================================
        # SUBTOTAL SIN IGV
        # =================================================

        subtotal_linea = (
            _dos_decimales(
                importe_total
                /
                FACTOR_IGV
            )
        )

        # =================================================
        # IGV INCLUIDO
        # =================================================

        igv_linea = (
            _dos_decimales(
                importe_total
                -
                subtotal_linea
            )
        )

        total_gravada += (
            subtotal_linea
        )

        total_igv += (
            igv_linea
        )

        total_documento += (
            importe_total
        )

        unidad_original = str(
            detalle[
                "unidad_medida"
            ]
            or "Unidad"
        )

        items.append({

            "unidad_de_medida":
                _unidad_nubefact(
                    unidad_original
                ),

            "codigo":
                str(
                    detalle[
                        "codigo_producto"
                    ]
                ),

            "descripcion":
                str(
                    detalle[
                        "nombre_producto"
                    ]
                ),

            "cantidad":
                float(
                    cantidad
                ),

            "valor_unitario":
                float(
                    valor_unitario
                ),

            "precio_unitario":
                float(
                    _dos_decimales(
                        precio_final_unitario
                    )
                ),

            "descuento":
                "",

            "subtotal":
                float(
                    subtotal_linea
                ),

            "tipo_de_igv":
                1,

            "igv":
                float(
                    igv_linea
                ),

            "total":
                float(
                    importe_total
                ),

            "anticipo_regularizacion":
                False,

            "anticipo_documento_serie":
                "",

            "anticipo_documento_numero":
                ""
        })

    # =====================================================
    # REDONDEAR
    # =====================================================

    total_gravada = (
        _dos_decimales(
            total_gravada
        )
    )

    total_igv = (
        _dos_decimales(
            total_igv
        )
    )

    total_documento = (
        _dos_decimales(
            total_documento
        )
    )

    # =====================================================
    # VALIDAR TOTAL
    # =====================================================

    total_venta = (
        _dos_decimales(
            venta[
                "total"
            ]
        )
    )

    diferencia = abs(
        total_documento
        -
        total_venta
    )

    if diferencia > Decimal(
        "0.02"
    ):

        raise ErrorNubeFact(
            (
                "El total de los productos "
                "no coincide con el total "
                "de la venta."
            )
        )

    # =====================================================
    # TIPO DE CAMBIO
    # =====================================================

    if moneda == "PEN":

        tipo_cambio = ""

    else:

        tipo_cambio = float(
            _decimal(
                venta[
                    "tipo_cambio_soles_por_dolar"
                ]
            )
        )

    # =====================================================
    # CLIENTE
    # =====================================================

    tipo_documento = (
        boleta[
            "cliente_tipo_documento"
        ]
    )

    numero_documento = (
        boleta[
            "cliente_numero_documento"
        ]
    )

    # =====================================================
    # PAYLOAD
    # =====================================================

    payload = {

        "operacion":
            "generar_comprobante",

        "tipo_de_comprobante":
            2,

        # =================================================
        # SERIE CORRECTA CONFIGURADA
        # =================================================

        "serie":
            serie_nubefact,

        "numero":
            int(
                boleta[
                    "numero"
                ]
            ),

        "sunat_transaction":
            1,

        "cliente_tipo_de_documento":
            _tipo_documento_nubefact(
                tipo_documento
            ),

        "cliente_numero_de_documento":
            _numero_documento_nubefact(
                tipo_documento,
                numero_documento
            ),

        "cliente_denominacion":
            boleta[
                "cliente_nombre"
            ],

        "cliente_direccion":
            (
                boleta[
                    "cliente_direccion"
                ]
                or ""
            ),

        "cliente_email":
            (
                boleta[
                    "cliente_correo"
                ]
                or ""
            ),

        "cliente_email_1":
            "",

        "cliente_email_2":
            "",

        # =================================================
        # FECHA ACTUAL EN PERU
        # =================================================

        "fecha_de_emision":
            fecha_emision_peru.strftime(
                "%d-%m-%Y"
            ),

        "fecha_de_vencimiento":
            "",

        "moneda":
            moneda_nubefact,

        "tipo_de_cambio":
            tipo_cambio,

        "porcentaje_de_igv":
            18.00,

        "descuento_global":
            "",

        "total_descuento":
            "",

        "total_anticipo":
            "",

        "total_gravada":
            float(
                total_gravada
            ),

        "total_inafecta":
            "",

        "total_exonerada":
            "",

        "total_igv":
            float(
                total_igv
            ),

        "total_gratuita":
            "",

        "total_otros_cargos":
            "",

        "total":
            float(
                total_documento
            ),

        "percepcion_tipo":
            "",

        "percepcion_base_imponible":
            "",

        "total_percepcion":
            "",

        "total_incluido_percepcion":
            "",

        "detraccion":
            False,

        "observaciones":
            (
                f"Venta "
                f"{venta['numero_venta']} "
                f"- Cotización "
                f"{cotizacion['numero_cotizacion']}"
            ),

        "documento_que_se_modifica_tipo":
            "",

        "documento_que_se_modifica_serie":
            "",

        "documento_que_se_modifica_numero":
            "",

        "tipo_de_nota_de_credito":
            "",

        "tipo_de_nota_de_debito":
            "",

        "enviar_automaticamente_a_la_sunat":
            True,

        # =================================================
        # SMTP LO MANEJAMOS NOSOTROS
        # =================================================

        "enviar_automaticamente_al_cliente":
            False,

        "codigo_unico":
            (
                f"ROPUSAC-"
                f"{serie_nubefact}-"
                f"{boleta['numero']}"
            ),

        "condiciones_de_pago":
            "",

        "medio_de_pago":
            "",

        "placa_vehiculo":
            "",

        "orden_compra_servicio":
            "",

        "formato_de_pdf":
            "A4",

        "items":
            items
    }

    return payload


# =========================================================
# NORMALIZAR RESPUESTA
# =========================================================

def normalizar_respuesta(
    datos,
    codigo_http=None
):

    enlace = None
    enlace_pdf = None
    enlace_xml = None
    enlace_cdr = None

    if isinstance(
        datos,
        dict
    ):

        enlace = datos.get(
            "enlace"
        )

        enlace_pdf = (
            datos.get(
                "enlace_del_pdf"
            )
            or
            datos.get(
                "enlace_pdf"
            )
        )

        enlace_xml = (
            datos.get(
                "enlace_del_xml"
            )
            or
            datos.get(
                "enlace_xml"
            )
        )

        enlace_cdr = (
            datos.get(
                "enlace_del_cdr"
            )
            or
            datos.get(
                "enlace_cdr"
            )
        )

    if (
        not enlace_pdf
        and enlace
    ):

        enlace_pdf = (
            f"{enlace}.pdf"
        )

    mensaje = None

    if isinstance(
        datos,
        dict
    ):

        mensaje = (
            datos.get(
                "sunat_description"
            )
            or
            datos.get(
                "mensaje"
            )
            or
            datos.get(
                "sunat_note"
            )
        )

    return {

        "codigo_http":
            codigo_http,

        "tipo_de_comprobante":
            (
                datos.get(
                    "tipo_de_comprobante"
                )
                if isinstance(
                    datos,
                    dict
                )
                else None
            ),

        "serie":
            (
                datos.get(
                    "serie"
                )
                if isinstance(
                    datos,
                    dict
                )
                else None
            ),

        "numero":
            (
                datos.get(
                    "numero"
                )
                if isinstance(
                    datos,
                    dict
                )
                else None
            ),

        "identificador":
            enlace,

        "enlace_pdf":
            enlace_pdf,

        "enlace_xml":
            enlace_xml,

        "enlace_cdr":
            enlace_cdr,

        "codigo_hash":
            (
                datos.get(
                    "codigo_hash"
                )
                if isinstance(
                    datos,
                    dict
                )
                else None
            ),

        "cadena_qr":
            (
                datos.get(
                    "cadena_para_codigo_qr"
                )
                if isinstance(
                    datos,
                    dict
                )
                else None
            ),

        "aceptada_sunat":
            (
                datos.get(
                    "aceptada_por_sunat"
                )
                if isinstance(
                    datos,
                    dict
                )
                else None
            ),

        "mensaje":
            mensaje,

        "raw":
            datos
    }


# =========================================================
# GENERAR BOLETA
# =========================================================

def generar_boleta(
    payload
):

    datos, codigo_http = (
        _post(
            payload
        )
    )

    resultado = (
        normalizar_respuesta(
            datos,
            codigo_http
        )
    )

    # =====================================================
    # SI NUBEFACT NO RETORNA SERIE,
    # CONSERVAMOS LA QUE ENVIAMOS
    # =====================================================

    if not resultado[
        "serie"
    ]:

        resultado[
            "serie"
        ] = payload[
            "serie"
        ]

    if not resultado[
        "numero"
    ]:

        resultado[
            "numero"
        ] = payload[
            "numero"
        ]

    return resultado


# =========================================================
# CONSULTAR BOLETA
# =========================================================

def consultar_boleta(
    serie,
    numero
):

    payload = {

        "operacion":
            "consultar_comprobante",

        "tipo_de_comprobante":
            2,

        "serie":
            serie,

        "numero":
            int(
                numero
            )
    }

    try:

        datos, codigo_http = (
            _post(
                payload,
                permitir_error_negocio=True
            )
        )

    except ErrorNubeFact:

        return None

    if not isinstance(
        datos,
        dict
    ):

        return None

    if datos.get(
        "errors"
    ):

        return None

    if (
        not datos.get(
            "serie"
        )
        and
        not datos.get(
            "enlace"
        )
    ):

        return None

    return normalizar_respuesta(
        datos,
        codigo_http
    )


# =========================================================
# DESCARGAR PDF
# =========================================================

def descargar_pdf(
    url
):

    if not url:

        raise ErrorNubeFact(
            (
                "La boleta no tiene "
                "un PDF disponible."
            )
        )

    try:

        respuesta = requests.get(
            url,
            timeout=30
        )

    except requests.RequestException as error:

        raise ErrorNubeFact(
            (
                "No fue posible descargar "
                "el PDF desde NubeFact."
            ),

            error_conexion=True
        ) from error

    if not respuesta.ok:

        raise ErrorNubeFact(
            (
                "NubeFact no permitió "
                "descargar el PDF "
                "de la boleta."
            ),

            codigo_http=(
                respuesta.status_code
            )
        )

    return (
        respuesta.content
    )