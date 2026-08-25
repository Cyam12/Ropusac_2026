import os

from dotenv import load_dotenv


# =========================================================
# VARIABLES DE ENTORNO
# =========================================================

load_dotenv()


# =========================================================
# DATABASE URL
# =========================================================

def obtener_database_url():

    database_url = os.getenv(
        "DATABASE_URL"
    )

    if not database_url:

        raise RuntimeError(
            "DATABASE_URL no está configurada."
        )

    if database_url.startswith(
        "postgres://"
    ):

        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    return database_url


# =========================================================
# CONFIGURACION BASE
# =========================================================

class Config:

    # =====================================================
    # GENERAL
    # =====================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY"
    )

    APP_TIMEZONE = os.getenv(
        "APP_TIMEZONE",
        "America/Lima"
    )

    # =====================================================
    # POSTGRESQL / NEON
    # =====================================================

    SQLALCHEMY_DATABASE_URI = (
        obtener_database_url()
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = (
        False
    )

    # =====================================================
    # POOL REDUCIDO
    #
    # RENDER FREE = 512 MB
    # GUNICORN = 1 WORKER
    # =====================================================

    SQLALCHEMY_ENGINE_OPTIONS = {

        "pool_pre_ping":
            True,

        "pool_recycle":
            240,

        # Solo dos conexiones persistentes.
        "pool_size":
            2,

        # No abrir conexiones adicionales
        # durante picos.
        "max_overflow":
            0,

        "pool_timeout":
            15,

        "pool_use_lifo":
            True,

        "connect_args": {

            "connect_timeout":
                10,

            "keepalives":
                1,

            "keepalives_idle":
                30,

            "keepalives_interval":
                10,

            "keepalives_count":
                5,

            "options":
                "-c timezone=America/Lima"
        }
    }

    # =====================================================
    # APIS.NET
    # =====================================================

    APIS_NET_PE_TOKEN = os.getenv(
        "APIS_NET_PE_TOKEN"
    )

    APIS_NET_PE_BASE_URL = os.getenv(
        "APIS_NET_PE_BASE_URL",
        "https://api.decolecta.com/v1"
    )

    # =====================================================
    # GEOAPIFY
    # =====================================================

    GEOAPIFY_API_KEY = os.getenv(
        "GEOAPIFY_API_KEY"
    )

    # =====================================================
    # IMGBB
    # =====================================================

    IMGBB_API_KEY = os.getenv(
        "IMGBB_API_KEY"
    )

    IMGBB_HOST = os.getenv(
        "IMGBB_HOST",
        "api.imgbb.com"
    )

    # =====================================================
    # EXCHANGERATE-API
    # =====================================================

    EXCHANGE_RATE_API_KEY = os.getenv(
        "EXCHANGE_RATE_API_KEY"
    )

    EXCHANGE_RATE_BASE_URL = os.getenv(
        "EXCHANGE_RATE_BASE_URL",
        "https://v6.exchangerate-api.com/v6"
    )

    # =====================================================
    # NUBEFACT
    # =====================================================

    NUBEFACT_API_URL = os.getenv(
        "NUBEFACT_API_URL"
    )

    NUBEFACT_TOKEN = os.getenv(
        "NUBEFACT_TOKEN"
    )

    NUBEFACT_SERIE_BOLETA = os.getenv(
        "NUBEFACT_SERIE_BOLETA"
    )

    NUBEFACT_AUTH_MODE = os.getenv(
        "NUBEFACT_AUTH_MODE",
        "TOKEN"
    )

    # =====================================================
    # SMTP
    # =====================================================

    SMTP_HOST = os.getenv(
        "SMTP_HOST"
    )

    SMTP_PORT = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    SMTP_USER = os.getenv(
        "SMTP_USER"
    )

    SMTP_PASSWORD = os.getenv(
        "SMTP_PASSWORD"
    )

    SMTP_FROM_EMAIL = os.getenv(
        "SMTP_FROM_EMAIL"
    )

    SMTP_FROM_NAME = os.getenv(
        "SMTP_FROM_NAME",
        "ROPUSAC"
    )

    SMTP_USE_TLS = (
        os.getenv(
            "SMTP_USE_TLS",
            "true"
        ).lower()
        in (
            "1",
            "true",
            "yes",
            "si"
        )
    )

    SMTP_USE_SSL = (
        os.getenv(
            "SMTP_USE_SSL",
            "false"
        ).lower()
        in (
            "1",
            "true",
            "yes",
            "si"
        )
    )


# =========================================================
# DESARROLLO
# =========================================================

class ConfigDesarrollo(
    Config
):

    DEBUG = True


# =========================================================
# PRODUCCION
# =========================================================

class ConfigProduccion(
    Config
):

    DEBUG = False