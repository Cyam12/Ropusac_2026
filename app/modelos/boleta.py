from app.extensiones import db

from app.modelos.enumerados import (
    EstadoBoletaEnum,
    estado_boleta_db,
    moneda_db,
    tipo_documento_db
)


class Boleta(db.Model):

    __tablename__ = "boletas"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_boleta = db.Column(
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
        nullable=False,
        unique=True
    )

    estado = db.Column(
        estado_boleta_db,
        nullable=False,
        default=EstadoBoletaEnum.PENDIENTE,
        server_default="PENDIENTE"
    )

    tipo_comprobante = db.Column(
        db.String(30),
        nullable=False,
        default="BOLETA",
        server_default="BOLETA"
    )

    serie = db.Column(
        db.String(20),
        nullable=True
    )

    numero = db.Column(
        db.String(30),
        nullable=True
    )

    identificador_nubefact = db.Column(
        db.String(255),
        nullable=True
    )

    fecha_emision = db.Column(
        db.Date,
        nullable=True
    )

    moneda = db.Column(
        moneda_db,
        nullable=False
    )

    total = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    # =====================================================
    # SNAPSHOT DEL CLIENTE
    # =====================================================

    cliente_tipo_documento = db.Column(
        tipo_documento_db,
        nullable=True
    )

    cliente_numero_documento = db.Column(
        db.String(20),
        nullable=True
    )

    cliente_nombre = db.Column(
        db.String(250),
        nullable=False
    )

    cliente_direccion = db.Column(
        db.String(300),
        nullable=True
    )

    cliente_correo = db.Column(
        db.String(180),
        nullable=True
    )

    # =====================================================
    # NUBEFACT
    # =====================================================

    enlace_pdf = db.Column(
        db.Text,
        nullable=True
    )

    enlace_xml = db.Column(
        db.Text,
        nullable=True
    )

    enlace_cdr = db.Column(
        db.Text,
        nullable=True
    )

    codigo_hash = db.Column(
        db.Text,
        nullable=True
    )

    cadena_codigo_qr = db.Column(
        db.Text,
        nullable=True
    )

    respuesta_nubefact = db.Column(
        db.JSON,
        nullable=True
    )

    mensaje_nubefact = db.Column(
        db.Text,
        nullable=True
    )

    generada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    creada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    actualizada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    # =====================================================
    # RESTRICCIONES E INDICES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            "total >= 0",
            name="chk_boleta_total"
        ),

        db.Index(
            "uq_boleta_serie_numero",
            "serie",
            "numero",
            unique=True,
            postgresql_where=db.text(
                "serie IS NOT NULL "
                "AND numero IS NOT NULL"
            )
        ),

        db.Index(
            "idx_boletas_estado",
            "estado"
        ),

        db.Index(
            "idx_boletas_venta",
            "id_venta"
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    venta = db.relationship(
        "Venta",
        back_populates="boleta",
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<Boleta "
            f"id={self.id_boleta} "
            f"serie='{self.serie}' "
            f"numero='{self.numero}'>"
        )

    envios_correo = db.relationship(
        "EnvioCorreo",
        back_populates="boleta",
        lazy="selectin"
    )