from app.extensiones import db


class DetalleCotizacion(db.Model):

    __tablename__ = "detalle_cotizaciones"

    id_detalle_cotizacion = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_cotizacion = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "cotizaciones.id_cotizacion",
            ondelete="CASCADE"
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

    precio_unitario_pen_referencia = db.Column(
        db.Numeric(14, 2),
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

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    __table_args__ = (

        db.CheckConstraint(
            "cantidad > 0",
            name="chk_detalle_cantidad"
        ),

        db.CheckConstraint(
            """
            precio_unitario >= 0
            AND precio_unitario_pen_referencia >= 0
            """,
            name="chk_detalle_precio"
        ),

        db.Index(
            "idx_detalle_cotizacion",
            "id_cotizacion"
        ),

        db.Index(
            "idx_detalle_cotizacion_producto",
            "id_producto"
        ),
    )

    cotizacion = db.relationship(
        "Cotizacion",
        back_populates="detalles"
    )

    producto = db.relationship(
        "Producto",
        back_populates="detalles_cotizaciones",
        lazy="joined"
    )

    def __repr__(self):
        return (
            f"<DetalleCotizacion "
            f"id={self.id_detalle_cotizacion} "
            f"producto={self.id_producto}>"
        )