from django.shortcuts import render, redirect, get_object_or_404
from .models import Libro
from .forms import LibroForm

# Función única para manejar el inicio, listar y crear libros
def inicio(request):
    libros = Libro.objects.all()
    
    if request.method == 'POST':
        form = LibroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inicio')
    else:
        form = LibroForm()
    
    # Pasamos 'editando': False porque estamos en modo "crear"
    return render(request, 'app_libros/inicio.html', {
        'libros': libros, 
        'form': form, 
        'editando': False
    })

# Función para editar un libro en la misma página principal
def editar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    libros = Libro.objects.all() # Necesitamos mandar la lista de nuevo para que se vea la tabla
    
    if request.method == 'POST':
        form = LibroForm(request.POST, instance=libro)
        if form.is_valid():
            form.save()
            return redirect('inicio')
    else:
        # Cargamos el formulario con los datos del libro existente
        form = LibroForm(instance=libro)
        
    # Pasamos 'editando': True para que el HTML cambie el diseño a amarillo (modo edición)
    return render(request, 'app_libros/inicio.html', {
        'libros': libros, 
        'form': form, 
        'editando': True,
        'libro_id': id
    })

# Función para eliminar (borra directamente y recarga el inicio)
def eliminar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    libro.delete()
    return redirect('inicio') # Redirige al inicio inmediatamente, no busca otro HTML