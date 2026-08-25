from decimal import Decimal

from html import escape

from io import BytesIO

from reportlab.lib import colors

from reportlab.lib.enums import (
    TA_CENTER
)

from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet
)

from reportlab.lib.units import mm

from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle
)

from app.extensiones import db

from app.modelos import (
    Cliente,
    Cotizacion,
    DetalleCotizacion,
    Usuario
)


# =========================================================
# AUXILIARES
# =========================================================

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


def nombre_usuario(
    usuario
):

    return " ".join(
        parte
        for parte in [
            usuario.nombres,
            usuario.apellidos
        ]
        if parte
    ).strip()


def simbolo_moneda(
    moneda
):

    return (
        "S/"
        if moneda == "PEN"
        else "US$"
    )


# =========================================================
# GENERAR PDF
# =========================================================

def generar_pdf_cotizacion(
    id_cotizacion
):

    cotizacion = db.session.get(
        Cotizacion,
        id_cotizacion
    )

    if cotizacion is None:

        raise ValueError(
            "La cotización no existe."
        )

    cliente = db.session.get(
        Cliente,
        cotizacion.id_cliente
    )

    vendedor = db.session.get(
        Usuario,
        cotizacion.id_vendedor
    )

    detalles = (
        db.session.execute(
            db.select(
                DetalleCotizacion
            )
            .where(
                DetalleCotizacion.id_cotizacion
                == cotizacion.id_cotizacion
            )
            .order_by(
                DetalleCotizacion.id_detalle_cotizacion.asc()
            )
        )
        .scalars()
        .all()
    )

    moneda = texto_enum(
        cotizacion.moneda
    )

    simbolo = simbolo_moneda(
        moneda
    )

    # =====================================================
    # IMPORTES
    # =====================================================

    subtotal = Decimal(
        cotizacion.subtotal
        or 0
    )

    total = Decimal(
        cotizacion.total
        or 0
    )

    igv = (
        total
        -
        subtotal
    )

    # =====================================================
    # BUFFER
    # =====================================================

    memoria = BytesIO()

    documento = SimpleDocTemplate(
        memoria,

        pagesize=A4,

        rightMargin=16 * mm,
        leftMargin=16 * mm,

        topMargin=15 * mm,
        bottomMargin=15 * mm,

        title=(
            cotizacion.numero_cotizacion
        )
    )

    estilos = getSampleStyleSheet()

    # =====================================================
    # ESTILOS
    # =====================================================

    estilo_titulo = ParagraphStyle(
        "TituloROPUSAC",

        parent=estilos[
            "Heading1"
        ],

        fontName="Helvetica-Bold",

        fontSize=18,

        leading=22,

        alignment=TA_CENTER,

        spaceAfter=5 * mm
    )


    estilo_subtitulo = ParagraphStyle(
        "SubtituloROPUSAC",

        parent=estilos[
            "Normal"
        ],

        fontName="Helvetica",

        fontSize=9,

        leading=12,

        alignment=TA_CENTER
    )


    estilo_etiqueta = ParagraphStyle(
        "EtiquetaROPUSAC",

        parent=estilos[
            "Normal"
        ],

        fontName="Helvetica-Bold",

        fontSize=8.5,

        leading=11
    )


    estilo_valor = ParagraphStyle(
        "ValorROPUSAC",

        parent=estilos[
            "Normal"
        ],

        fontName="Helvetica",

        fontSize=8.5,

        leading=11,

        wordWrap="CJK"
    )


    estilo_producto = ParagraphStyle(
        "ProductoROPUSAC",

        parent=estilos[
            "Normal"
        ],

        fontName="Helvetica",

        fontSize=8,

        leading=10,

        wordWrap="CJK"
    )


    elementos = []

    # =====================================================
    # TITULO
    # =====================================================

    elementos.append(
        Paragraph(
            "ROPUSAC",
            estilo_titulo
        )
    )

    elementos.append(
        Paragraph(
            (
                "Cotización Comercial"
                "<br/>"
                f"{escape(cotizacion.numero_cotizacion)}"
            ),
            estilo_subtitulo
        )
    )

    elementos.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # =====================================================
    # DATOS GENERALES
    #
    # IMPORTANTE:
    #
    # DIRECCION Y TIPO DE CAMBIO
    # TIENEN FILAS INDEPENDIENTES.
    # =====================================================

    datos_generales = [

        # FECHAS
        [
            Paragraph(
                "Fecha de emisión:",
                estilo_etiqueta
            ),

            Paragraph(
                cotizacion.fecha_emision.strftime(
                    "%d/%m/%Y"
                ),
                estilo_valor
            ),

            Paragraph(
                "Vigencia:",
                estilo_etiqueta
            ),

            Paragraph(
                cotizacion.fecha_vigencia.strftime(
                    "%d/%m/%Y"
                ),
                estilo_valor
            )
        ],

        # CLIENTE
        [
            Paragraph(
                "Cliente:",
                estilo_etiqueta
            ),

            Paragraph(
                escape(
                    nombre_cliente(
                        cliente
                    )
                ),
                estilo_valor
            ),

            Paragraph(
                "Documento:",
                estilo_etiqueta
            ),

            Paragraph(
                escape(
                    cliente.numero_documento
                    or "SIN DOCUMENTO"
                ),
                estilo_valor
            )
        ],

        # VENDEDOR Y MONEDA
        [
            Paragraph(
                "Vendedor:",
                estilo_etiqueta
            ),

            Paragraph(
                escape(
                    nombre_usuario(
                        vendedor
                    )
                ),
                estilo_valor
            ),

            Paragraph(
                "Moneda:",
                estilo_etiqueta
            ),

            Paragraph(
                escape(
                    moneda
                ),
                estilo_valor
            )
        ],

        # TIPO DE CAMBIO
        [
            Paragraph(
                "Tipo de cambio:",
                estilo_etiqueta
            ),

            Paragraph(
                (
                    "1 USD = "
                    f"{cotizacion.tipo_cambio_soles_por_dolar:.6f} "
                    "PEN"
                ),
                estilo_valor
            ),

            "",
            ""
        ],

        # DIRECCION
        [
            Paragraph(
                "Dirección:",
                estilo_etiqueta
            ),

            Paragraph(
                escape(
                    cliente.direccion
                    or "No registrada"
                ),
                estilo_valor
            ),

            "",
            ""
        ]
    ]


    tabla_general = Table(
        datos_generales,

        colWidths=[
            30 * mm,
            55 * mm,
            30 * mm,
            55 * mm
        ]
    )


    tabla_general.setStyle(
        TableStyle([

            # =============================================
            # TIPO CAMBIO OCUPA EL RESTO DE LA FILA
            # =============================================

            (
                "SPAN",
                (1, 3),
                (3, 3)
            ),

            # =============================================
            # DIRECCION OCUPA EL RESTO DE LA FILA
            # =============================================

            (
                "SPAN",
                (1, 4),
                (3, 4)
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3
            )

        ])
    )


    elementos.append(
        tabla_general
    )


    elementos.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # =====================================================
    # PRODUCTOS
    # =====================================================

    datos_productos = [
        [
            Paragraph(
                "<b>Código</b>",
                estilo_producto
            ),

            Paragraph(
                "<b>Producto</b>",
                estilo_producto
            ),

            Paragraph(
                "<b>Cantidad</b>",
                estilo_producto
            ),

            Paragraph(
                "<b>Precio final</b>",
                estilo_producto
            ),

            Paragraph(
                "<b>Importe</b>",
                estilo_producto
            )
        ]
    ]


    for detalle in detalles:

        datos_productos.append([

            Paragraph(
                escape(
                    detalle.codigo_producto
                    or ""
                ),
                estilo_producto
            ),

            Paragraph(
                escape(
                    detalle.nombre_producto
                    or ""
                ),
                estilo_producto
            ),

            Paragraph(
                f"{detalle.cantidad:g}",
                estilo_producto
            ),

            Paragraph(
                (
                    f"{simbolo} "
                    f"{detalle.precio_unitario:.2f}"
                ),
                estilo_producto
            ),

            Paragraph(
                (
                    f"{simbolo} "
                    f"{detalle.subtotal:.2f}"
                ),
                estilo_producto
            )

        ])


    tabla_productos = Table(
        datos_productos,

        colWidths=[
            26 * mm,
            70 * mm,
            22 * mm,
            28 * mm,
            28 * mm
        ],

        repeatRows=1
    )


    tabla_productos.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),

                colors.HexColor(
                    "#1f2937"
                )
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,

                colors.HexColor(
                    "#d1d5db"
                )
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "RIGHT"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )

        ])
    )


    elementos.append(
        tabla_productos
    )


    elementos.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # =====================================================
    # MONEDA EQUIVALENTE
    # =====================================================

    if moneda == "PEN":

        equivalente_texto = (
            "Equivalente total en USD"
        )

        simbolo_equivalente = (
            "US$"
        )

    else:

        equivalente_texto = (
            "Equivalente total en PEN"
        )

        simbolo_equivalente = (
            "S/"
        )

    # =====================================================
    # TOTALES
    # =====================================================

    tabla_totales = Table(
        [
            [
                "Subtotal",
                (
                    f"{simbolo} "
                    f"{subtotal:.2f}"
                )
            ],

            [
                "IGV incluido (18%)",
                (
                    f"{simbolo} "
                    f"{igv:.2f}"
                )
            ],

            [
                "TOTAL",
                (
                    f"{simbolo} "
                    f"{total:.2f}"
                )
            ],

            [
                equivalente_texto,
                (
                    f"{simbolo_equivalente} "
                    f"{cotizacion.total_equivalente:.2f}"
                )
            ]
        ],

        colWidths=[
            55 * mm,
            40 * mm
        ],

        hAlign="RIGHT"
    )


    tabla_totales.setStyle(
        TableStyle([

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica"
            ),

            (
                "FONTNAME",
                (0, 2),
                (-1, 2),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                10
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "RIGHT"
            ),

            (
                "LINEABOVE",
                (0, 2),
                (-1, 2),
                0.8,
                colors.black
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )

        ])
    )


    elementos.append(
        tabla_totales
    )

    # =====================================================
    # OBSERVACIONES
    # =====================================================

    if cotizacion.observaciones:

        elementos.append(
            Spacer(
                1,
                8 * mm
            )
        )


        elementos.append(
            Paragraph(
                "<b>Observaciones</b>",
                estilos[
                    "Normal"
                ]
            )
        )


        elementos.append(
            Spacer(
                1,
                2 * mm
            )
        )


        elementos.append(
            Paragraph(
                escape(
                    cotizacion.observaciones
                ),
                estilo_valor
            )
        )

    # =====================================================
    # PIE
    # =====================================================

    elementos.append(
        Spacer(
            1,
            10 * mm
        )
    )


    elementos.append(
        Paragraph(
            (
                "Documento generado por "
                "el Sistema ROPUSAC."
            ),
            estilo_subtitulo
        )
    )

    # =====================================================
    # GENERAR
    # =====================================================

    documento.build(
        elementos
    )


    memoria.seek(
        0
    )


    return memoria.getvalue()