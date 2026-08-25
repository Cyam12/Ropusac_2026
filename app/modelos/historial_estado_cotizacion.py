from app.extensiones import db

from app.modelos.enumerados import (
    estado_cotizacion_db
)


class HistorialEstadoCotizacion(db.Model):

    __tablename__ = "historial_estados_cotizacion"

    id_historial_estado = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_cotizacion = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "cotizaciones.id_cotizacion",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    estado_anterior = db.Column(
        estado_cotizacion_db,
        nullable=True
    )

    estado_nuevo = db.Column(
        estado_cotizacion_db,
        nullable=False
    )

    cambiado_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=True
    )

    observacion = db.Column(
        db.String(500),
        nullable=True
    )

    cambiado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    __table_args__ = (

        db.Index(
            "idx_historial_estado_cotizacion",
            "id_cotizacion"
        ),

    )

    cotizacion = db.relationship(
        "Cotizacion",
        back_populates="historial_estados"
    )

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[cambiado_por],
        lazy="joined"
    )

    def __repr__(self):
        return (
            f"<HistorialEstadoCotizacion "
            f"id={self.id_historial_estado} "
            f"cotizacion={self.id_cotizacion}>"
        )