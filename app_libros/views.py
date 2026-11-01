from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Libro
from .forms import LibroForm
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

# Read
def inicio(request):
    libros = Libro.objects.all()
    return render(request, 'app_libros/inicio.html', {'libros': libros})

# Create
def crear_libro(request):
    if request.method == 'POST':
        form = LibroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Libro agregado correctamente!')
            return redirect('inicio')
    else:
        form = LibroForm()
    return render(request, 'app_libros/crear.html', {'form': form})

# Update
def editar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    if request.method == 'POST':
        form = LibroForm(request.POST, instance=libro)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Libro actualizado con éxito!')
            return redirect('inicio')
    else:
        form = LibroForm(instance=libro)
    return render(request, 'app_libros/editar.html', {'form': form, 'libro': libro})

# Delete
def eliminar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    if request.method == 'POST':
        libro.delete()
        messages.error(request, 'El libro ha sido eliminado del inventario.')
        return redirect('inicio')
    return render(request, 'app_libros/eliminar.html', {'libro': libro})

def login_pagina(request):
    """Devuelve la pantalla HTML del login"""
    return render(request, 'app_libros/login.html')

class LoginAPIView(APIView):
    """API para validar usuario y devolver el Token"""
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
            
        return Response({
            'error': 'Usuario o contraseña incorrecta'
        }, status=status.HTTP_401_UNAUTHORIZED)