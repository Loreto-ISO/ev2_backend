from rest_framework.permissions import BasePermission, SAFE_METHODS


class SoloAdministradorOModoLectura(BasePermission):
    """
    Los usuarios autenticados pueden consultar productos.

    Solamente los administradores pueden crear,
    modificar o eliminar productos.
    """

    message = (
        "No tienes permisos administrativos "
        "para modificar productos."
    )

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(
                request.user
                and request.user.is_authenticated
            )

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )