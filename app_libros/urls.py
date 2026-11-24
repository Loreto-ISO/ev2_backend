from django.urls import path

from . import views


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

    # API REST temporal
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
