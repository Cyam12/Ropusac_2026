from datetime import (
    datetime,
    timezone
)

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
    Proveedor,
    TipoDocumentoEnum,
    Usuario
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "proveedores_comercial",
    __name__,
    url_prefix="/area-comercial/proveedores"
)


# =========================================================
# AUXILIARES
# =========================================================

def nombre_usuario(
    usuario
):

    if usuario is None:

        return "Usuario no disponible"

    nombre = " ".join(
        parte
        for parte in [
            usuario.nombres,
            usuario.apellidos
        ]
        if parte
    ).strip()

    return (
        nombre
        or usuario.correo
        or "Usuario"
    )


# =========================================================
# LISTAR
#
# IMPORTANTE:
# NO SE FILTRA POR current_user.
#
# TODOS LOS USUARIOS DE AREA COMERCIAL VEN EL MISMO
# CATALOGO GENERAL DE PROVEEDORES.
# =========================================================

@bp.get("/")
@rol_requerido(
    "AREA_COMERCIAL"
)
def lista():

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    estado = request.args.get(
        "estado",
        ""
    ).strip()

    # =====================================================
    # CONSULTA GLOBAL
    # =====================================================

    consulta = (
        db.select(
            Proveedor,
            Usuario
        )
        .join(
            Usuario,
            Proveedor.creado_por
            == Usuario.id_usuario
        )
        .order_by(
            Proveedor.activo.desc(),
            Proveedor.razon_social.asc()
        )
    )

    # =====================================================
    # BUSQUEDA GLOBAL
    # =====================================================

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        consulta = consulta.where(
            or_(
                Proveedor.razon_social.ilike(
                    patron
                ),

                Proveedor.nombre_comercial.ilike(
                    patron
                ),

                Proveedor.numero_documento.ilike(
                    patron
                ),

                Proveedor.correo.ilike(
                    patron
                ),

                Usuario.nombres.ilike(
                    patron
                ),

                Usuario.apellidos.ilike(
                    patron
                )
            )
        )

    # =====================================================
    # ESTADO
    # =====================================================

    if estado == "ACTIVO":

        consulta = consulta.where(
            Proveedor.activo.is_(
                True
            )
        )

    elif estado == "INACTIVO":

        consulta = consulta.where(
            Proveedor.activo.is_(
                False
            )
        )

    filas = (
        db.session.execute(
            consulta
        )
        .all()
    )

    proveedores = []

    for proveedor, usuario in filas:

        proveedores.append({
            "proveedor":
                proveedor,

            "registrado_por":
                nombre_usuario(
                    usuario
                ),

            "es_mio":
                (
                    proveedor.creado_por
                    == current_user.id_usuario
                )
        })

    return render_template(
        "area_comercial/proveedores/lista.html",

        proveedores=proveedores,

        buscar=buscar,

        estado=estado
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_proveedor>"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def detalle(
    id_proveedor
):

    proveedor = db.get_or_404(
        Proveedor,
        id_proveedor
    )

    creador = db.session.get(
        Usuario,
        proveedor.creado_por
    )

    return render_template(
        "area_comercial/proveedores/detalle.html",

        proveedor=proveedor,

        registrado_por=(
            nombre_usuario(
                creador
            )
        )
    )


# =========================================================
# NUEVO
# =========================================================

