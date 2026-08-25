from pathlib import Path
from sqlalchemy import text
from alembic import op


# =========================================================
# IDENTIFICADORES ALEMBIC
# =========================================================

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


# =========================================================
# RUTA DEL SCRIPT SQL PRINCIPAL
# =========================================================

RUTA_PROYECTO = Path(__file__).resolve().parents[2]

RUTA_ESQUEMA = (
    RUTA_PROYECTO
    / "sql"
    / "esquema_inicial_ropusac.sql"
)


# =========================================================
# UPGRADE
# =========================================================

def upgrade():

    if not RUTA_ESQUEMA.exists():

        raise FileNotFoundError(
            f"No se encontro el archivo SQL: "
            f"{RUTA_ESQUEMA}"
        )

    sql_esquema = RUTA_ESQUEMA.read_text(
        encoding="utf-8"
    )

    conexion = op.get_bind()

    conexion.execute(
        text(sql_esquema)
    )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade():

    raise RuntimeError(
        "La migracion baseline de ROPUSAC no puede "
        "revertirse automaticamente porque contiene "
        "el esquema estructural completo del sistema."
    )