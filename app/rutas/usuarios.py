from datetime import (
    datetime,
    timezone
)

from decimal import (
    Decimal,
    InvalidOperation
)

from time import perf_counter

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import current_user

from sqlalchemy import (
    func,
    or_
)

from app.extensiones import db

from app.modelos import (
    Rol,
    Usuario,
    TipoDocumentoEnum
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/administrador/usuarios"
)


# =========================================================
# CONFIGURACION
# =========================================================

USUARIOS_POR_PAGINA = 20


# =========================================================
# AUXILIARES
# =========================================================

def obtener_roles():

    return (
        db.session.execute(
            db.select(
                Rol
            )
            .where(
                Rol.activo.is_(True)
            )
            .order_by(
                Rol.nombre.asc()
            )
        )
        .scalars()
        .all()
    )


def decimal_o_none(
    valor
):

    if not valor:

        return None

    try:

        return Decimal(
            str(
                valor
            )
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return None


# =========================================================
# LISTAR
#
# OPTIMIZADO PARA RENDER + NEON
# =========================================================

@bp.get("/")
@rol_requerido(
    "ADMINISTRADOR"
)
def lista():

    tiempo_inicio = (
        perf_counter()
    )

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    pagina = request.args.get(
        "pagina",
        1,
        type=int
    )

    if pagina < 1:

        pagina = 1

    # =====================================================
    # CONSULTA LIGERA
    #
    # NO:
    #
    # select(Usuario)
    # joinedload()
    # objetos ORM completos
    #
    # SOLO COLUMNAS NECESARIAS.
    # =====================================================

    consulta = (
        db.select(

            Usuario.id_usuario.label(
                "id_usuario"
            ),

            Usuario.nombres.label(
                "nombres"
            ),

            Usuario.apellidos.label(
                "apellidos"
            ),

            Usuario.numero_documento.label(
                "numero_documento"
            ),

            Usuario.correo.label(
                "correo"
            ),

            Usuario.activo.label(
                "activo"
            ),

            Rol.nombre.label(
                "rol_nombre"
            )
        )
        .select_from(
            Usuario
        )
        .join(
            Rol,
            Usuario.id_rol
            == Rol.id_rol
        )
    )

    # =====================================================
    # BUSQUEDA
    # =====================================================

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        consulta = consulta.where(
            or_(
                Usuario.nombres.ilike(
                    patron
                ),

                Usuario.apellidos.ilike(
                    patron
                ),

                Usuario.correo.ilike(
                    patron
                ),

                Usuario.numero_documento.ilike(
                    patron
                )
            )
        )

    # =====================================================
    # PAGINACION
    #
    # IMPORTANTE:
    #
    # ORDENAMOS POR PK.
    #
    # id_usuario YA ESTA INDEXADO
    # POR SER PRIMARY KEY.
    #
    # EVITAMOS ORDER BY creado_en
    # SIN INDICE.
    # =====================================================

    offset = (
        pagina - 1
    ) * USUARIOS_POR_PAGINA

    consulta = (
        consulta
        .order_by(
            Usuario.id_usuario.desc()
        )
        .offset(
            offset
        )
        .limit(
            USUARIOS_POR_PAGINA
            + 1
        )
    )

    # =====================================================
    # MEDIR CONSULTA
    # =====================================================

    tiempo_consulta_inicio = (
        perf_counter()
    )

    filas = (
        db.session.execute(
            consulta
        )
        .mappings()
        .all()
    )

    tiempo_consulta = (
        perf_counter()
        -
        tiempo_consulta_inicio
    )

    # =====================================================
    # PAGINA SIGUIENTE
    # =====================================================

    hay_siguiente = (
        len(
            filas
        )
        >
        USUARIOS_POR_PAGINA
    )

    filas = filas[
        :USUARIOS_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # DATOS SIMPLES
    #
    # NO OBJETOS SQLALCHEMY.
    # =====================================================

    usuarios = []

    for fila in filas:

        nombre_completo = " ".join(
            parte
            for parte in [
                fila[
                    "nombres"
                ],

                fila[
                    "apellidos"
                ]
            ]
            if parte
        ).strip()

        usuarios.append({

            "id_usuario":
                fila[
                    "id_usuario"
                ],

            "nombres":
                fila[
                    "nombres"
                ],

            "apellidos":
                fila[
                    "apellidos"
                ],

            "nombre_completo":
                nombre_completo,

            "numero_documento":
                fila[
                    "numero_documento"
                ],

            "correo":
                fila[
                    "correo"
                ],

            "activo":
                fila[
                    "activo"
                ],

            "rol_nombre":
                fila[
                    "rol_nombre"
                ]
        })

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not usuarios
    ):

        return redirect(
            url_for(
                "usuarios.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar
            )
        )

    # =====================================================
    # MEDIR TEMPLATE
    # =====================================================

    tiempo_template_inicio = (
        perf_counter()
    )

    html = render_template(
        "administrador/usuarios/lista.html",

        usuarios=usuarios,

        buscar=buscar,

        pagina=pagina,

        hay_anterior=(
            hay_anterior
        ),

        hay_siguiente=(
            hay_siguiente
        ),

        por_pagina=(
            USUARIOS_POR_PAGINA
        )
    )

    tiempo_template = (
        perf_counter()
        -
        tiempo_template_inicio
    )

    tiempo_total = (
        perf_counter()
        -
        tiempo_inicio
    )

    # =====================================================
    # LOG TEMPORAL
    #
    # APARECERA EN RENDER LOGS:
    #
    # [PERF USUARIOS]
    # SQL=0.120s
    # TEMPLATE=0.030s
    # TOTAL=0.170s
    # =====================================================

    print(
        (
            "[PERF USUARIOS] "
            f"SQL={tiempo_consulta:.3f}s | "
            f"TEMPLATE={tiempo_template:.3f}s | "
            f"TOTAL={tiempo_total:.3f}s | "
            f"FILAS={len(usuarios)}"
        ),
        flush=True
    )

    return html


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_usuario>"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def detalle(
    id_usuario
):

    usuario = db.get_or_404(
        Usuario,
        id_usuario
    )

    return render_template(
        "administrador/usuarios/detalle.html",
        usuario=usuario
    )


