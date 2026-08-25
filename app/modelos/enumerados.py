from enum import Enum

from sqlalchemy.dialects.postgresql import ENUM


# =========================================================
# ENUMS DE PYTHON
# =========================================================


class TipoDocumentoEnum(str, Enum):
    DNI = "DNI"
    RUC = "RUC"
    SIN_DOCUMENTO = "SIN_DOCUMENTO"


class MonedaEnum(str, Enum):
    PEN = "PEN"
    USD = "USD"


class EstadoCotizacionEnum(str, Enum):
    BORRADOR = "BORRADOR"
    EMITIDA = "EMITIDA"
    ENVIADA = "ENVIADA"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    VENCIDA = "VENCIDA"
    CONVERTIDA_VENTA = "CONVERTIDA_VENTA"
    ANULADA = "ANULADA"


class EstadoImportacionEnum(str, Enum):
    PROCESANDO = "PROCESANDO"
    COMPLETADA = "COMPLETADA"
    COMPLETADA_CON_ERRORES = "COMPLETADA_CON_ERRORES"
    FALLIDA = "FALLIDA"


class EstadoVentaEnum(str, Enum):
    PENDIENTE_BOLETA = "PENDIENTE_BOLETA"
    FACTURADA = "FACTURADA"
    ANULADA = "ANULADA"


class EstadoBoletaEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    GENERADA = "GENERADA"
    ERROR = "ERROR"
    ANULADA = "ANULADA"


class EstadoEnvioEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    ERROR = "ERROR"


class TipoDocumentoEnvioEnum(str, Enum):
    COTIZACION = "COTIZACION"
    BOLETA = "BOLETA"


class ServicioApiEnum(str, Enum):
    APIS_NET = "APIS_NET"
    GEOAPIFY = "GEOAPIFY"
    IMGBB = "IMGBB"
    EXCHANGE_RATE = "EXCHANGE_RATE"
    NUBEFACT = "NUBEFACT"
    SMTP = "SMTP"


# =========================================================
# ENUMS POSTGRESQL EXISTENTES
# =========================================================
#
# create_type=False:
# SQLAlchemy NO intentara crear estos ENUMS.
# Ya existen en PostgreSQL porque fueron creados
# mediante BASE DE DATOS ROPUSAC.sql.
# =========================================================


tipo_documento_db = ENUM(
    TipoDocumentoEnum,
    name="tipo_documento_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


moneda_db = ENUM(
    MonedaEnum,
    name="moneda_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


estado_cotizacion_db = ENUM(
    EstadoCotizacionEnum,
    name="estado_cotizacion_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


estado_importacion_db = ENUM(
    EstadoImportacionEnum,
    name="estado_importacion_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


estado_venta_db = ENUM(
    EstadoVentaEnum,
    name="estado_venta_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


estado_boleta_db = ENUM(
    EstadoBoletaEnum,
    name="estado_boleta_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


estado_envio_db = ENUM(
    EstadoEnvioEnum,
    name="estado_envio_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


tipo_documento_envio_db = ENUM(
    TipoDocumentoEnvioEnum,
    name="tipo_documento_envio_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)


servicio_api_db = ENUM(
    ServicioApiEnum,
    name="servicio_api_enum",
    create_type=False,
    values_callable=lambda enumerado: [
        elemento.value
        for elemento in enumerado
    ],
)