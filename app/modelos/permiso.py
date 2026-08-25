from app.extensiones import db


class Permiso(db.Model):

    __tablename__ = "permisos"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_permiso = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    codigo = db.Column(
        db.String(80),
        nullable=False,
        unique=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(
        db.String(255),
        nullable=True
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text("TRUE")
    )

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    roles_permisos = db.relationship(
        "RolPermiso",
        back_populates="permiso",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    roles = db.relationship(
        "Rol",
        secondary="roles_permisos",
        viewonly=True,
        lazy="selectin"
    )

    # =====================================================
    # REPRESENTACION
    # =====================================================

    def __repr__(self):
        return (
            f"<Permiso "
            f"id={self.id_permiso} "
            f"codigo='{self.codigo}'>"
        )