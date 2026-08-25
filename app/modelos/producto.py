from app.extensiones import db

from app.modelos.enumerados import (
    moneda_db
)


class Producto(db.Model):

    __tablename__ = "productos"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_producto = db.Column(
        db.BigInteger,
        primary_key=True
    )

    id_proveedor = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "proveedores.id_proveedor",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    codigo_producto = db.Column(
        db.String(60),
        nullable=False,
        unique=True
    )

    codigo_proveedor = db.Column(
        db.String(100),
        nullable=True
    )

    nombre = db.Column(
        db.String(200),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    categoria = db.Column(
        db.String(150),
        nullable=True
    )

    marca = db.Column(
        db.String(120),
        nullable=True
    )

    modelo = db.Column(
        db.String(120),
        nullable=True
    )

    unidad_medida = db.Column(
        db.String(50),
        nullable=False,
        default="UNIDAD",
        server_default="UNIDAD"
    )

    precio_base_actual = db.Column(
        db.Numeric(
            14,
            2
        ),
        nullable=False
    )

    precio_venta_actual = db.Column(
        db.Numeric(
            14,
            2
        ),
        nullable=True
    )

    moneda_precio = db.Column(
        moneda_db,
        nullable=False,
        default="PEN",
        server_default="PEN"
    )

    # =====================================================
    # STOCK
    # =====================================================

    stock_disponible = db.Column(
        db.Numeric(
            14,
            3
        ),
        nullable=False,
        default=0,
        server_default="0"
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.true()
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
        db.DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=db.func.now()
    )

    actualizado_en = db.Column(
        db.DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=db.func.now()
    )

    # =====================================================
    # RESTRICCIONES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            "precio_base_actual >= 0",
            name="chk_precio_base"
        ),

        db.CheckConstraint(
            """
            precio_venta_actual IS NULL
            OR precio_venta_actual >= 0
            """,
            name="chk_precio_venta"
        ),

        db.CheckConstraint(
            "stock_disponible >= 0",
            name="chk_stock_disponible"
        ),

        db.Index(
            "idx_productos_proveedor",
            "id_proveedor"
        ),

        db.Index(
            "idx_productos_nombre",
            "nombre"
        ),

        db.Index(
            "idx_productos_activos",
            "activo"
        ),
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    proveedor = db.relationship(
        "Proveedor",
        back_populates="productos"
    )

    creador = db.relationship(
        "Usuario",
        foreign_keys=[
            creado_por
        ]
    )

    actualizador = db.relationship(
        "Usuario",
        foreign_keys=[
            actualizado_por
        ]
    )

    imagenes = db.relationship(
        "ImagenProducto",
        back_populates="producto",
        cascade="all, delete-orphan"
    )

    historial_precios_base = db.relationship(
        "HistorialPrecioBase",
        back_populates="producto"
    )

    historial_precios_venta = db.relationship(
        "HistorialPrecioVenta",
        back_populates="producto"
    )

    detalles_cotizaciones = db.relationship(
        "DetalleCotizacion",
        back_populates="producto"
    )

    detalles_ventas = db.relationship(
        "DetalleVenta",
        back_populates="producto"
    )

    # =====================================================
    # PROPIEDADES
    # =====================================================

    @property
    def imagen_principal(self):

        for imagen in self.imagenes:

            if (
                imagen.activa
                and imagen.es_principal
            ):

                return imagen

        return None

    @property
    def tiene_precio_venta(self):

        return (
            self.precio_venta_actual
            is not None
        )

    @property
    def tiene_stock(self):

        return (
            self.stock_disponible
            is not None
            and self.stock_disponible > 0
        )

    def __repr__(self):

        return (
            f"<Producto "
            f"{self.codigo_producto} "
            f"{self.nombre}>"
        )