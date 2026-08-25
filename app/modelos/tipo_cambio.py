from app.extensiones import db


class TipoCambio(db.Model):

    __tablename__ = "tipos_cambio"

    id_tipo_cambio = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    soles_por_dolar = db.Column(
        db.Numeric(12, 6),
        nullable=False
    )

    proveedor = db.Column(
        db.String(100),
        nullable=False,
        default="ExchangeRate-API",
        server_default="ExchangeRate-API"
    )

    fecha_tipo_cambio = db.Column(
        db.Date,
        nullable=False,
        server_default=db.text("CURRENT_DATE")
    )

    obtenido_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    identificador_consulta = db.Column(
        db.String(255),
        nullable=True
    )

    __table_args__ = (

        db.CheckConstraint(
            "soles_por_dolar > 0",
            name="chk_tipo_cambio_positivo"
        ),

        db.Index(
            "idx_tipo_cambio_fecha",
            db.text("fecha_tipo_cambio DESC")
        ),
    )

    cotizaciones = db.relationship(
        "Cotizacion",
        back_populates="tipo_cambio",
        lazy="selectin"
    )

    def __repr__(self):
        return (
            f"<TipoCambio "
            f"id={self.id_tipo_cambio} "
            f"valor={self.soles_por_dolar}>"
        )