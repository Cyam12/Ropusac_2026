import click

from flask.cli import with_appcontext
from sqlalchemy import func

from app.extensiones import db
from app.modelos import (
    Rol,
    Usuario,
    TipoDocumentoEnum
)


@click.command("crear-administrador")
@with_appcontext
def crear_administrador():
    """
    Crea un usuario con rol ADMINISTRADOR.
    """

    click.echo("")
    click.echo("======================================")
    click.echo(" CREAR ADMINISTRADOR - ROPUSAC")
    click.echo("======================================")
    click.echo("")

    # =====================================================
    # BUSCAR ROL ADMINISTRADOR
    # =====================================================

    rol = db.session.execute(
        db.select(Rol)
        .where(
            Rol.codigo == "ADMINISTRADOR"
        )
    ).scalar_one_or_none()

    if rol is None:

        click.echo(
            "ERROR: No existe el rol ADMINISTRADOR."
        )

        return

    # =====================================================
    # DATOS DEL USUARIO
    # =====================================================

    nombres = click.prompt(
        "Nombres",
        type=str
    ).strip()

    apellidos = click.prompt(
        "Apellidos",
        type=str
    ).strip()

    correo = click.prompt(
        "Correo electronico",
        type=str
    ).strip().lower()

    # =====================================================
    # VALIDAR CORREO
    # =====================================================

    usuario_existente = db.session.execute(
        db.select(Usuario)
        .where(
            func.lower(
                Usuario.correo
            ) == correo
        )
    ).scalar_one_or_none()

    if usuario_existente:

        click.echo("")
        click.echo(
            "ERROR: Ya existe un usuario "
            "con ese correo."
        )

        return

    # =====================================================
    # CONTRASEÑA
    # =====================================================

    contrasena = click.prompt(
        "Contrasena",
        hide_input=True,
        confirmation_prompt="Repita la contrasena"
    )

    if len(contrasena) < 8:

        click.echo("")
        click.echo(
            "ERROR: La contrasena debe tener "
            "como minimo 8 caracteres."
        )

        return

    # =====================================================
    # CREAR ADMINISTRADOR
    # =====================================================

    usuario = Usuario(
        id_rol=rol.id_rol,
        tipo_documento=TipoDocumentoEnum.SIN_DOCUMENTO,
        numero_documento=None,
        nombres=nombres,
        apellidos=apellidos,
        correo=correo,
        activo=True,
        datos_obtenidos_api=False
    )

    usuario.contrasena = contrasena

    try:

        db.session.add(usuario)

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        click.echo("")
        click.echo(
            "ERROR: No se pudo crear "
            "el administrador."
        )

        click.echo(
            f"Detalle: {error}"
        )

        return

    click.echo("")
    click.echo(
        "Administrador creado correctamente."
    )

    click.echo(
        f"ID: {usuario.id_usuario}"
    )

    click.echo(
        f"Usuario: {usuario.nombre_completo}"
    )

    click.echo(
        f"Correo: {usuario.correo}"
    )

    click.echo(
        f"Rol: {rol.nombre}"
    )

    click.echo("")


def registrar_comandos(app):

    app.cli.add_command(
        crear_administrador
    )