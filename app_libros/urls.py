from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_pagina, name='login_pagina'),
    path('registro/', views.registro_pagina, name='registro_pagina'),
    path('libros/', views.inicio, name='inicio'),
    path('crear/', views.crear_libro, name='crear_libro'),
    path('editar/<int:id>/', views.editar_libro, name='editar_libro'),
    path('eliminar/<int:id>/', views.eliminar_libro, name='eliminar_libro'),
    
    # ==========================================
    # 2. ENDPOINTS DE SEGURIDAD (API REST)
    # ==========================================
    path('api/login/', views.LoginAPIView.as_view(), name='login_api'),
    path('api/registro/', views.RegistroAPIView.as_view(), name='registro_api'),
    
    # ==========================================
    # 3. ENDPOINTS DE LIBROS (API REST CRUD)
    # ==========================================
    path('api/libros/', views.LibrosApiView.as_view(), name='api_libros'),
    path('api/libros/<int:id>/', views.LibroDetalleApiView.as_view(), name='api_libro_detalle'),
]