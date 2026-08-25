import os

from app import crear_app


# =========================================================
# CREAR APLICACION
# =========================================================

app = crear_app()



if __name__ == "__main__":

    puerto = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "false"
        ).lower()
        ==
        "true"
    )

    app.run(
        host="0.0.0.0",
        port=puerto,
        debug=debug
    )