import os
import time

from flask import Flask

from config import ConfigDesarrollo

from app.extensiones import (
    db,
    migrate,
    login_manager,
    csrf
)


# =========================================================
# CONFIGURAR ZONA HORARIA DEL PROCESO
# =========================================================

def configurar_zona_horaria():

    os.environ[
        "TZ"
    ] = "America/Lima"

    if hasattr(
        time,
        "tzset"
    ):

        time.tzset()


# =========================================================
# CREAR APP
# =========================================================

def crear_app(
    configuracion=ConfigDesarrollo
):

    configurar_zona_horaria()

    app = Flask(
        __name__,
        template_folder="plantillas",
        static_folder="static"
    )

    app.config.from_object(
        configuracion
    )

    # =====================================================
    # EXTENSIONES
    # =====================================================

    db.init_app(
        app
    )

    migrate.init_app(
        app,
        db,
        compare_type=True
    )

    login_manager.init_app(
        app
    )

    csrf.init_app(
        app
    )

    # =====================================================
    # LOGIN
    # =====================================================

    login_manager.login_view = (
        "autenticacion.login"
    )

    login_manager.login_message = (
        "Debes iniciar sesión para continuar."
    )

    login_manager.login_message_category = (
        "warning"
    )

    # =====================================================
    # MODELOS
    # =====================================================

    from app import modelos

    # =====================================================
    # AUTENTICACION
    # =====================================================

    from app.rutas.autenticacion import (
        bp as autenticacion_bp
    )

    app.register_blueprint(
        autenticacion_bp
    )

    # =====================================================
    # DASHBOARD
    # =====================================================

    from app.rutas.dashboard import (
        bp as dashboard_bp
    )

    app.register_blueprint(
        dashboard_bp
    )

    # =====================================================
    # ADMINISTRADOR
    # =====================================================

    from app.rutas.administrador import (
        bp as administrador_bp
    )

    app.register_blueprint(
        administrador_bp
    )


    from app.rutas.usuarios import (
        bp as usuarios_bp
    )

    app.register_blueprint(
        usuarios_bp
    )


    from app.rutas.proveedores import (
        bp as proveedores_bp
    )

    app.register_blueprint(
        proveedores_bp
    )


    from app.rutas.clientes import (
        bp as clientes_bp
    )

    app.register_blueprint(
        clientes_bp
    )


    from app.rutas.productos import (
        bp as productos_bp
    )

    app.register_blueprint(
        productos_bp
    )


    from app.rutas.precios_venta import (
        bp as precios_venta_bp
    )

    app.register_blueprint(
        precios_venta_bp
    )


    from app.rutas.cotizaciones_admin import (
        bp as cotizaciones_admin_bp
    )

    app.register_blueprint(
        cotizaciones_admin_bp
    )


    from app.rutas.boletas_admin import (
        bp as boletas_admin_bp
    )

    app.register_blueprint(
        boletas_admin_bp
    )

    # =====================================================
    # AREA COMERCIAL
    # =====================================================

    from app.rutas.proveedores_comercial import (
        bp as proveedores_comercial_bp
    )

    app.register_blueprint(
        proveedores_comercial_bp
    )


    from app.rutas.productos_comercial import (
        bp as productos_comercial_bp
    )

    app.register_blueprint(
        productos_comercial_bp
    )


    from app.rutas.precios_venta_comercial import (
        bp as precios_venta_comercial_bp
    )

    app.register_blueprint(
        precios_venta_comercial_bp
    )

    # =====================================================
    # VENDEDOR - CLIENTES
    # =====================================================

    from app.rutas.clientes_vendedor import (
        bp as clientes_vendedor_bp
    )

    app.register_blueprint(
        clientes_vendedor_bp
    )

    # =====================================================
    # VENDEDOR - PRODUCTOS
    # =====================================================

    from app.rutas.productos_vendedor import (
        bp as productos_vendedor_bp
    )

    app.register_blueprint(
        productos_vendedor_bp
    )

    # =====================================================
    # VENDEDOR - COTIZACIONES
    # =====================================================

    from app.rutas.cotizaciones_vendedor import (
        bp as cotizaciones_vendedor_bp
    )

    app.register_blueprint(
        cotizaciones_vendedor_bp
    )

    # =====================================================
    # VENDEDOR - BOLETAS
    # =====================================================

    from app.rutas.boletas_vendedor import (
        bp as boletas_vendedor_bp
    )

    app.register_blueprint(
        boletas_vendedor_bp
    )

    # =====================================================
    # DOCUMENTOS
    # =====================================================

    from app.rutas.documentos import (
        bp as documentos_bp
    )

    app.register_blueprint(
        documentos_bp
    )

    # =====================================================
    # INTEGRACIONES
    # =====================================================

    from app.rutas.integraciones import (
        bp as integraciones_bp
    )

    app.register_blueprint(
        integraciones_bp
    )

    # =====================================================
    # COMANDOS
    # =====================================================

    from app.comandos import (
        registrar_comandos
    )

    registrar_comandos(
        app
    )

    return app