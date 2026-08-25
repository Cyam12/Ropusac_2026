from datetime import (
    datetime,
    timezone
)

from decimal import (
    Decimal,
    InvalidOperation
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
    Cliente,
    Rol,
    TipoDocumentoEnum,
    Usuario
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "clientes_vendedor",
    __name__,
    url_prefix="/vendedor/clientes"
)


# =========================================================
# CONFIGURACION
# =========================================================

CLIENTES_POR_PAGINA = 20


# =========================================================
# AUXILIARES
# =========================================================

def decimal_o_none(
    valor
):

    if valor is None:
        return None

    valor = str(
        valor
    ).strip()

    if not valor:
        return None

    try:

        return Decimal(
            valor
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return None


def texto_enum(
    valor
):

    if valor is None:
        return ""

    if hasattr(
        valor,
        "value"
    ):
        return valor.value

    return str(
        valor
    )


def nombre_cliente(
    cliente
):

    if cliente is None:
        return ""

    if isinstance(
        cliente,
        dict
    ):

        razon_social = cliente.get(
            "razon_social"
        )

        nombres = cliente.get(
            "nombres"
        )

        apellidos = cliente.get(
            "apellidos"
        )

    else:

        razon_social = (
            cliente.razon_social
        )

        nombres = (
            cliente.nombres
        )

        apellidos = (
            cliente.apellidos
        )

    if razon_social:
        return razon_social

    return " ".join(
        parte
        for parte in [
            nombres,
            apellidos
        ]
        if parte
    ).strip()


def nombre_usuario(
    usuario
):

    if usuario is None:

        return (
            "Usuario no disponible"
        )

    if isinstance(
        usuario,
        dict
    ):

        nombres = usuario.get(
            "nombres"
        )

        apellidos = usuario.get(
            "apellidos"
        )

        correo = usuario.get(
            "correo"
        )

    else:

        nombres = (
            usuario.nombres
        )

        apellidos = (
            usuario.apellidos
        )

        correo = (
            usuario.correo
        )

    nombre = " ".join(
        parte
        for parte in [
            nombres,
            apellidos
        ]
        if parte
    ).strip()

    return (
        nombre
        or correo
        or "Usuario"
    )


# =========================================================
# BUSCAR POSIBLE DUPLICADO SIN DOCUMENTO
#
# SOLO CONSULTAMOS EL ID DEL CLIENTE.
# =========================================================

def buscar_duplicado_sin_documento(
    datos
):

    # =====================================================
    # EMPRESA
    # =====================================================

    if datos[
        "razon_social"
    ]:

        return (
            db.session.execute(
                db.select(
                    Cliente.id_cliente
                )
                .where(
                    func.lower(
                        func.trim(
                            Cliente.razon_social
                        )
                    )
                    ==
                    datos[
                        "razon_social"
                    ].strip().lower()
                )
                .order_by(
                    Cliente.id_cliente.asc()
                )
                .limit(
                    1
                )
            )
            .scalar_one_or_none()
        )

    # =====================================================
    # PERSONA
    # =====================================================

    if (
        datos[
            "nombres"
        ]
        and datos[
            "apellidos"
        ]
    ):

        return (
            db.session.execute(
                db.select(
                    Cliente.id_cliente
                )
                .where(
                    func.lower(
                        func.trim(
                            Cliente.nombres
                        )
                    )
                    ==
                    datos[
                        "nombres"
                    ].strip().lower(),

                    func.lower(
                        func.trim(
                            Cliente.apellidos
                        )
                    )
                    ==
                    datos[
                        "apellidos"
                    ].strip().lower()
                )
                .order_by(
                    Cliente.id_cliente.asc()
                )
                .limit(
                    1
                )
            )
            .scalar_one_or_none()
        )

    return None


# =========================================================
# LISTAR
#
# CATALOGO GLOBAL:
# SE MUESTRAN CLIENTES REGISTRADOS POR ADMINISTRADORES
# Y TODOS LOS VENDEDORES.
#
# OPTIMIZADO:
#
# - MAXIMO 20 CLIENTES POR PAGINA
# - SOLO COLUMNAS NECESARIAS
# - UNA SOLA CONSULTA CLIENTE + USUARIO + ROL
# - SIN OBJETOS ORM COMPLETOS
# - SIN N+1 PARA usuario.rol
# =========================================================

@bp.get("/")
@rol_requerido(
    "VENDEDOR"
)
def lista():

    buscar = request.args.get(
        "buscar",
        ""
    ).strip()

    tipo_documento = request.args.get(
        "tipo_documento",
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
    # =====================================================

    consulta = (
        db.select(

            # =================================================
            # CLIENTE
            # =================================================

            Cliente.id_cliente.label(
                "id_cliente"
            ),

            Cliente.tipo_documento.label(
                "tipo_documento"
            ),

            Cliente.numero_documento.label(
                "numero_documento"
            ),

            Cliente.nombres.label(
                "nombres"
            ),

            Cliente.apellidos.label(
                "apellidos"
            ),

            Cliente.razon_social.label(
                "razon_social"
            ),

            Cliente.correo.label(
                "correo"
            ),

            Cliente.celular.label(
                "celular"
            ),

            Cliente.direccion.label(
                "direccion"
            ),

            Cliente.activo.label(
                "activo"
            ),

            Cliente.creado_por.label(
                "creado_por"
            ),

            # =================================================
            # CREADOR
            # =================================================

            Usuario.nombres.label(
                "usuario_nombres"
            ),

            Usuario.apellidos.label(
                "usuario_apellidos"
            ),

            Usuario.correo.label(
                "usuario_correo"
            ),

            # =================================================
            # ROL
            # =================================================

            Rol.nombre.label(
                "rol_nombre"
            )
        )
        .select_from(
            Cliente
        )
        .join(
            Usuario,
            Cliente.creado_por
            == Usuario.id_usuario
        )
        .join(
            Rol,
            Usuario.id_rol
            == Rol.id_rol
        )
    )

    # =====================================================
    # BUSCAR
    # =====================================================

    if buscar:

        patron = (
            f"%{buscar}%"
        )

        consulta = consulta.where(
            or_(
                Cliente.nombres.ilike(
                    patron
                ),

                Cliente.apellidos.ilike(
                    patron
                ),

                Cliente.razon_social.ilike(
                    patron
                ),

                Cliente.numero_documento.ilike(
                    patron
                ),

                Cliente.correo.ilike(
                    patron
                ),

                Cliente.celular.ilike(
                    patron
                )
            )
        )

    # =====================================================
    # TIPO DOCUMENTO
    # =====================================================

    if tipo_documento in (
        "DNI",
        "RUC",
        "SIN_DOCUMENTO"
    ):

        consulta = consulta.where(
            Cliente.tipo_documento
            == tipo_documento
        )

    # =====================================================
    # PAGINACION
    #
    # 20 CLIENTES VISIBLES
    # + 1 PARA SABER SI HAY SIGUIENTE PAGINA
    # =====================================================

    offset = (
        pagina - 1
    ) * CLIENTES_POR_PAGINA

    consulta = (
        consulta
        .order_by(
            Cliente.activo.desc(),
            Cliente.id_cliente.desc()
        )
        .offset(
            offset
        )
        .limit(
            CLIENTES_POR_PAGINA
            + 1
        )
    )

    filas = (
        db.session.execute(
            consulta
        )
        .mappings()
        .all()
    )

    # =====================================================
    # PAGINACION
    # =====================================================

    hay_siguiente = (
        len(
            filas
        )
        >
        CLIENTES_POR_PAGINA
    )

    filas = filas[
        :CLIENTES_POR_PAGINA
    ]

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # PREPARAR DATOS
    # =====================================================

    clientes = []

    for fila in filas:

        cliente = {

            "id_cliente":
                fila[
                    "id_cliente"
                ],

            "tipo_documento":
                texto_enum(
                    fila[
                        "tipo_documento"
                    ]
                ),

            "numero_documento":
                fila[
                    "numero_documento"
                ],

            "nombres":
                fila[
                    "nombres"
                ],

            "apellidos":
                fila[
                    "apellidos"
                ],

            "razon_social":
                fila[
                    "razon_social"
                ],

            "correo":
                fila[
                    "correo"
                ],

            "celular":
                fila[
                    "celular"
                ],

            "direccion":
                fila[
                    "direccion"
                ],

            "activo":
                fila[
                    "activo"
                ],

            "creado_por":
                fila[
                    "creado_por"
                ]
        }

        usuario = {

            "nombres":
                fila[
                    "usuario_nombres"
                ],

            "apellidos":
                fila[
                    "usuario_apellidos"
                ],

            "correo":
                fila[
                    "usuario_correo"
                ]
        }

        clientes.append({

            "cliente":
                cliente,

            "nombre":
                nombre_cliente(
                    cliente
                ),

            "registrado_por":
                nombre_usuario(
                    usuario
                ),

            "rol_registro":
                (
                    fila[
                        "rol_nombre"
                    ]
                    or ""
                ),

            "es_mio":
                (
                    fila[
                        "creado_por"
                    ]
                    ==
                    current_user.id_usuario
                )
        })

    # =====================================================
    # PAGINA VACIA
    # =====================================================

    if (
        pagina > 1
        and not clientes
    ):

        return redirect(
            url_for(
                "clientes_vendedor.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar,

                tipo_documento=(
                    tipo_documento
                )
            )
        )

    return render_template(
        "vendedor/clientes/lista.html",

        clientes=clientes,

        buscar=buscar,

        tipo_documento=(
            tipo_documento
        ),

        pagina=pagina,

        hay_anterior=(
            hay_anterior
        ),

        hay_siguiente=(
            hay_siguiente
        ),

        por_pagina=(
            CLIENTES_POR_PAGINA
        )
    )


# =========================================================
# DETALLE
# =========================================================

@bp.get(
    "/<int:id_cliente>"
)
@rol_requerido(
    "VENDEDOR"
)
def detalle(
    id_cliente
):

    cliente = db.get_or_404(
        Cliente,
        id_cliente
    )

    creador = db.session.get(
        Usuario,
        cliente.creado_por
    )

    rol_registro = ""

    if (
        creador
        and creador.rol
    ):

        rol_registro = (
            creador.rol.nombre
        )

    return render_template(
        "vendedor/clientes/detalle.html",

        cliente=cliente,

        nombre_cliente=(
            nombre_cliente(
                cliente
            )
        ),

        registrado_por=(
            nombre_usuario(
                creador
            )
        ),

        rol_registro=(
            rol_registro
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
    "VENDEDOR"
)
def nuevo():

    if request.method == "POST":

        datos = obtener_formulario_nuevo()

        error = validar_nuevo(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "vendedor/clientes/formulario.html"
            )

        # =================================================
        # DNI / RUC DUPLICADO GLOBAL
        #
        # SOLO CONSULTAMOS EL ID.
        # =================================================

        if datos[
            "numero_documento"
        ]:

            id_existente = (
                db.session.execute(
                    db.select(
                        Cliente.id_cliente
                    )
                    .where(
                        Cliente.numero_documento
                        == datos[
                            "numero_documento"
                        ]
                    )
                    .limit(
                        1
                    )
                )
                .scalar_one_or_none()
            )

            if (
                id_existente
                is not None
            ):

                flash(
                    (
                        "El cliente ya se encuentra "
                        "registrado en el sistema. "
                        "Se abrió su ficha existente."
                    ),
                    "warning"
                )

                return redirect(
                    url_for(
                        "clientes_vendedor.detalle",

                        id_cliente=(
                            id_existente
                        )
                    )
                )

        # =================================================
        # SIN DOCUMENTO
        # =================================================

        if (
            datos[
                "tipo_documento"
            ]
            == "SIN_DOCUMENTO"
        ):

            id_existente = (
                buscar_duplicado_sin_documento(
                    datos
                )
            )

            if (
                id_existente
                is not None
            ):

                flash(
                    (
                        "Ya existe un cliente con "
                        "los mismos datos principales. "
                        "Revise el registro existente "
                        "antes de crear uno nuevo."
                    ),
                    "warning"
                )

                return redirect(
                    url_for(
                        "clientes_vendedor.detalle",

                        id_cliente=(
                            id_existente
                        )
                    )
                )

        # =================================================
        # CREAR
        # =================================================

        cliente = Cliente(

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

            nombres=(
                datos[
                    "nombres"
                ]
            ),

            apellidos=(
                datos[
                    "apellidos"
                ]
            ),

            razon_social=(
                datos[
                    "razon_social"
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

            telefono=None,

            direccion=(
                datos[
                    "direccion"
                ]
            ),

            geoapify_place_id=(
                datos[
                    "geoapify_place_id"
                ]
            ),

            latitud=(
                datos[
                    "latitud"
                ]
            ),

            longitud=(
                datos[
                    "longitud"
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
                cliente
            )

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR REGISTRANDO CLIENTE VENDEDOR:",
                error_bd
            )

            flash(
                "No se pudo registrar el cliente.",
                "danger"
            )

            return render_template(
                "vendedor/clientes/formulario.html"
            )

        flash(
            "Cliente registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "clientes_vendedor.detalle",

                id_cliente=(
                    cliente.id_cliente
                )
            )
        )

    return render_template(
        "vendedor/clientes/formulario.html"
    )


# =========================================================
# EDITAR CONTACTO
#
# EL VENDEDOR SOLO PUEDE MODIFICAR:
#
# - CORREO
# - CELULAR
# - DIRECCION
# =========================================================

@bp.route(
    "/<int:id_cliente>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "VENDEDOR"
)
def editar(
    id_cliente
):

    cliente = db.get_or_404(
        Cliente,
        id_cliente
    )

    if request.method == "POST":

        correo = (
            request.form.get(
                "correo",
                ""
            )
            .strip()
            .lower()
            or None
        )

        celular = (
            request.form.get(
                "celular",
                ""
            )
            .strip()
            or None
        )

        direccion = (
            request.form.get(
                "direccion",
                ""
            )
            .strip()
            or None
        )

        geoapify_place_id = (
            request.form.get(
                "geoapify_place_id",
                ""
            )
            .strip()
            or None
        )

        latitud = decimal_o_none(
            request.form.get(
                "latitud"
            )
        )

        longitud = decimal_o_none(
            request.form.get(
                "longitud"
            )
        )

        # =================================================
        # ACTUALIZAR SOLO CONTACTO
        # =================================================

        cliente.correo = (
            correo
        )

        cliente.celular = (
            celular
        )

        cliente.direccion = (
            direccion
        )

        cliente.geoapify_place_id = (
            geoapify_place_id
        )

        cliente.latitud = (
            latitud
        )

        cliente.longitud = (
            longitud
        )

        cliente.actualizado_por = (
            current_user.id_usuario
        )

        try:

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR ACTUALIZANDO CONTACTO CLIENTE:",
                error_bd
            )

            flash(
                (
                    "No se pudo actualizar "
                    "la información de contacto."
                ),
                "danger"
            )

            return render_template(
                "vendedor/clientes/editar.html",

                cliente=cliente,

                nombre_cliente=(
                    nombre_cliente(
                        cliente
                    )
                )
            )

        flash(
            (
                "Información de contacto "
                "actualizada correctamente."
            ),
            "success"
        )

        return redirect(
            url_for(
                "clientes_vendedor.detalle",

                id_cliente=(
                    cliente.id_cliente
                )
            )
        )

    return render_template(
        "vendedor/clientes/editar.html",

        cliente=cliente,

        nombre_cliente=(
            nombre_cliente(
                cliente
            )
        )
    )


# =========================================================
# FORMULARIO NUEVO
# =========================================================

def obtener_formulario_nuevo():

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

    razon_social = (
        request.form.get(
            "razon_social",
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
            "latitud"
        )
    )

    longitud = decimal_o_none(
        request.form.get(
            "longitud"
        )
    )

    datos_obtenidos_api = (
        request.form.get(
            "datos_obtenidos_api",
            "0"
        )
        == "1"
    )

    # =====================================================
    # DNI
    # =====================================================

    if tipo_documento == "DNI":

        razon_social = None

    # =====================================================
    # RUC
    # =====================================================

    elif tipo_documento == "RUC":

        nombres = None

        apellidos = None

        geoapify_place_id = None

        latitud = None

        longitud = None

    # =====================================================
    # SIN DOCUMENTO
    # =====================================================

    elif (
        tipo_documento
        == "SIN_DOCUMENTO"
    ):

        numero_documento = None

        datos_obtenidos_api = False

    return {

        "tipo_documento":
            tipo_documento,

        "numero_documento":
            numero_documento
            or None,

        "nombres":
            nombres
            or None,

        "apellidos":
            apellidos
            or None,

        "razon_social":
            razon_social
            or None,

        "correo":
            correo
            or None,

        "celular":
            celular
            or None,

        "direccion":
            direccion
            or None,

        "geoapify_place_id":
            geoapify_place_id
            or None,

        "latitud":
            latitud,

        "longitud":
            longitud,

        "datos_obtenidos_api":
            datos_obtenidos_api
    }


# =========================================================
# VALIDAR NUEVO
# =========================================================

def validar_nuevo(
    datos
):

    if datos[
        "tipo_documento"
    ] not in (
        "DNI",
        "RUC",
        "SIN_DOCUMENTO"
    ):

        return (
            "Seleccione un tipo de documento válido."
        )

    # =====================================================
    # DNI
    # =====================================================

    if (
        datos[
            "tipo_documento"
        ]
        == "DNI"
    ):

        dni = (
            datos[
                "numero_documento"
            ]
            or ""
        )

        if (
            not dni.isdigit()
            or len(
                dni
            ) != 8
        ):

            return (
                "El DNI debe contener "
                "exactamente 8 dígitos."
            )

        if not datos[
            "nombres"
        ]:

            return (
                "Los nombres son obligatorios."
            )

        if not datos[
            "apellidos"
        ]:

            return (
                "Los apellidos son obligatorios."
            )

    # =====================================================
    # RUC
    # =====================================================

    elif (
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
            or len(
                ruc
            ) != 11
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

    # =====================================================
    # SIN DOCUMENTO
    # =====================================================

    else:

        if (
            not datos[
                "razon_social"
            ]
            and not datos[
                "nombres"
            ]
        ):

            return (
                "Ingrese el nombre de la persona "
                "o la razón social del cliente."
            )

        if (
            datos[
                "nombres"
            ]
            and not datos[
                "apellidos"
            ]
        ):

            return (
                "Ingrese los apellidos del cliente."
            )

    return None