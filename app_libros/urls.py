from django.urls import path

from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # AutenticaciÃ³n
    path(
        "",
        views.login_view,
        name="login_pagina",
    ),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "registro/",
        views.registro,
        name="registro",
    ),
    path(
        "logout/",
        views.cerrar_sesion,
        name="logout_usuario",
    ),

    # Sitio pÃºblico
    path(
        "inicio/",
        views.inicio,
        name="inicio",
    ),
    path(
        "catalogo/",
        views.catalogo,
        name="catalogo",
    ),
    path(
        "producto/<int:id>/",
        views.detalle_producto,
        name="detalle_producto",
    ),

    path(
        "admin-panel/",
        views.admin_panel,
        name="admin_panel",
    ),

    # GestiÃ³n administrativa
    path(
        "crear/",
        views.crear_libro,
        name="crear_libro",
    ),
    path(
        "editar/<int:id>/",
        views.editar_libro,
        name="editar_libro",
    ),
    path(
        "eliminar/<int:id>/",
        views.eliminar_libro,
        name="eliminar_libro",
    ),

    path(
        "api/productos/",
        views.LibrosAPIView.as_view(),
        name="api_productos",
    ),

    path(
        "api/productos/<int:id>/",
        views.LibroDetalleAPIView.as_view(),
        name="api_producto_detalle",
    ),

        # Autenticación JWT
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "api/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify",
    ),

    path(
    "api/logout/",
    views.LogoutAPIView.as_view(),
    name="api_logout",
    ),
]
