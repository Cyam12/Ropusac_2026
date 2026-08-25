# =========================================================
# ENUMS
# =========================================================

from app.modelos.enumerados import (
    TipoDocumentoEnum,
    MonedaEnum,
    EstadoCotizacionEnum,
    EstadoImportacionEnum,
    EstadoVentaEnum,
    EstadoBoletaEnum,
    EstadoEnvioEnum,
    TipoDocumentoEnvioEnum,
    ServicioApiEnum,
)


# =========================================================
# MODELOS
# =========================================================

from app.modelos.rol import Rol
from app.modelos.permiso import Permiso
from app.modelos.rol_permiso import RolPermiso
from app.modelos.usuario import Usuario

from app.modelos.proveedor import Proveedor
from app.modelos.cliente import Cliente

from app.modelos.producto import Producto
from app.modelos.imagen_producto import ImagenProducto
from app.modelos.historial_precio_base import HistorialPrecioBase
from app.modelos.historial_precio_venta import HistorialPrecioVenta
from app.modelos.importacion_producto import ImportacionProducto

from app.modelos.tipo_cambio import TipoCambio
from app.modelos.cotizacion import Cotizacion
from app.modelos.detalle_cotizacion import DetalleCotizacion
from app.modelos.historial_estado_cotizacion import HistorialEstadoCotizacion

from app.modelos.venta import Venta
from app.modelos.detalle_venta import DetalleVenta
from app.modelos.boleta import Boleta

from app.modelos.envio_correo import EnvioCorreo
from app.modelos.registro_api import RegistroApi
from app.modelos.bitacora_operacion import BitacoraOperacion


__all__ = [

    # ENUMS
    "TipoDocumentoEnum",
    "MonedaEnum",
    "EstadoCotizacionEnum",
    "EstadoImportacionEnum",
    "EstadoVentaEnum",
    "EstadoBoletaEnum",
    "EstadoEnvioEnum",
    "TipoDocumentoEnvioEnum",
    "ServicioApiEnum",

    # MODELOS
    "Rol",
    "Permiso",
    "RolPermiso",
    "Usuario",
    "Proveedor",
    "Cliente",
    "Producto",
    "ImagenProducto",
    "HistorialPrecioBase",
    "HistorialPrecioVenta",
    "ImportacionProducto",
    "TipoCambio",
    "Cotizacion",
    "DetalleCotizacion",
    "HistorialEstadoCotizacion",
    "Venta",
    "DetalleVenta",
    "Boleta",
    "EnvioCorreo",
    "RegistroApi",
    "BitacoraOperacion"
]