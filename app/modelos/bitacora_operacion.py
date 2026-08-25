from sqlalchemy.dialects.postgresql import JSONB

from app.extensiones import db


class BitacoraOperacion(db.Model):

    __tablename__ = "bitacora_operaciones"

    id_bitacora = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_usuario = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    accion = db.Column(
        db.String(100),
        nullable=False
    )

    modulo = db.Column(
        db.String(100),
        nullable=False
    )

    entidad = db.Column(
        db.String(100),
        nullable=True
    )

    id_entidad = db.Column(
        db.BigInteger,
        nullable=True
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    datos_adicionales = db.Column(
        JSONB,
        nullable=True
    )

    direccion_ip = db.Column(
        db.String(50),
        nullable=True
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    __table_args__ = (

        db.Index(
            "idx_bitacora_usuario",
            "id_usuario"
        ),

        db.Index(
            "idx_bitacora_fecha",
            db.text("creado_en DESC")
        ),

        db.Index(
            "idx_bitacora_modulo",
            "modulo"
        ),
    )

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[id_usuario],
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<BitacoraOperacion "
            f"id={self.id_bitacora} "
            f"accion='{self.accion}' "
            f"modulo='{self.modulo}'>"
        )