from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError

# Importaciones de Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import Libro

# ==========================================
# 1. VISTAS HTML (Frontend / SPA)
# ==========================================
def login_pagina(request):
    return render(request, 'app_libros/login.html')

def registro_pagina(request):
    return render(request, 'app_libros/registro.html')

def inicio(request):
    return render(request, 'app_libros/inicio.html')

def crear_libro(request):
    return render(request, 'app_libros/crear.html')

def editar_libro(request, id):
    return render(request, 'app_libros/editar.html')

def eliminar_libro(request, id):
    return render(request, 'app_libros/eliminar.html')


# ==========================================
# 2. ENDPOINTS API DE SEGURIDAD Y USUARIOS
# ==========================================
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        usuario = authenticate(username=username, password=password)
        
        if usuario is not None:
            token, creado = Token.objects.get_or_create(user=usuario)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Credenciales incorrectas'}, status=status.HTTP_400_BAD_REQUEST)

class RegistroAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'El usuario y la contraseña son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = User.objects.create_user(username=username, password=password)
            return Response({'mensaje': 'Usuario creado exitosamente. Ya puedes iniciar sesión.'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'error': 'Ese nombre de usuario ya existe, elige otro.'}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 3. ENDPOINTS API REST DE LIBROS (CRUD)
# ==========================================
class LibrosApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        libros = Libro.objects.all()
        datos = [{'id': l.id, 'titulo': l.titulo, 'autor': l.autor, 'precio': l.precio, 'stock': l.stock} for l in libros]
        return Response(datos, status=status.HTTP_200_OK)

    def post(self, request):
        titulo = request.data.get('titulo')
        autor = request.data.get('autor')
        precio = request.data.get('precio')
        stock = request.data.get('stock')

        if not titulo or not autor or precio is None or stock is None:
            return Response({'error': 'Todos los campos son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            libro = Libro(titulo=titulo, autor=autor, precio=precio, stock=stock)
            libro.full_clean()  
            libro.save()
            return Response({
                'mensaje': 'Libro creado correctamente',
                'libro': {'id': libro.id, 'titulo': libro.titulo, 'autor': libro.autor, 'precio': libro.precio, 'stock': libro.stock}
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            mensaje_error = list(e.message_dict.values())[0][0]
            return Response({'error': mensaje_error}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LibroDetalleApiView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        libro = get_object_or_404(Libro, id=id)
        return Response({'id': libro.id, 'titulo': libro.titulo, 'autor': libro.autor, 'precio': libro.precio, 'stock': libro.stock}, status=status.HTTP_200_OK)

    def put(self, request, id):
        libro = get_object_or_404(Libro, id=id)
        
        libro.titulo = request.data.get('titulo', libro.titulo)
        libro.autor = request.data.get('autor', libro.autor)
        libro.precio = request.data.get('precio', libro.precio)
        libro.stock = request.data.get('stock', libro.stock)
        
        try:
            libro.full_clean()  
            libro.save() 
            return Response({'mensaje': 'Libro actualizado correctamente'}, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            mensaje_error = list(e.message_dict.values())[0][0]
            return Response({'error': mensaje_error}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        libro = get_object_or_404(Libro, id=id)
        libro.delete()
        return Response({'mensaje': 'Libro eliminado'}, status=status.HTTP_204_NO_CONTENT)