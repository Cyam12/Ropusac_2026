from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def rol_requerido(*roles_permitidos):

    def decorador(funcion):

        @wraps(funcion)
        @login_required
        def funcion_protegida(*args, **kwargs):

            if not current_user.activo:
                abort(403)

            if current_user.codigo_rol not in roles_permitidos:
                abort(403)

            return funcion(*args, **kwargs)

        return funcion_protegida

    return decorador