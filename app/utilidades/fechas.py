from datetime import datetime

from zoneinfo import ZoneInfo


# =========================================================
# ZONA HORARIA DEL SISTEMA
# =========================================================

ZONA_HORARIA_PERU = ZoneInfo(
    "America/Lima"
)


# =========================================================
# FECHA Y HORA PERU
# =========================================================

def ahora_peru():

    return datetime.now(
        ZONA_HORARIA_PERU
    )


# =========================================================
# FECHA ACTUAL PERU
# =========================================================

def fecha_hoy_peru():

    return ahora_peru().date()