@bp.route(
    "/nuevo",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def nuevo():

    if request.method == "POST":

        datos = obtener_datos_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "area_comercial/proveedores/formulario.html",
                proveedor=None
            )

        # =================================================
        # VALIDAR RUC GLOBALMENTE
        # =================================================

        if datos[
            "numero_documento"
        ]:

            existente_documento = (
                db.session.execute(
                    db.select(
                        Proveedor
                    )
                    .where(
                        Proveedor.numero_documento
                        == datos[
                            "numero_documento"
                        ]
                    )
                )
                .scalar_one_or_none()
            )

            if existente_documento:

                flash(
                    (
                        "Este proveedor ya se encuentra "
                        "registrado en el sistema con el RUC "
                        f"{datos['numero_documento']}."
                    ),
                    "danger"
                )

                return redirect(
                    url_for(
                        "proveedores_comercial.detalle",
                        id_proveedor=(
                            existente_documento.id_proveedor
                        )
                    )
                )

        # =================================================
        # VALIDAR RAZON SOCIAL GLOBALMENTE
        #
        # EVITA:
        # FERREYROS
        # ferreyros
        # Ferreyros
        # =================================================

        existente_nombre = (
            db.session.execute(
                db.select(
                    Proveedor
                )
                .where(
                    func.lower(
                        func.trim(
                            Proveedor.razon_social
                        )
                    )
                    ==
                    datos[
                        "razon_social"
                    ].strip().lower()
                )
            )
            .scalar_one_or_none()
        )

        if existente_nombre:

            flash(
                (
                    "Ya existe un proveedor registrado "
                    "con la misma razón social. "
                    "Revise el proveedor existente "
                    "antes de crear uno nuevo."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "proveedores_comercial.detalle",
                    id_proveedor=(
                        existente_nombre.id_proveedor
                    )
                )
            )

        # =================================================
        # CREAR
        # =================================================

        proveedor = Proveedor(
            tipo_documento=(
                TipoDocumentoEnum(
                    datos[
                        "tipo_documento"
                    ]
                )
            ),

            numero_documento=(
                datos[
                    "numero_documento"
                ]
            ),

            razon_social=(
                datos[
                    "razon_social"
                ]
            ),

            nombre_comercial=(
                datos[
                    "nombre_comercial"
                ]
            ),

            correo=(
                datos[
                    "correo"
                ]
            ),

            celular=(
                datos[
                    "celular"
                ]
            ),

            telefono=(
                datos[
                    "telefono"
                ]
            ),

            direccion_fiscal=(
                datos[
                    "direccion_fiscal"
                ]
            ),

            datos_obtenidos_api=(
                datos[
                    "datos_obtenidos_api"
                ]
            ),

            api_consultada_en=(
                datetime.now(
                    timezone.utc
                )
                if datos[
                    "datos_obtenidos_api"
                ]
                else None
            ),

            activo=True,

            creado_por=(
                current_user.id_usuario
            ),

            actualizado_por=None
        )

        try:

            db.session.add(
                proveedor
            )

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR REGISTRANDO PROVEEDOR AREA COMERCIAL:",
                error_bd
            )

            flash(
                "No se pudo registrar el proveedor.",
                "danger"
            )

            return render_template(
                "area_comercial/proveedores/formulario.html",
                proveedor=None
            )

        flash(
            "Proveedor registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "proveedores_comercial.lista"
            )
        )

    return render_template(
        "area_comercial/proveedores/formulario.html",
        proveedor=None
    )


# =========================================================
# EDITAR
# =========================================================

@bp.route(
    "/<int:id_proveedor>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def editar(
    id_proveedor
):

    proveedor = db.get_or_404(
        Proveedor,
        id_proveedor
    )

    if request.method == "POST":

        datos = obtener_datos_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "area_comercial/proveedores/formulario.html",
                proveedor=proveedor
            )

        # =================================================
        # RUC DUPLICADO GLOBAL
        # =================================================

        if datos[
            "numero_documento"
        ]:

            existente_documento = (
                db.session.execute(
                    db.select(
                        Proveedor
                    )
                    .where(
                        Proveedor.numero_documento
                        == datos[
                            "numero_documento"
                        ],

                        Proveedor.id_proveedor
                        != proveedor.id_proveedor
                    )
                )
                .scalar_one_or_none()
            )

            if existente_documento:

                flash(
                    (
                        "El RUC ingresado pertenece "
                        "a otro proveedor registrado."
                    ),
                    "danger"
                )

                return render_template(
                    "area_comercial/proveedores/formulario.html",
                    proveedor=proveedor
                )

        # =================================================
        # RAZON SOCIAL DUPLICADA GLOBAL
        # =================================================

        existente_nombre = (
            db.session.execute(
                db.select(
                    Proveedor
                )
                .where(
                    func.lower(
                        func.trim(
                            Proveedor.razon_social
                        )
                    )
                    ==
                    datos[
                        "razon_social"
                    ].strip().lower(),

                    Proveedor.id_proveedor
                    != proveedor.id_proveedor
                )
            )
            .scalar_one_or_none()
        )

        if existente_nombre:

            flash(
                (
                    "Ya existe otro proveedor "
                    "con esa razón social."
                ),
                "warning"
            )

            return render_template(
                "area_comercial/proveedores/formulario.html",
                proveedor=proveedor
            )

        documento_anterior = (
            proveedor.numero_documento
        )

        datos_api_anteriores = (
            proveedor.datos_obtenidos_api
        )

        # =================================================
        # ACTUALIZAR
        # =================================================

        proveedor.tipo_documento = (
            TipoDocumentoEnum(
                datos[
                    "tipo_documento"
                ]
            )
        )

        proveedor.numero_documento = (
            datos[
                "numero_documento"
            ]
        )

        proveedor.razon_social = (
            datos[
                "razon_social"
            ]
        )

        proveedor.nombre_comercial = (
            datos[
                "nombre_comercial"
            ]
        )

        proveedor.correo = (
            datos[
                "correo"
            ]
        )

        proveedor.celular = (
            datos[
                "celular"
            ]
        )

        proveedor.telefono = (
            datos[
                "telefono"
            ]
        )

        proveedor.direccion_fiscal = (
            datos[
                "direccion_fiscal"
            ]
        )

        proveedor.datos_obtenidos_api = (
            datos[
                "datos_obtenidos_api"
            ]
        )

        proveedor.actualizado_por = (
            current_user.id_usuario
        )

        # =================================================
        # FECHA API
        # =================================================

        if not datos[
            "datos_obtenidos_api"
        ]:

            proveedor.api_consultada_en = (
                None
            )

        elif (
            not datos_api_anteriores
            or documento_anterior
            != datos[
                "numero_documento"
            ]
        ):

            proveedor.api_consultada_en = (
                datetime.now(
                    timezone.utc
                )
            )

        try:

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR ACTUALIZANDO PROVEEDOR AREA COMERCIAL:",
                error_bd
            )

            flash(
                "No se pudo actualizar el proveedor.",
                "danger"
            )

            return render_template(
                "area_comercial/proveedores/formulario.html",
                proveedor=proveedor
            )

        flash(
            "Proveedor actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "proveedores_comercial.detalle",
                id_proveedor=(
                    proveedor.id_proveedor
                )
            )
        )

    return render_template(
        "area_comercial/proveedores/formulario.html",
        proveedor=proveedor
    )


