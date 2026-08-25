from app.extensiones import db


class ImagenProducto(db.Model):

    __tablename__ = "imagenes_productos"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_imagen_producto = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    id_producto = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "productos.id_producto",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    id_imagen_externa = db.Column(
        db.String(255),
        nullable=True
    )

    url_imagen = db.Column(
        db.Text,
        nullable=False
    )

    url_visualizacion = db.Column(
        db.Text,
        nullable=True
    )

    url_eliminacion = db.Column(
        db.Text,
        nullable=True
    )

    nombre_archivo_original = db.Column(
        db.String(255),
        nullable=True
    )

    es_principal = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text("TRUE")
    )

    activa = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text("TRUE")
    )

    subida_por = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id_usuario",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    creada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    eliminada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # =====================================================
    # INDICES
    # =====================================================

    __table_args__ = (

        db.Index(
            "idx_imagenes_producto",
            "id_producto"
        ),

        db.Index(
            "uq_imagen_principal_producto",
            "id_producto",
            unique=True,
            postgresql_where=db.text(
                "es_principal = TRUE "
                "AND activa = TRUE"
            )
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    producto = db.relationship(
        "Producto",
        back_populates="imagenes"
    )

    usuario_subida = db.relationship(
        "Usuario",
        foreign_keys=[subida_por],
        lazy="joined"
    )

    # =====================================================
    # REPRESENTACION
    # =====================================================

    def __repr__(self):

        return (
            f"<ImagenProducto "
            f"id={self.id_imagen_producto} "
            f"producto={self.id_producto}>"
        )