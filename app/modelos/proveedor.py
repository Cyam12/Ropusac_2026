from app.extensiones import db

from app.modelos.enumerados import (
    TipoDocumentoEnum,
    tipo_documento_db
)


class Proveedor(db.Model):

    __tablename__ = "proveedores"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_proveedor = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    tipo_documento = db.Column(
        tipo_documento_db,
        nullable=False,
        default=TipoDocumentoEnum.SIN_DOCUMENTO,
        server_default="SIN_DOCUMENTO"
    )

    numero_documento = db.Column(
        db.String(20),
        nullable=True
    )

    razon_social = db.Column(
        db.String(200),
        nullable=False
    )

    nombre_comercial = db.Column(
        db.String(200),
        nullable=True
    )

    correo = db.Column(
        db.String(180),
        nullable=True
    )

    celular = db.Column(
        db.String(30),
        nullable=True
    )

    telefono = db.Column(
        db.String(30),
        nullable=True
    )

    direccion_fiscal = db.Column(
        db.String(300),
        nullable=True
    )

    datos_obtenidos_api = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text("FALSE")
    )

    api_consultada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text("TRUE")
    )

    creado_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=False
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

    # =====================================================
    # RESTRICCIONES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            """
            tipo_documento IN (
                'RUC',
                'SIN_DOCUMENTO'
            )
            """,
            name="chk_proveedor_tipo_documento"
        ),

        db.CheckConstraint(
            """
            (
                tipo_documento = 'RUC'
                AND numero_documento ~ '^[0-9]{11}$'
            )
            OR
            (
                tipo_documento = 'SIN_DOCUMENTO'
                AND numero_documento IS NULL
            )
            """,
            name="chk_proveedor_documento"
        ),

        db.Index(
            "uq_proveedores_documento",
            numero_documento,
            unique=True,
            postgresql_where=numero_documento.is_not(None)
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    usuario_creador = db.relationship(
        "Usuario",
        foreign_keys=[creado_por],
        lazy="joined"
    )

    usuario_actualizador = db.relationship(
        "Usuario",
        foreign_keys=[actualizado_por],
        lazy="joined"
    )
    productos = db.relationship(
        "Producto",
        back_populates="proveedor",
        lazy="selectin"
    )

    # =====================================================
    # REPRESENTACION
    # =====================================================

    def __repr__(self):

        return (
            f"<Proveedor "
            f"id={self.id_proveedor} "
            f"razon_social='{self.razon_social}'>"
        )