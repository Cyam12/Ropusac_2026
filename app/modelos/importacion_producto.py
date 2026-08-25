from sqlalchemy.dialects.postgresql import JSONB
from app.extensiones import db

from app.modelos.enumerados import (
    EstadoImportacionEnum,
    estado_importacion_db
)


class ImportacionProducto(db.Model):

    __tablename__ = "importaciones_productos"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_importacion = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    nombre_archivo = db.Column(
        db.String(255),
        nullable=False
    )

    estado = db.Column(
        estado_importacion_db,
        nullable=False,
        default=EstadoImportacionEnum.PROCESANDO,
        server_default="PROCESANDO"
    )

    total_filas = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    filas_correctas = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    filas_con_error = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    detalle_errores = db.Column(
        JSONB,
        nullable=True
    )

    importado_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    iniciado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    finalizado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # =====================================================
    # RESTRICCIONES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            """
            total_filas >= 0
            AND filas_correctas >= 0
            AND filas_con_error >= 0
            """,
            name="chk_importacion_totales"
        ),

    )

    # =====================================================
    # RELACIONES
    # =====================================================

    usuario_importador = db.relationship(
        "Usuario",
        foreign_keys=[importado_por],
        lazy="joined"
    )

    def __repr__(self):

        return (
            f"<ImportacionProducto "
            f"id={self.id_importacion} "
            f"archivo='{self.nombre_archivo}'>"
        )