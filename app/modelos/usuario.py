from flask_login import UserMixin

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.extensiones import (
    db,
    login_manager
)

from app.modelos.enumerados import (
    TipoDocumentoEnum,
    tipo_documento_db
)


class Usuario(
    UserMixin,
    db.Model
):

    __tablename__ = "usuarios"


    # =====================================================
    # COLUMNAS
    # =====================================================

    id_usuario = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )


    id_rol = db.Column(
        db.BigInteger,

        db.ForeignKey(
            "roles.id_rol",
            ondelete="RESTRICT"
        ),

        nullable=False
    )


    tipo_documento = db.Column(
        tipo_documento_db,
        nullable=False,
        default=TipoDocumentoEnum.SIN_DOCUMENTO,
        server_default="SIN_DOCUMENTO"
    )


    numero_documento = db.Column(
        db.String(
            20
        ),
        nullable=True
    )


    nombres = db.Column(
        db.String(
            120
        ),
        nullable=False
    )


    apellidos = db.Column(
        db.String(
            120
        ),
        nullable=False
    )


    correo = db.Column(
        db.String(
            180
        ),
        nullable=False
    )


    hash_contrasena = db.Column(
        db.String(
            255
        ),
        nullable=False
    )


    celular = db.Column(
        db.String(
            30
        ),
        nullable=True
    )


    direccion = db.Column(
        db.String(
            300
        ),
        nullable=True
    )


    geoapify_place_id = db.Column(
        db.String(
            255
        ),
        nullable=True
    )


    latitud = db.Column(
        db.Numeric(
            10,
            7
        ),
        nullable=True
    )


    longitud = db.Column(
        db.Numeric(
            10,
            7
        ),
        nullable=True
    )


    datos_obtenidos_api = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text(
            "FALSE"
        )
    )


    api_consultada_en = db.Column(
        db.DateTime(
            timezone=True
        ),
        nullable=True
    )


    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text(
            "TRUE"
        )
    )


    ultimo_acceso_en = db.Column(
        db.DateTime(
            timezone=True
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
    # RESTRICCIONES E INDICES
    # =====================================================

    __table_args__ = (

        db.CheckConstraint(
            """
            tipo_documento IN (
                'DNI',
                'SIN_DOCUMENTO'
            )
            """,
            name="chk_usuario_tipo_documento"
        ),

        db.CheckConstraint(
            """
            (
                tipo_documento = 'DNI'
                AND numero_documento ~ '^[0-9]{8}$'
            )
            OR
            (
                tipo_documento = 'SIN_DOCUMENTO'
                AND numero_documento IS NULL
            )
            """,
            name="chk_usuario_documento"
        ),

        db.CheckConstraint(
            """
            latitud IS NULL
            OR latitud BETWEEN -90 AND 90
            """,
            name="chk_usuario_latitud"
        ),

        db.CheckConstraint(
            """
            longitud IS NULL
            OR longitud BETWEEN -180 AND 180
            """,
            name="chk_usuario_longitud"
        ),

        db.Index(
            "uq_usuarios_correo",
            db.func.lower(
                correo
            ),
            unique=True
        ),

        db.Index(
            "uq_usuarios_documento",
            numero_documento,
            unique=True,
            postgresql_where=(
                numero_documento.is_not(
                    None
                )
            )
        ),
    )


    # =====================================================
    # RELACIONES
    # =====================================================

    # =====================================================
    # ROL
    #
    # SE CONSERVA JOINED.
    #
    # ES UNA RELACION PEQUEÑA Y codigo_rol SE UTILIZA
    # CONSTANTEMENTE PARA AUTORIZACION.
    #
    # ESTO PERMITE QUE:
    #
    # current_user.codigo_rol
    #
    # NO NECESITE UNA CONSULTA POSTERIOR.
    # =====================================================

    rol = db.relationship(
        "Rol",
        back_populates="usuarios",
        lazy="joined"
    )


    # =====================================================
    # VENTAS
    #
    # IMPORTANTE:
    #
    # ANTES:
    #
    # lazy="selectin"
    #
    # ESO HACIA QUE CADA VEZ QUE SE CARGABA UN USUARIO
    # SQLALCHEMY CONSULTARA TAMBIEN SUS VENTAS.
    #
    # ESTO AFECTABA ESPECIALMENTE:
    #
    # - LOGIN
    # - USER_LOADER DE FLASK-LOGIN
    # - LOGOUT
    # - CUALQUIER CONSULTA DE USUARIOS
    #
    # AHORA:
    #
    # lazy="select"
    #
    # LAS VENTAS SOLO SE CONSULTAN SI ALGUNA PARTE
    # DEL SISTEMA HACE EXPLICITAMENTE:
    #
    # usuario.ventas
    #
    # LA LOGICA DE LA RELACION SE CONSERVA.
    # =====================================================

    ventas = db.relationship(
        "Venta",
        foreign_keys="Venta.id_vendedor",
        back_populates="vendedor",
        lazy="select"
    )


    # =====================================================
    # CONTRASEÑA
    # =====================================================

    def establecer_contrasena(
        self,
        contrasena
    ):
        """
        Genera un hash seguro y nunca almacena
        la contraseña original.
        """

        if not contrasena:

            raise ValueError(
                "La contraseña no puede estar vacía."
            )

        self.hash_contrasena = (
            generate_password_hash(
                contrasena
            )
        )


    def verificar_contrasena(
        self,
        contrasena
    ):
        """
        Compara una contraseña con el hash almacenado.
        """

        if not contrasena:

            return False

        if not self.hash_contrasena:

            return False

        return check_password_hash(
            self.hash_contrasena,
            contrasena
        )


    @property
    def contrasena(
        self
    ):
        """
        Impide leer la contraseña desde el modelo.
        """

        raise AttributeError(
            "La contraseña no puede ser consultada."
        )


    @contrasena.setter
    def contrasena(
        self,
        valor
    ):
        """
        Permite hacer:

        usuario.contrasena = 'MiClaveSegura'

        y almacena solamente el hash.
        """

        self.establecer_contrasena(
            valor
        )


    # =====================================================
    # FLASK-LOGIN
    # =====================================================

    def get_id(
        self
    ):
        """
        Flask-Login necesita que el ID se retorne
        como cadena.
        """

        return str(
            self.id_usuario
        )


    @property
    def is_active(
        self
    ):
        """
        Flask-Login consultará esta propiedad antes
        de considerar activo al usuario.
        """

        return bool(
            self.activo
        )


    # =====================================================
    # PROPIEDADES AUXILIARES
    # =====================================================

    @property
    def nombre_completo(
        self
    ):

        return " ".join(
            parte
            for parte in [
                self.nombres,
                self.apellidos
            ]
            if parte
        ).strip()


    @property
    def codigo_rol(
        self
    ):

        if not self.rol:

            return None

        return self.rol.codigo


    # =====================================================
    # ROLES
    # =====================================================

    def es_administrador(
        self
    ):

        return (
            self.codigo_rol
            == "ADMINISTRADOR"
        )


    def es_area_comercial(
        self
    ):

        return (
            self.codigo_rol
            == "AREA_COMERCIAL"
        )


    def es_vendedor(
        self
    ):

        return (
            self.codigo_rol
            == "VENDEDOR"
        )


    # =====================================================
    # PERMISOS
    # =====================================================

    def tiene_permiso(
        self,
        codigo_permiso
    ):
        """
        Comprueba si el usuario posee un permiso
        mediante su rol.
        """

        if not self.activo:

            return False

        if not self.rol:

            return False

        return self.rol.tiene_permiso(
            codigo_permiso
        )


    # =====================================================
    # REPRESENTACION
    # =====================================================

    def __repr__(
        self
    ):

        return (
            f"<Usuario "
            f"id={self.id_usuario} "
            f"correo='{self.correo}'>"
        )


# =========================================================
# CARGADOR PARA FLASK-LOGIN
# =========================================================

@login_manager.user_loader
def cargar_usuario(
    id_usuario
):
    """
    Flask-Login ejecutará esta función para recuperar
    al usuario almacenado en la sesión.

    Gracias a que Usuario.ventas usa lazy='select',
    cargar al usuario NO carga automáticamente
    todas sus ventas.
    """

    try:

        id_usuario = int(
            id_usuario
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    return db.session.get(
        Usuario,
        id_usuario
    )