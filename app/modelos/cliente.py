from app.extensiones import db

from app.modelos.enumerados import (
    TipoDocumentoEnum,
    tipo_documento_db
)


class Cliente(db.Model):

    __tablename__ = "clientes"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_cliente = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    tipo_documento = db.Column(
        tipo_documento_db,
        nullable=False
    )

    numero_documento = db.Column(
        db.String(20),
        nullable=True
    )

    nombres = db.Column(
        db.String(150),
        nullable=True
    )

    apellidos = db.Column(
        db.String(150),
        nullable=True
    )

    razon_social = db.Column(
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

    direccion = db.Column(
        db.String(300),
        nullable=True
    )

    geoapify_place_id = db.Column(
        db.String(255),
        nullable=True
    )

    latitud = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    longitud = db.Column(
        db.Numeric(10, 7),
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
    # RESTRICCIONES E INDICES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            """
            (
                tipo_documento = 'DNI'
                AND numero_documento ~ '^[0-9]{8}$'
            )
            OR
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
            name="chk_cliente_documento"
        ),

        db.CheckConstraint(
            """
            razon_social IS NOT NULL
            OR nombres IS NOT NULL
            """,
            name="chk_cliente_nombre"
        ),

        db.CheckConstraint(
            """
            latitud IS NULL
            OR latitud BETWEEN -90 AND 90
            """,
            name="chk_cliente_latitud"
        ),

        db.CheckConstraint(
            """
            longitud IS NULL
            OR longitud BETWEEN -180 AND 180
            """,
            name="chk_cliente_longitud"
        ),

        db.Index(
            "uq_clientes_documento",
            numero_documento,
            unique=True,
            postgresql_where=numero_documento.is_not(None)
        ),

        db.Index(
            "idx_clientes_correo",
            db.func.lower(correo)
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
    cotizaciones = db.relationship(
        "Cotizacion",
        back_populates="cliente",
        lazy="selectin"
    )
    ventas = db.relationship(
        "Venta",
        back_populates="cliente",
        lazy="selectin"
    )

    # =====================================================
    # PROPIEDADES
    # =====================================================

    @property
    def nombre_completo(self):

        if self.razon_social:
            return self.razon_social

        return " ".join(
            parte
            for parte in [
                self.nombres,
                self.apellidos
            ]
            if parte
        ).strip()

    # =====================================================
    # REPRESENTACION
    # =====================================================

    def __repr__(self):

        return (
            f"<Cliente "
            f"id={self.id_cliente} "
            f"nombre='{self.nombre_completo}'>"
        )