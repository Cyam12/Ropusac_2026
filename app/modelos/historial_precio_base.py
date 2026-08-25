from app.extensiones import db


class HistorialPrecioBase(db.Model):

    __tablename__ = "historial_precios_base"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_historial_precio_base = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_producto = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "productos.id_producto",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    precio_anterior = db.Column(
        db.Numeric(14, 2),
        nullable=True
    )

    precio_nuevo = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    cambiado_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    cambiado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    # =====================================================
    # INDICES
    # =====================================================

    __table_args__ = (
        db.Index(
            "idx_historial_base_producto",
            "id_producto"
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    producto = db.relationship(
        "Producto",
        back_populates="historial_precios_base"
    )

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[cambiado_por],
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<HistorialPrecioBase "
            f"id={self.id_historial_precio_base} "
            f"producto={self.id_producto}>"
        )