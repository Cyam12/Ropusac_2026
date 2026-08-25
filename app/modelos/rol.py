from app.extensiones import db


class Rol(db.Model):

    __tablename__ = "roles"

    # =====================================================
    # COLUMNAS
    # =====================================================

    id_rol = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    codigo = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
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

    actualizado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now()
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    usuarios = db.relationship(
        "Usuario",
        back_populates="rol",
        lazy="selectin"
    )

    roles_permisos = db.relationship(
        "RolPermiso",
        back_populates="rol",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    permisos = db.relationship(
        "Permiso",
        secondary="roles_permisos",
        viewonly=True,
        lazy="selectin"
    )

    # =====================================================
    # METODOS
    # =====================================================

    def tiene_permiso(self, codigo_permiso):
        """
        Indica si el rol posee un permiso determinado.
        """

        return any(
            permiso.codigo == codigo_permiso
            and permiso.activo
            for permiso in self.permisos
        )

    def __repr__(self):
        return (
            f"<Rol "
            f"id={self.id_rol} "
            f"codigo='{self.codigo}'>"
        )