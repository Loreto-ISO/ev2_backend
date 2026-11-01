from django.urls import path
from . import views

urlpatterns = [
    # Pantallas HTML
    path('', views.login_pagina, name='login_pagina'),
    path('libros/', views.inicio, name='inicio'),
    path('crear/', views.crear_libro, name='crear_libro'),
    path('editar/<int:id>/', views.editar_libro, name='editar_libro'),
    path('eliminar/<int:id>/', views.eliminar_libro, name='eliminar_libro'),
    
    # Endpoints de Seguridad (Eduardo)
    path('api/login/', views.LoginAPIView.as_view(), name='login_api'),
    
    # Endpoints API REST (Loreto)
    path('api/libros/', views.LibrosApiView.as_view(), name='api_libros'),
    path('api/libros/<int:id>/', views.LibroDetalleApiView.as_view(), name='api_libro_detalle'),
]