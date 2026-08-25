from app.extensiones import db


class RolPermiso(db.Model):

    __tablename__ = "roles_permisos"

    # =====================================================
    # CLAVE PRIMARIA COMPUESTA
    # =====================================================

    id_rol = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "roles.id_rol",
            ondelete="CASCADE"
        ),
        primary_key=True,
        nullable=False
    )

    id_permiso = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "permisos.id_permiso",
            ondelete="CASCADE"
        ),
        primary_key=True,
        nullable=False
    )

    # =====================================================
    # RELACIONES
    # =====================================================

    rol = db.relationship(
        "Rol",
        back_populates="roles_permisos"
    )

    permiso = db.relationship(
        "Permiso",
        back_populates="roles_permisos"
    )

    # =====================================================
    # REPRESENTACION
    # =====================================================

    def __repr__(self):
        return (
            f"<RolPermiso "
            f"rol={self.id_rol} "
            f"permiso={self.id_permiso}>"
        )