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

from sqlalchemy import or_

from app.extensiones import db

from app.modelos import (
    Cliente,
    TipoDocumentoEnum
)

from app.utilidades.decoradores import (
    rol_requerido
)


bp = Blueprint(
    "clientes",
    __name__,
    url_prefix="/administrador/clientes"
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

    # =====================================================
    # SOPORTAR OBJETO ORM
    # =====================================================

    if not isinstance(
        cliente,
        dict
    ):

        if cliente.razon_social:

            return cliente.razon_social

        return " ".join(
            parte
            for parte in [
                cliente.nombres,
                cliente.apellidos
            ]
            if parte
        ).strip()

    # =====================================================
    # SOPORTAR DICCIONARIO DEL LISTADO
    # =====================================================

    if cliente.get(
        "razon_social"
    ):

        return cliente[
            "razon_social"
        ]

    return " ".join(
        parte
        for parte in [
            cliente.get(
                "nombres"
            ),

            cliente.get(
                "apellidos"
            )
        ]
        if parte
    ).strip()


# =========================================================
# LISTAR
#
# OPTIMIZADO PARA RENDER:
#
# - MAXIMO 20 CLIENTES POR PAGINA
# - TRAE SOLO COLUMNAS NECESARIAS
# - NO CARGA TODOS LOS CLIENTES A RAM
# - NO CREA OBJETOS ORM COMPLETOS
# =========================================================

@bp.get("/")
@rol_requerido(
    "ADMINISTRADOR"
)
def lista():

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
    # CONSULTA BASE
    #
    # IMPORTANTE:
    #
    # ANTES:
    #
    # db.select(Cliente)
    #
    # ESO CARGABA EL OBJETO COMPLETO.
    #
    # AHORA SOLO OBTENEMOS LO QUE LA TABLA NECESITA.
    # =====================================================

    consulta = (
        db.select(

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

            Cliente.telefono.label(
                "telefono"
            ),

            Cliente.direccion.label(
                "direccion"
            ),

            Cliente.activo.label(
                "activo"
            ),

            Cliente.datos_obtenidos_api.label(
                "datos_obtenidos_api"
            ),

            Cliente.creado_en.label(
                "creado_en"
            )
        )
        .select_from(
            Cliente
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
                )
            )
        )

    # =====================================================
    # PAGINACION
    #
    # PEDIMOS 21 REGISTROS.
    #
    # 20 = LOS QUE MOSTRAMOS
    # 21 = NOS INDICA SI EXISTE PAGINA SIGUIENTE
    #
    # ASI EVITAMOS HACER COUNT(*) DE TODA LA TABLA.
    # =====================================================

    offset = (
        pagina - 1
    ) * CLIENTES_POR_PAGINA

    consulta = (
        consulta
        .order_by(
            Cliente.creado_en.desc(),
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
    # EXISTE PAGINA SIGUIENTE
    # =====================================================

    hay_siguiente = (
        len(
            filas
        )
        >
        CLIENTES_POR_PAGINA
    )

    # =====================================================
    # SOLO CONSERVAMOS LOS 20 QUE MOSTRAREMOS
    # =====================================================

    filas = filas[
        :CLIENTES_POR_PAGINA
    ]

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

            "telefono":
                fila[
                    "telefono"
                ],

            "direccion":
                fila[
                    "direccion"
                ],

            "activo":
                fila[
                    "activo"
                ],

            "datos_obtenidos_api":
                fila[
                    "datos_obtenidos_api"
                ],

            "creado_en":
                fila[
                    "creado_en"
                ]
        }

        cliente[
            "nombre_mostrar"
        ] = nombre_cliente(
            cliente
        )

        clientes.append(
            cliente
        )

    # =====================================================
    # PAGINA ANTERIOR
    # =====================================================

    hay_anterior = (
        pagina > 1
    )

    # =====================================================
    # SI ALGUIEN INGRESA MANUALMENTE A UNA PAGINA
    # QUE YA NO TIENE REGISTROS, REGRESAR UNA PAGINA.
    # =====================================================

    if (
        pagina > 1
        and not clientes
    ):

        return redirect(
            url_for(
                "clientes.lista",

                pagina=(
                    pagina - 1
                ),

                buscar=buscar
            )
        )

    return render_template(
        "administrador/clientes/lista.html",

        clientes=clientes,

        buscar=buscar,

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
    "ADMINISTRADOR"
)
def detalle(
    id_cliente
):

    cliente = db.get_or_404(
        Cliente,
        id_cliente
    )

    return render_template(
        "administrador/clientes/detalle.html",

        cliente=cliente,

        nombre_cliente=(
            nombre_cliente(
                cliente
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
    "ADMINISTRADOR"
)
def nuevo():

    if request.method == "POST":

        datos = obtener_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "administrador/clientes/formulario.html",
                cliente=None
            )

        # =================================================
        # DOCUMENTO DUPLICADO
        #
        # SOLO CONSULTAMOS EL ID.
        # NO NECESITAMOS CARGAR TODO EL CLIENTE.
        # =================================================

        if datos[
            "numero_documento"
        ]:

            existe = (
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

            if existe is not None:

                flash(
                    (
                        "Ya existe un cliente "
                        "registrado con ese documento."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/clientes/formulario.html",
                    cliente=None
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

            telefono=(
                datos[
                    "telefono"
                ]
            ),

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
                "ERROR REGISTRANDO CLIENTE:",
                error_bd
            )

            flash(
                "No se pudo registrar el cliente.",
                "danger"
            )

            return render_template(
                "administrador/clientes/formulario.html",
                cliente=None
            )

        flash(
            "Cliente registrado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "clientes.lista"
            )
        )

    return render_template(
        "administrador/clientes/formulario.html",
        cliente=None
    )


# =========================================================
# EDITAR
# =========================================================

@bp.route(
    "/<int:id_cliente>/editar",
    methods=[
        "GET",
        "POST"
    ]
)
@rol_requerido(
    "ADMINISTRADOR"
)
def editar(
    id_cliente
):

    cliente = db.get_or_404(
        Cliente,
        id_cliente
    )

    if request.method == "POST":

        datos = obtener_formulario()

        error = validar_datos(
            datos
        )

        if error:

            flash(
                error,
                "danger"
            )

            return render_template(
                "administrador/clientes/formulario.html",
                cliente=cliente
            )

        # =================================================
        # DOCUMENTO DUPLICADO
        #
        # SOLO CONSULTAMOS EL ID DEL OTRO CLIENTE.
        # =================================================

        if datos[
            "numero_documento"
        ]:

            existe = (
                db.session.execute(
                    db.select(
                        Cliente.id_cliente
                    )
                    .where(
                        Cliente.numero_documento
                        == datos[
                            "numero_documento"
                        ],

                        Cliente.id_cliente
                        != cliente.id_cliente
                    )
                    .limit(
                        1
                    )
                )
                .scalar_one_or_none()
            )

            if existe is not None:

                flash(
                    (
                        "Ya existe otro cliente "
                        "registrado con ese documento."
                    ),
                    "danger"
                )

                return render_template(
                    "administrador/clientes/formulario.html",
                    cliente=cliente
                )

        documento_anterior = (
            cliente.numero_documento
        )

        datos_api_anteriores = (
            cliente.datos_obtenidos_api
        )

        # =================================================
        # ACTUALIZAR
        # =================================================

        cliente.tipo_documento = (
            TipoDocumentoEnum(
                datos[
                    "tipo_documento"
                ]
            )
        )

        cliente.numero_documento = (
            datos[
                "numero_documento"
            ]
        )

        cliente.nombres = (
            datos[
                "nombres"
            ]
        )

        cliente.apellidos = (
            datos[
                "apellidos"
            ]
        )

        cliente.razon_social = (
            datos[
                "razon_social"
            ]
        )

        cliente.correo = (
            datos[
                "correo"
            ]
        )

        cliente.celular = (
            datos[
                "celular"
            ]
        )

        cliente.telefono = (
            datos[
                "telefono"
            ]
        )

        cliente.direccion = (
            datos[
                "direccion"
            ]
        )

        cliente.geoapify_place_id = (
            datos[
                "geoapify_place_id"
            ]
        )

        cliente.latitud = (
            datos[
                "latitud"
            ]
        )

        cliente.longitud = (
            datos[
                "longitud"
            ]
        )

        cliente.datos_obtenidos_api = (
            datos[
                "datos_obtenidos_api"
            ]
        )

        cliente.actualizado_por = (
            current_user.id_usuario
        )

        if not datos[
            "datos_obtenidos_api"
        ]:

            cliente.api_consultada_en = (
                None
            )

        elif (
            not datos_api_anteriores
            or documento_anterior
            != datos[
                "numero_documento"
            ]
        ):

            cliente.api_consultada_en = (
                datetime.now(
                    timezone.utc
                )
            )

        try:

            db.session.commit()

        except Exception as error_bd:

            db.session.rollback()

            print(
                "ERROR ACTUALIZANDO CLIENTE:",
                error_bd
            )

            flash(
                "No se pudo actualizar el cliente.",
                "danger"
            )

            return render_template(
                "administrador/clientes/formulario.html",
                cliente=cliente
            )

        flash(
            "Cliente actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "clientes.detalle",

                id_cliente=(
                    cliente.id_cliente
                )
            )
        )

    return render_template(
        "administrador/clientes/formulario.html",
        cliente=cliente
    )


# =========================================================
# OBTENER FORMULARIO
# =========================================================

def obtener_formulario():

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

    telefono = (
        request.form.get(
            "telefono",
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

    datos_obtenidos_api = (
        request.form.get(
            "datos_obtenidos_api",
            "0"
        )
        == "1"
    )

    # =====================================================
    # AJUSTAR SEGUN DOCUMENTO
    # =====================================================

    if tipo_documento == "DNI":

        razon_social = ""

    elif tipo_documento == "RUC":

        nombres = ""
        apellidos = ""

        # Geoapify no se usa para RUC.
        geoapify_place_id = ""
        latitud = None
        longitud = None

    elif tipo_documento == "SIN_DOCUMENTO":

        numero_documento = ""
        datos_obtenidos_api = False

    return {
        "tipo_documento":
            tipo_documento,

        "numero_documento":
            (
                numero_documento
                or None
            ),

        "nombres":
            (
                nombres
                or None
            ),

        "apellidos":
            (
                apellidos
                or None
            ),

        "razon_social":
            (
                razon_social
                or None
            ),

        "correo":
            (
                correo
                or None
            ),

        "celular":
            (
                celular
                or None
            ),

        "telefono":
            (
                telefono
                or None
            ),

        "direccion":
            (
                direccion
                or None
            ),

        "geoapify_place_id":
            (
                geoapify_place_id
                or None
            ),

        "latitud":
            latitud,

        "longitud":
            longitud,

        "datos_obtenidos_api":
            datos_obtenidos_api
    }


# =========================================================
# VALIDAR
# =========================================================

def validar_datos(
    datos
):

    tipo = datos[
        "tipo_documento"
    ]

    if tipo not in (
        "DNI",
        "RUC",
        "SIN_DOCUMENTO"
    ):

        return (
            "Tipo de documento inválido."
        )

    # =====================================================
    # DNI
    # =====================================================

    if tipo == "DNI":

        documento = (
            datos[
                "numero_documento"
            ]
            or ""
        )

        if (
            not documento.isdigit()
            or len(
                documento
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
                "Los nombres del cliente "
                "son obligatorios."
            )

        if not datos[
            "apellidos"
        ]:

            return (
                "Los apellidos del cliente "
                "son obligatorios."
            )

    # =====================================================
    # RUC
    # =====================================================

    elif tipo == "RUC":

        documento = (
            datos[
                "numero_documento"
            ]
            or ""
        )

        if (
            not documento.isdigit()
            or len(
                documento
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
                "La razón social "
                "es obligatoria."
            )

    # =====================================================
    # SIN DOCUMENTO
    # =====================================================

    else:

        if (
            not datos[
                "nombres"
            ]
            and not datos[
                "razon_social"
            ]
        ):

            return (
                "Ingrese los nombres del cliente "
                "o una razón social."
            )

    return None