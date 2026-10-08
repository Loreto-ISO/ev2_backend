from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal (sirve para listar y crear al mismo tiempo)
    path('', views.inicio, name='inicio'),
    
    # Rutas ocultas que procesan el Editar y Eliminar usando el ID del libro
    path('editar/<int:id>/', views.editar_libro, name='editar_libro'),
    path('eliminar/<int:id>/', views.eliminar_libro, name='eliminar_libro'),
]
