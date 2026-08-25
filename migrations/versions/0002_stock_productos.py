from alembic import op

import sqlalchemy as sa


# =========================================================
# IDENTIFICADORES ALEMBIC
# =========================================================

revision = "0002_stock_productos"

down_revision = "0001_baseline"

branch_labels = None

depends_on = None


# =========================================================
# UPGRADE
# =========================================================

def upgrade():

    # =====================================================
    # AGREGAR STOCK
    # =====================================================

    op.add_column(
        "productos",

        sa.Column(
            "stock_disponible",
            sa.Numeric(
                14,
                3
            ),
            nullable=False,
            server_default=sa.text(
                "0"
            )
        )
    )

    op.create_check_constraint(
        "chk_stock_disponible",
        "productos",
        "stock_disponible >= 0"
    )

    # =====================================================
    # ACTUALIZAR VISTA DEL CATALOGO
    # =====================================================

    op.execute(
        """
        CREATE OR REPLACE VIEW vista_catalogo_productos AS

        SELECT
            p.id_producto,
            p.codigo_producto,
            p.nombre,
            p.descripcion,
            p.categoria,
            p.marca,
            p.modelo,
            p.unidad_medida,

            p.precio_venta_actual,
            p.moneda_precio,

            pr.id_proveedor,
            pr.razon_social AS proveedor,

            ip.url_imagen,
            ip.url_visualizacion,

            p.stock_disponible

        FROM productos p

        INNER JOIN proveedores pr
            ON pr.id_proveedor = p.id_proveedor

        LEFT JOIN imagenes_productos ip
            ON ip.id_producto = p.id_producto
            AND ip.es_principal = TRUE
            AND ip.activa = TRUE

        WHERE
            p.activo = TRUE
            AND pr.activo = TRUE
            AND p.precio_venta_actual IS NOT NULL;
        """
    )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade():

    # =====================================================
    # RESTAURAR VISTA
    # =====================================================

    op.execute(
        """
        CREATE OR REPLACE VIEW vista_catalogo_productos AS

        SELECT
            p.id_producto,
            p.codigo_producto,
            p.nombre,
            p.descripcion,
            p.categoria,
            p.marca,
            p.modelo,
            p.unidad_medida,

            p.precio_venta_actual,
            p.moneda_precio,

            pr.id_proveedor,
            pr.razon_social AS proveedor,

            ip.url_imagen,
            ip.url_visualizacion

        FROM productos p

        INNER JOIN proveedores pr
            ON pr.id_proveedor = p.id_proveedor

        LEFT JOIN imagenes_productos ip
            ON ip.id_producto = p.id_producto
            AND ip.es_principal = TRUE
            AND ip.activa = TRUE

        WHERE
            p.activo = TRUE
            AND pr.activo = TRUE
            AND p.precio_venta_actual IS NOT NULL;
        """
    )

    op.drop_constraint(
        "chk_stock_disponible",
        "productos",
        type_="check"
    )

    op.drop_column(
        "productos",
        "stock_disponible"
    )