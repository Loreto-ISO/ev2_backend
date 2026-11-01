from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import Libro
from .forms import LibroForm

# --- VISTAS HTML ---
def login_pagina(request):
    return render(request, 'app_libros/login.html')

def inicio(request):
    return render(request, 'app_libros/inicio.html')

def crear_libro(request):
    return render(request, 'app_libros/crear.html')

def editar_libro(request, id):
    return render(request, 'app_libros/editar.html')

def eliminar_libro(request, id):
    return render(request, 'app_libros/eliminar.html')

# --- API REST DE EDUARDO (Login) ---
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        usuario = authenticate(username=username, password=password)

        if usuario is not None:
            token, creado = Token.objects.get_or_create(user=usuario)
            return Response({
                'mensaje': 'Autenticacion correcta',
                'usuario': usuario.username,
                'token': token.key
            }, status=status.HTTP_200_OK)
            
        return Response({'error': 'Usuario o contraseña incorrecta'}, status=status.HTTP_401_UNAUTHORIZED)

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
            # En lugar de objects.create(), preparamos el libro, LO LIMPIAMOS y luego guardamos
            libro = Libro(titulo=titulo, autor=autor, precio=precio, stock=stock)
            libro.full_clean()  # <--- ESTO ACTIVA LOS LIMITES DE EDUARDO EN MODELS.PY
            libro.save()
            return Response({
                'mensaje': 'Libro creado correctamente',
                'libro': {'id': libro.id, 'titulo': libro.titulo, 'autor': libro.autor, 'precio': libro.precio, 'stock': libro.stock}
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            # Captura el mensaje exacto de Eduardo (ej: "Un libro no puede costar más de $150.000")
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
            libro.full_clean()  # <--- VUELVE A VALIDAR AL EDITAR
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