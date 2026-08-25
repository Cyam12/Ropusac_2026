import smtplib

from email.message import (
    EmailMessage
)

from flask import current_app


# =========================================================
# ERROR
# =========================================================

class ErrorCorreo(
    Exception
):

    pass


# =========================================================
# ENVIAR CORREO
# =========================================================

def enviar_correo(
    destinatario,
    asunto,
    cuerpo,
    archivo=None,
    nombre_archivo=None
):

    host = current_app.config.get(
        "SMTP_HOST"
    )

    port = current_app.config.get(
        "SMTP_PORT"
    )

    usuario = current_app.config.get(
        "SMTP_USER"
    )

    password = current_app.config.get(
        "SMTP_PASSWORD"
    )

    remitente = current_app.config.get(
        "SMTP_FROM_EMAIL"
    )

    nombre_remitente = (
        current_app.config.get(
            "SMTP_FROM_NAME"
        )
        or "ROPUSAC"
    )

    usar_tls = current_app.config.get(
        "SMTP_USE_TLS",
        True
    )

    usar_ssl = current_app.config.get(
        "SMTP_USE_SSL",
        False
    )

    # =====================================================
    # VALIDACION
    # =====================================================

    if not host:

        raise ErrorCorreo(
            "SMTP_HOST no está configurado."
        )

    if not port:

        raise ErrorCorreo(
            "SMTP_PORT no está configurado."
        )

    if not remitente:

        raise ErrorCorreo(
            (
                "SMTP_FROM_EMAIL "
                "no está configurado."
            )
        )

    if not destinatario:

        raise ErrorCorreo(
            (
                "El destinatario "
                "no tiene correo electrónico."
            )
        )

    # =====================================================
    # MENSAJE
    # =====================================================

    mensaje = EmailMessage()

    mensaje[
        "Subject"
    ] = asunto

    mensaje[
        "From"
    ] = (
        f"{nombre_remitente} "
        f"<{remitente}>"
    )

    mensaje[
        "To"
    ] = destinatario

    mensaje.set_content(
        cuerpo
    )

    # =====================================================
    # PDF
    # =====================================================

    if archivo:

        mensaje.add_attachment(
            archivo,
            maintype="application",
            subtype="pdf",
            filename=(
                nombre_archivo
                or "documento.pdf"
            )
        )

    # =====================================================
    # CONEXION
    # =====================================================

    try:

        if usar_ssl:

            servidor = smtplib.SMTP_SSL(
                host,
                port,
                timeout=30
            )

        else:

            servidor = smtplib.SMTP(
                host,
                port,
                timeout=30
            )

        with servidor:

            servidor.ehlo()

            if (
                usar_tls
                and not usar_ssl
            ):

                servidor.starttls()

                servidor.ehlo()

            if usuario:

                servidor.login(
                    usuario,
                    password
                )

            servidor.send_message(
                mensaje
            )

    except (
        smtplib.SMTPException,
        OSError
    ) as error:

        raise ErrorCorreo(
            (
                "No fue posible enviar "
                "el correo electrónico."
            )
        ) from error