# =========================================================
# DAR DE BAJA / REACTIVAR
# =========================================================

@bp.post(
    "/<int:id_proveedor>/cambiar-estado"
)
@rol_requerido(
    "AREA_COMERCIAL"
)
def cambiar_estado(
    id_proveedor
):

    proveedor = db.get_or_404(
        Proveedor,
        id_proveedor
    )

    proveedor.activo = (
        not proveedor.activo
    )

    proveedor.actualizado_por = (
        current_user.id_usuario
    )

    try:

        db.session.commit()

    except Exception as error_bd:

        db.session.rollback()

        print(
            "ERROR CAMBIANDO ESTADO PROVEEDOR:",
            error_bd
        )

        flash(
            "No se pudo cambiar el estado del proveedor.",
            "danger"
        )

        return redirect(
            url_for(
                "proveedores_comercial.lista"
            )
        )

    if proveedor.activo:

        flash(
            "Proveedor reactivado correctamente.",
            "success"
        )

    else:

        flash(
            "Proveedor dado de baja correctamente.",
            "success"
        )

    return redirect(
        url_for(
            "proveedores_comercial.lista"
        )
    )


# =========================================================
# OBTENER FORMULARIO
# =========================================================

def obtener_datos_formulario():

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

    razon_social = (
        request.form.get(
            "razon_social",
            ""
        )
        .strip()
    )

    nombre_comercial = (
        request.form.get(
            "nombre_comercial",
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

    telefono = (
        request.form.get(
            "telefono",
            ""
        )
        .strip()
    )

    direccion_fiscal = (
        request.form.get(
            "direccion_fiscal",
            ""
        )
        .strip()
    )

    datos_obtenidos_api = (
        request.form.get(
            "datos_obtenidos_api",
            "0"
        )
        == "1"
    )

    if (
        tipo_documento
        == "SIN_DOCUMENTO"
    ):

        numero_documento = None

        datos_obtenidos_api = False

    return {
        "tipo_documento":
            tipo_documento,

        "numero_documento":
            numero_documento,

        "razon_social":
            razon_social,

        "nombre_comercial":
            nombre_comercial
            or None,

        "correo":
            correo
            or None,

        "celular":
            celular
            or None,

        "telefono":
            telefono
            or None,

        "direccion_fiscal":
            direccion_fiscal
            or None,

        "datos_obtenidos_api":
            datos_obtenidos_api
    }


# =========================================================
# VALIDAR
# =========================================================

def validar_datos(
    datos
):

    if datos[
        "tipo_documento"
    ] not in (
        "RUC",
        "SIN_DOCUMENTO"
    ):

        return (
            "Tipo de documento inválido."
        )

    if (
        datos[
            "tipo_documento"
        ]
        == "RUC"
    ):

        ruc = (
            datos[
                "numero_documento"
            ]
            or ""
        )

        if (
            not ruc.isdigit()
            or len(ruc) != 11
        ):

            return (
                "El RUC debe contener "
                "exactamente 11 dígitos."
            )

    if not datos[
        "razon_social"
    ]:

        return (
            "La razón social es obligatoria."
        )

    return None