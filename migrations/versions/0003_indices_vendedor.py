from alembic import op



revision = "0003_indices_vendedor"

down_revision = "0002_stock_productos"

branch_labels = None

depends_on = None


# =========================================================
# UPGRADE
#
# INDICES DE RENDIMIENTO PARA EL ECOSISTEMA VENDEDOR.
#
# NO MODIFICA:
#
# - TABLAS
# - COLUMNAS
# - ENUMS
# - TRIGGERS
# - VISTAS
# - FOREIGN KEYS
# - DATOS
# - LOGICA DE NEGOCIO
#
# SOLO AGREGA UN INDICE PARA ACELERAR
# CONSULTAS POR creador DEL CLIENTE.
# =========================================================

def upgrade():

    # =====================================================
    # CLIENTES -> CREADO POR
    #
    # UTILIZADO PRINCIPALMENTE EN:
    #
    # Dashboard Vendedor
    #
    # SELECT COUNT(*)
    # FROM clientes
    # WHERE creado_por = :id_usuario
    #
    # POSTGRESQL NO CREA AUTOMATICAMENTE UN INDICE
    # PARA UNA FOREIGN KEY.
    # =====================================================

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_clientes_creado_por
        ON clientes (creado_por);
        """
    )

    # =====================================================
    # ACTUALIZAR ESTADISTICAS
    #
    # AYUDA AL PLANIFICADOR DE POSTGRESQL
    # A ELEGIR MEJORES PLANES DE EJECUCION.
    # =====================================================

    op.execute(
        """
        ANALYZE clientes;
        """
    )

    op.execute(
        """
        ANALYZE cotizaciones;
        """
    )

    op.execute(
        """
        ANALYZE ventas;
        """
    )

    op.execute(
        """
        ANALYZE boletas;
        """
    )


# =========================================================
# DOWNGRADE
#
# SOLO ELIMINA EL INDICE CREADO
# POR ESTA MIGRACION.
# =========================================================

def downgrade():

    op.execute(
        """
        DROP INDEX IF EXISTS
            idx_clientes_creado_por;
        """
    )