from sqlalchemy.dialects.postgresql import JSONB

from app.extensiones import db

from app.modelos.enumerados import (
    servicio_api_db
)


class RegistroApi(db.Model):

    __tablename__ = "registros_api"

    id_registro_api = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    servicio = db.Column(
        servicio_api_db,
        nullable=False
    )

    operacion = db.Column(
        db.String(120),
        nullable=False
    )

    id_usuario = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    entidad_relacionada = db.Column(
        db.String(80),
        nullable=True
    )

    id_entidad_relacionada = db.Column(
        db.BigInteger,
        nullable=True
    )

    codigo_http = db.Column(
        db.Integer,
        nullable=True
    )

    exitoso = db.Column(
        db.Boolean,
        nullable=False
    )

    identificador_externo = db.Column(
        db.String(255),
        nullable=True
    )

    mensaje = db.Column(
        db.Text,
        nullable=True
    )

    respuesta_resumida = db.Column(
        JSONB,
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    __table_args__ = (

        db.Index(
            "idx_registros_api_servicio",
            "servicio"
        ),

        db.Index(
            "idx_registros_api_fecha",
            db.text("creado_en DESC")
        ),
    )

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[id_usuario],
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<RegistroApi "
            f"id={self.id_registro_api} "
            f"servicio='{self.servicio}' "
            f"exitoso={self.exitoso}>"
        )