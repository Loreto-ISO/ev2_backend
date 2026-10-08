from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Libro
from .forms import LibroForm

# R - Listar
def inicio(request):
    libros = Libro.objects.all()
    return render(request, 'app_libros/inicio.html', {'libros': libros})

# C - Crear
def crear_libro(request):
    if request.method == 'POST':
        form = LibroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '📚 ¡Libro agregado correctamente!')
            return redirect('inicio')
    else:
        form = LibroForm()
    return render(request, 'app_libros/crear.html', {'form': form})

# U - Editar
def editar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    if request.method == 'POST':
        form = LibroForm(request.POST, instance=libro)
        if form.is_valid():
            form.save()
            messages.success(request, '✏️ ¡Libro actualizado con éxito!')
            return redirect('inicio')
    else:
        form = LibroForm(instance=libro)
    return render(request, 'app_libros/editar.html', {'form': form, 'libro': libro})

# D - Eliminar
def eliminar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    if request.method == 'POST':
        libro.delete()
        messages.error(request, '🗑️ El libro ha sido eliminado del inventario.')
        return redirect('inicio')
    return render(request, 'app_libros/eliminar.html', {'libro': libro})