# =========================================================
# NUEVO USUARIO
# =========================================================

@bp.route(
    "/nuevo",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "ADMINISTRADOR"
)
def nuevo():

    roles = obtener_roles()

    if request.method == "POST":

        tipo_documento = (
            request.form.get(
                "tipo_documento",
                ""
            )
            .strip()
        )

        numero_documento = (
            request.form.get(
                "numero_documento",
                ""
            )
            .strip()
        )

        nombres = (
            request.form.get(
                "nombres",
                ""
            )
            .strip()
        )

        apellidos = (
            request.form.get(
                "apellidos",
                ""
            )
            .strip()
        )

        correo = (
            request.form.get(
                "correo",
                ""
            )
            .strip()
            .lower()
        )

        celular = (
            request.form.get(
                "celular",
                ""
            )
            .strip()
        )

        direccion = (
            request.form.get(
                "direccion",
                ""
            )
            .strip()
        )

        geoapify_place_id = (
            request.form.get(
                "geoapify_place_id",
                ""
            )
            .strip()
        )

        latitud = decimal_o_none(
            request.form.get(
                "latitud",
                ""
            ).strip()
        )

        longitud = decimal_o_none(
            request.form.get(
                "longitud",
                ""
            ).strip()
        )

        id_rol = request.form.get(
            "id_rol",
            type=int
        )

        contrasena = request.form.get(
            "contrasena",
            ""
        )

        datos_obtenidos_api = (
            request.form.get(
                "datos_obtenidos_api",
                "0"
            )
            == "1"
        )

        # =================================================
        # TIPO DOCUMENTO
        # =================================================

        if tipo_documento not in (
            "DNI",
            "SIN_DOCUMENTO"
        ):

            flash(
                "Tipo de documento inválido.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        # =================================================
        # DNI
        # =================================================

        if tipo_documento == "DNI":

            if (
                not numero_documento.isdigit()
                or
                len(
                    numero_documento
                )
                != 8
            ):

                flash(
                    (
                        "El DNI debe contener "
                        "exactamente 8 dígitos."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/usuarios/formulario.html",
                    roles=roles,
                    usuario=None
                )

        else:

            numero_documento = None

            datos_obtenidos_api = (
                False
            )

        # =================================================
        # DATOS
        # =================================================

        if not nombres:

            flash(
                "Los nombres son obligatorios.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        if not apellidos:

            flash(
                "Los apellidos son obligatorios.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        if not correo:

            flash(
                (
                    "El correo electrónico "
                    "es obligatorio."
                ),
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        if len(
            contrasena
        ) < 8:

            flash(
                (
                    "La contraseña debe tener "
                    "como mínimo 8 caracteres."
                ),
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        # =================================================
        # ROL
        # =================================================

        rol = db.session.get(
            Rol,
            id_rol
        )

        if (
            rol is None
            or not rol.activo
        ):

            flash(
                "Seleccione un rol válido.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        # =================================================
        # CORREO DUPLICADO
        # =================================================

        usuario_correo = (
            db.session.execute(
                db.select(
                    Usuario.id_usuario
                )
                .where(
                    func.lower(
                        Usuario.correo
                    )
                    == correo
                )
                .limit(
                    1
                )
            )
            .scalar_one_or_none()
        )

        if usuario_correo is not None:

            flash(
                (
                    "Ya existe un usuario "
                    "con ese correo electrónico."
                ),
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        # =================================================
        # DNI DUPLICADO
        # =================================================

        if numero_documento:

            usuario_documento = (
                db.session.execute(
                    db.select(
                        Usuario.id_usuario
                    )
                    .where(
                        Usuario.numero_documento
                        == numero_documento
                    )
                    .limit(
                        1
                    )
                )
                .scalar_one_or_none()
            )

            if (
                usuario_documento
                is not None
            ):

                flash(
                    (
                        "Ya existe un usuario "
                        "registrado con ese DNI."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/usuarios/formulario.html",
                    roles=roles,
                    usuario=None
                )

        # =================================================
        # CREAR
        # =================================================

        usuario = Usuario(

            id_rol=(
                rol.id_rol
            ),

            tipo_documento=(
                TipoDocumentoEnum(
                    tipo_documento
                )
            ),

            numero_documento=(
                numero_documento
            ),

            nombres=nombres,

            apellidos=apellidos,

            correo=correo,

            celular=(
                celular
                or None
            ),

            direccion=(
                direccion
                or None
            ),

            geoapify_place_id=(
                geoapify_place_id
                or None
            ),

            latitud=latitud,

            longitud=longitud,

            datos_obtenidos_api=(
                datos_obtenidos_api
            ),

            api_consultada_en=(
                datetime.now(
                    timezone.utc
                )
                if datos_obtenidos_api
                else None
            ),

            activo=True
        )

        usuario.contrasena = (
            contrasena
        )

        try:

            db.session.add(
                usuario
            )

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR REGISTRANDO USUARIO:",
                error
            )

            flash(
                "No se pudo registrar el usuario.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=None
            )

        flash(
            "Usuario registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "usuarios.lista"
            )
        )

    return render_template(
        "administrador/usuarios/formulario.html",
        roles=roles,
        usuario=None
    )


# =========================================================
# EDITAR USUARIO
# =========================================================

@bp.route(
    "/<int:id_usuario>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "ADMINISTRADOR"
)
def editar(
    id_usuario
):

    usuario = db.get_or_404(
        Usuario,
        id_usuario
    )

    roles = obtener_roles()

    if request.method == "POST":

        tipo_documento = (
            request.form.get(
                "tipo_documento",
                ""
            )
            .strip()
        )

        numero_documento = (
            request.form.get(
                "numero_documento",
                ""
            )
            .strip()
        )

        nombres = (
            request.form.get(
                "nombres",
                ""
            )
            .strip()
        )

        apellidos = (
            request.form.get(
                "apellidos",
                ""
            )
            .strip()
        )

        correo = (
            request.form.get(
                "correo",
                ""
            )
            .strip()
            .lower()
        )

        celular = (
            request.form.get(
                "celular",
                ""
            )
            .strip()
        )

        direccion = (
            request.form.get(
                "direccion",
                ""
            )
            .strip()
        )

        geoapify_place_id = (
            request.form.get(
                "geoapify_place_id",
                ""
            )
            .strip()
        )

        latitud = decimal_o_none(
            request.form.get(
                "latitud",
                ""
            ).strip()
        )

        longitud = decimal_o_none(
            request.form.get(
                "longitud",
                ""
            ).strip()
        )

        id_rol = request.form.get(
            "id_rol",
            type=int
        )

        nueva_contrasena = (
            request.form.get(
                "nueva_contrasena",
                ""
            )
        )

        datos_obtenidos_api = (
            request.form.get(
                "datos_obtenidos_api",
                "0"
            )
            == "1"
        )

        # =================================================
        # DOCUMENTO
        # =================================================

        if tipo_documento not in (
            "DNI",
            "SIN_DOCUMENTO"
        ):

            flash(
                "Tipo de documento inválido.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=usuario
            )

        if tipo_documento == "DNI":

            if (
                not numero_documento.isdigit()
                or
                len(
                    numero_documento
                )
                != 8
            ):

                flash(
                    (
                        "El DNI debe contener "
                        "exactamente 8 dígitos."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/usuarios/formulario.html",
                    roles=roles,
                    usuario=usuario
                )

        else:

            numero_documento = None

            datos_obtenidos_api = (
                False
            )

        # =================================================
        # CAMPOS OBLIGATORIOS
        # =================================================

        if (
            not nombres
            or not apellidos
            or not correo
        ):

            flash(
                (
                    "Nombres, apellidos y correo "
                    "son obligatorios."
                ),
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=usuario
            )

        # =================================================
        # ROL
        # =================================================

        rol = db.session.get(
            Rol,
            id_rol
        )

        if (
            rol is None
            or not rol.activo
        ):

            flash(
                "Seleccione un rol válido.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=usuario
            )

        # =================================================
        # CORREO DUPLICADO
        # =================================================

        usuario_correo = (
            db.session.execute(
                db.select(
                    Usuario.id_usuario
                )
                .where(
                    func.lower(
                        Usuario.correo
                    )
                    == correo,

                    Usuario.id_usuario
                    != usuario.id_usuario
                )
                .limit(
                    1
                )
            )
            .scalar_one_or_none()
        )

        if usuario_correo is not None:

            flash(
                (
                    "Ya existe otro usuario "
                    "con ese correo."
                ),
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=usuario
            )

        # =================================================
        # DNI DUPLICADO
        # =================================================

        if numero_documento:

            usuario_documento = (
                db.session.execute(
                    db.select(
                        Usuario.id_usuario
                    )
                    .where(
                        Usuario.numero_documento
                        == numero_documento,

                        Usuario.id_usuario
                        != usuario.id_usuario
                    )
                    .limit(
                        1
                    )
                )
                .scalar_one_or_none()
            )

            if (
                usuario_documento
                is not None
            ):

                flash(
                    (
                        "Ya existe otro usuario "
                        "con ese DNI."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/usuarios/formulario.html",
                    roles=roles,
                    usuario=usuario
                )

        # =================================================
        # ACTUALIZAR
        # =================================================

        usuario.id_rol = (
            rol.id_rol
        )

        usuario.tipo_documento = (
            TipoDocumentoEnum(
                tipo_documento
            )
        )

        usuario.numero_documento = (
            numero_documento
        )

        usuario.nombres = nombres
        usuario.apellidos = apellidos
        usuario.correo = correo

        usuario.celular = (
            celular
            or None
        )

        usuario.direccion = (
            direccion
            or None
        )

        usuario.geoapify_place_id = (
            geoapify_place_id
            or None
        )

        usuario.latitud = latitud
        usuario.longitud = longitud

        usuario.datos_obtenidos_api = (
            datos_obtenidos_api
        )

        if datos_obtenidos_api:

            usuario.api_consultada_en = (
                datetime.now(
                    timezone.utc
                )
            )

        else:

            usuario.api_consultada_en = (
                None
            )

        # =================================================
        # CONTRASEÑA
        # =================================================

        if nueva_contrasena:

            if len(
                nueva_contrasena
            ) < 8:

                flash(
                    (
                        "La nueva contraseña debe "
                        "tener como mínimo 8 caracteres."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/usuarios/formulario.html",
                    roles=roles,
                    usuario=usuario
                )

            usuario.contrasena = (
                nueva_contrasena
            )

        # =================================================
        # GUARDAR
        # =================================================

        try:

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR ACTUALIZANDO USUARIO:",
                error
            )

            flash(
                "No se pudo actualizar el usuario.",
                "danger"
            )

            return render_template(
                "administrador/usuarios/formulario.html",
                roles=roles,
                usuario=usuario
            )

        flash(
            "Usuario actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "usuarios.detalle",

                id_usuario=(
                    usuario.id_usuario
                )
            )
        )

    return render_template(
        "administrador/usuarios/formulario.html",
        roles=roles,
        usuario=usuario
    )


# =========================================================
# ACTIVAR / DESACTIVAR
# =========================================================

@bp.post(
    "/<int:id_usuario>/cambiar-estado"
)
@rol_requerido(
    "ADMINISTRADOR"
)
def cambiar_estado(
    id_usuario
):

    usuario = db.get_or_404(
        Usuario,
        id_usuario
    )

    if (
        usuario.id_usuario
        == current_user.id_usuario
    ):

        flash(
            (
                "No puedes desactivar "
                "tu propio usuario."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "usuarios.lista"
            )
        )

    usuario.activo = (
        not usuario.activo
    )

    try:

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR CAMBIANDO ESTADO USUARIO:",
            error
        )

        flash(
            (
                "No se pudo cambiar "
                "el estado del usuario."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "usuarios.lista"
            )
        )

    if usuario.activo:

        flash(
            "Usuario activado correctamente.",
            "success"
        )

    else:

        flash(
            "Usuario desactivado correctamente.",
            "success"
        )

    return redirect(
        url_for(
            "usuarios.lista"
        )
    )