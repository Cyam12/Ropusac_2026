from app.extensiones import db


class DetalleVenta(db.Model):

    __tablename__ = "detalle_ventas"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_detalle_venta = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_venta = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "ventas.id_venta",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    id_producto = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "productos.id_producto",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    codigo_producto = db.Column(
        db.String(60),
        nullable=False
    )

    nombre_producto = db.Column(
        db.String(200),
        nullable=False
    )

    cantidad = db.Column(
        db.Numeric(14, 3),
        nullable=False
    )

    precio_unitario = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(14, 2),
        db.Computed(
            "ROUND(cantidad * precio_unitario, 2)",
            persisted=True
        )
    )

    # =====================================================
    # RESTRICCIONES E INDICES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            "cantidad > 0",
            name="chk_detalle_venta_cantidad"
        ),

        db.CheckConstraint(
            "precio_unitario >= 0",
            name="chk_detalle_venta_precio"
        ),

        db.Index(
            "idx_detalle_venta",
            "id_venta"
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    venta = db.relationship(
        "Venta",
        back_populates="detalles"
    )

    producto = db.relationship(
        "Producto",
        back_populates="detalles_ventas",
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<DetalleVenta "
            f"id={self.id_detalle_venta} "
            f"venta={self.id_venta} "
            f"producto={self.id_producto}>"
        )