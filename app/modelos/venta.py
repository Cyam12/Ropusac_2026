from app.extensiones import db

from app.modelos.enumerados import (
    EstadoVentaEnum,
    estado_venta_db,
    moneda_db
)


class Venta(db.Model):

    __tablename__ = "ventas"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_venta = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    numero_venta = db.Column(
        db.String(40),
        nullable=False,
        unique=True
    )

    id_cotizacion = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "cotizaciones.id_cotizacion",
            ondelete="RESTRICT"
        ),
        nullable=False,
        unique=True
    )

    id_cliente = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "clientes.id_cliente",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    id_vendedor = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    fecha_venta = db.Column(
        db.Date,
        nullable=False,
        server_default=db.text("CURRENT_DATE")
    )

    moneda = db.Column(
        moneda_db,
        nullable=False
    )

    tipo_cambio_soles_por_dolar = db.Column(
        db.Numeric(12, 6),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    total = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    estado = db.Column(
        estado_venta_db,
        nullable=False,
        default=EstadoVentaEnum.PENDIENTE_BOLETA,
        server_default="PENDIENTE_BOLETA"
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    # =====================================================
    # RESTRICCIONES E INDICES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            "tipo_cambio_soles_por_dolar > 0",
            name="chk_venta_tipo_cambio"
        ),

        db.CheckConstraint(
            """
            subtotal >= 0
            AND total >= 0
            """,
            name="chk_venta_total"
        ),

        db.Index(
            "idx_ventas_cliente",
            "id_cliente"
        ),

        db.Index(
            "idx_ventas_vendedor",
            "id_vendedor"
        ),

        db.Index(
            "idx_ventas_estado",
            "estado"
        ),

        db.Index(
            "idx_ventas_fecha",
            db.text("fecha_venta DESC")
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    cotizacion = db.relationship(
        "Cotizacion",
        back_populates="venta",
        lazy="joined"
    )

    cliente = db.relationship(
        "Cliente",
        back_populates="ventas",
        lazy="joined"
    )

    vendedor = db.relationship(
        "Usuario",
        foreign_keys=[id_vendedor],
        back_populates="ventas",
        lazy="joined"
    )

    detalles = db.relationship(
        "DetalleVenta",
        back_populates="venta",
        lazy="selectin"
    )

    boleta = db.relationship(
        "Boleta",
        back_populates="venta",
        uselist=False,
        lazy="selectin"
    )

    def __repr__(self):

        return (
            f"<Venta "
            f"id={self.id_venta} "
            f"numero='{self.numero_venta}'>"
        )