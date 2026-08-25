from app.extensiones import db

from app.modelos.enumerados import (
    EstadoEnvioEnum,
    estado_envio_db,
    tipo_documento_envio_db
)


class EnvioCorreo(db.Model):

    __tablename__ = "envios_correo"

    id_envio_correo = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    tipo_documento = db.Column(
        tipo_documento_envio_db,
        nullable=False
    )

    id_cotizacion = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "cotizaciones.id_cotizacion",
            ondelete="RESTRICT"
        ),
        nullable=True
    )

    id_boleta = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "boletas.id_boleta",
            ondelete="RESTRICT"
        ),
        nullable=True
    )

    destinatario = db.Column(
        db.String(180),
        nullable=False
    )

    asunto = db.Column(
        db.String(300),
        nullable=False
    )

    estado = db.Column(
        estado_envio_db,
        nullable=False,
        default=EstadoEnvioEnum.PENDIENTE,
        server_default="PENDIENTE"
    )

    numero_intento = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1"
    )

    mensaje_error = db.Column(
        db.Text,
        nullable=True
    )

    enviado_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    enviado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    __table_args__ = (

        db.CheckConstraint(
            """
            (
                tipo_documento = 'COTIZACION'
                AND id_cotizacion IS NOT NULL
                AND id_boleta IS NULL
            )
            OR
            (
                tipo_documento = 'BOLETA'
                AND id_boleta IS NOT NULL
                AND id_cotizacion IS NULL
            )
            """,
            name="chk_envio_documento"
        ),

        db.CheckConstraint(
            "numero_intento > 0",
            name="chk_numero_intento"
        ),

        db.Index(
            "idx_envios_cotizacion",
            "id_cotizacion"
        ),

        db.Index(
            "idx_envios_boleta",
            "id_boleta"
        ),

        db.Index(
            "idx_envios_estado",
            "estado"
        ),
    )

    cotizacion = db.relationship(
        "Cotizacion",
        back_populates="envios_correo",
        lazy="joined"
    )

    boleta = db.relationship(
        "Boleta",
        back_populates="envios_correo",
        lazy="joined"
    )

    usuario_envio = db.relationship(
        "Usuario",
        foreign_keys=[enviado_por],
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<EnvioCorreo "
            f"id={self.id_envio_correo} "
            f"estado='{self.estado}'>"
        )