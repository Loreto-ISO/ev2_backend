from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views


urlpatterns = [
    # Sitio web
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

    # Gestión administrativa
    path(
        "admin-panel/",
        views.admin_panel,
        name="admin_panel",
    ),
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

    # JWT
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

    # Productos API
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
]

