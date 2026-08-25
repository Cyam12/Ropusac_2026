from app.extensiones import db

from app.modelos.enumerados import (
    MonedaEnum,
    EstadoCotizacionEnum,
    moneda_db,
    estado_cotizacion_db
)


class Cotizacion(db.Model):

    __tablename__ = "cotizaciones"

    id_cotizacion = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    numero_cotizacion = db.Column(
        db.String(40),
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

    id_tipo_cambio = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "tipos_cambio.id_tipo_cambio",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    moneda = db.Column(
        moneda_db,
        nullable=False
    )

    tipo_cambio_soles_por_dolar = db.Column(
        db.Numeric(12, 6),
        nullable=False
    )

    fecha_emision = db.Column(
        db.Date,
        nullable=False,
        server_default=db.text("CURRENT_DATE")
    )

    fecha_vigencia = db.Column(
        db.Date,
        nullable=False
    )

    estado = db.Column(
        estado_cotizacion_db,
        nullable=False,
        default=EstadoCotizacionEnum.BORRADOR,
        server_default="BORRADOR"
    )

    subtotal = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    total_equivalente = db.Column(
        db.Numeric(14, 2),
        db.Computed(
            """
            CASE
                WHEN moneda = 'PEN'
                    THEN ROUND(
                        total / tipo_cambio_soles_por_dolar,
                        2
                    )
                ELSE
                    ROUND(
                        total * tipo_cambio_soles_por_dolar,
                        2
                    )
            END
            """,
            persisted=True
        )
    )

    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    pdf_nombre_archivo = db.Column(
        db.String(255),
        nullable=True
    )

    pdf_url = db.Column(
        db.Text,
        nullable=True
    )

    pdf_generado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    enviada_correo_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    aprobada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    actualizado_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    actualizado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    __table_args__ = (

        db.CheckConstraint(
            "fecha_vigencia >= fecha_emision",
            name="chk_cotizacion_vigencia"
        ),

        db.CheckConstraint(
            "tipo_cambio_soles_por_dolar > 0",
            name="chk_cotizacion_tipo_cambio"
        ),

        db.CheckConstraint(
            """
            subtotal >= 0
            AND total >= 0
            """,
            name="chk_cotizacion_total"
        ),

        db.Index(
            "idx_cotizacion_cliente",
            "id_cliente"
        ),

        db.Index(
            "idx_cotizacion_vendedor",
            "id_vendedor"
        ),

        db.Index(
            "idx_cotizacion_estado",
            "estado"
        ),

        db.Index(
            "idx_cotizacion_vigencia",
            "fecha_vigencia"
        ),

        db.Index(
            "idx_cotizaciones_fecha",
            db.text("fecha_emision DESC")
        ),
    )

    cliente = db.relationship(
        "Cliente",
        back_populates="cotizaciones",
        lazy="joined"
    )

    vendedor = db.relationship(
        "Usuario",
        foreign_keys=[id_vendedor],
        lazy="joined"
    )

    usuario_actualizador = db.relationship(
        "Usuario",
        foreign_keys=[actualizado_por],
        lazy="joined"
    )

    tipo_cambio = db.relationship(
        "TipoCambio",
        back_populates="cotizaciones",
        lazy="joined"
    )

    detalles = db.relationship(
        "DetalleCotizacion",
        back_populates="cotizacion",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    historial_estados = db.relationship(
        "HistorialEstadoCotizacion",
        back_populates="cotizacion",
        lazy="selectin"
    )
    venta = db.relationship(
        "Venta",
        back_populates="cotizacion",
        uselist=False,
        lazy="selectin"
    )
    envios_correo = db.relationship(
        "EnvioCorreo",
        back_populates="cotizacion",
        lazy="selectin"
    )

    def __repr__(self):
        return (
            f"<Cotizacion "
            f"id={self.id_cotizacion} "
            f"numero='{self.numero_cotizacion}'>"
        )