from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categoria, Producto

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .permissions import SoloAdministradorOModoLectura
from .serializers import ProductoSerializer


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def producto_a_diccionario(producto):
    """
    Convierte un objeto Producto en un diccionario para la API.
    Esta función es temporal hasta que Eduardo implemente serializers.
    """

    imagen_url = None

    if producto.imagen:
        imagen_url = producto.imagen.url

    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "categoria": {
            "id": producto.categoria.id,
            "nombre": producto.categoria.nombre,
            "slug": producto.categoria.slug,
        },
        "precio": str(producto.precio),
        "stock": producto.stock,
        "imagen": imagen_url,
        "activo": producto.activo,
        "creado_en": producto.creado_en,
        "actualizado_en": producto.actualizado_en,
    }


def es_administrador(usuario):
    """
    Devuelve True solamente cuando el usuario está autenticado
    y tiene permiso de administración.
    """

    return usuario.is_authenticated and usuario.is_staff


# ============================================================
# PÁGINAS PÚBLICAS
# ============================================================

def inicio(request):
    """
    Página principal pública de Librería Doña Zoyla.
    """

    productos_destacados = (
        Producto.objects
        .filter(activo=True)
        .select_related("categoria")
        .order_by("-creado_en")[:8]
    )

    categorias = Categoria.objects.filter(
        activa=True,
    ).order_by("nombre")

    return render(
        request,
        "app_libros/inicio.html",
        {
            "productos_destacados": productos_destacados,
            "categorias": categorias,
        },
    )

def catalogo(request):
    """
    Catálogo público con buscador y filtro por categoría.

    Ejemplos:
    /catalogo/?q=cuaderno
    /catalogo/?categoria=novelas
    /catalogo/?q=papel&categoria=resmas-papeles
    """
    productos = (
        Producto.objects
        .filter(activo=True)
        .select_related("categoria")
        .order_by("nombre")
    )

    consulta = request.GET.get("q", "").strip()
    categoria_slug = request.GET.get("categoria", "").strip()

    if consulta:
        productos = productos.filter(
            Q(nombre__icontains=consulta)
            | Q(descripcion__icontains=consulta)
            | Q(categoria__nombre__icontains=consulta)
        )

    if categoria_slug:
        productos = productos.filter(
            categoria__slug=categoria_slug,
        )

    categorias = Categoria.objects.filter(
        activa=True,
    ).order_by("nombre")

    return render(
        request,
        "app_libros/catalogo.html",
        {
            "productos": productos,
            "categorias": categorias,
            "consulta": consulta,
            "categoria_seleccionada": categoria_slug,
        },
    )


def detalle_producto(request, id):
    """
    Muestra un producto público.
    """

    producto = get_object_or_404(
        Producto.objects.select_related("categoria"),
        id=id,
        activo=True,
    )

    return render(
        request,
        "app_libros/detalle_producto.html",
        {
            "producto": producto,
        },
    )


# ============================================================
# REGISTRO DE CLIENTES
# ============================================================

def registro(request):
    """
    Registra exclusivamente cuentas de clientes.

    Los administradores no deben registrarse desde esta página.
    Deben crearse mediante createsuperuser o Django Admin.
    """

    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        confirmar_password = request.POST.get(
            "confirmar_password",
            request.POST.get("password2", ""),
        )

        # Validación del nombre de usuario.
        if len(username) < 4 or len(username) > 30:
            messages.error(
                request,
                (
                    "El nombre de usuario debe tener "
                    "entre 4 y 30 caracteres."
                ),
            )

            return render(
                request,
                "app_libros/registro.html",
                {
                    "username": username,
                },
            )

        # Solo letras, números y guion bajo.
        if not username.replace("_", "").isalnum():
            messages.error(
                request,
                (
                    "El nombre de usuario solo puede contener "
                    "letras, números y guion bajo."
                ),
            )

            return render(
                request,
                "app_libros/registro.html",
                {
                    "username": username,
                },
            )

        if User.objects.filter(username__iexact=username).exists():
            messages.error(
                request,
                "El nombre de usuario ya está registrado.",
            )

            return render(
                request,
                "app_libros/registro.html",
                {
                    "username": username,
                },
            )

        if password != confirmar_password:
            messages.error(
                request,
                "Las contraseñas no coinciden.",
            )

            return render(
                request,
                "app_libros/registro.html",
                {
                    "username": username,
                },
            )

        # Reglas solicitadas por el profesor.
        errores_password = []

        if len(password) < 8:
            errores_password.append(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if not any(caracter.isupper() for caracter in password):
            errores_password.append(
                "La contraseña debe incluir una letra mayúscula."
            )

        if not any(caracter.islower() for caracter in password):
            errores_password.append(
                "La contraseña debe incluir una letra minúscula."
            )

        if not any(caracter.isdigit() for caracter in password):
            errores_password.append(
                "La contraseña debe incluir un número."
            )

        if not any(
            not caracter.isalnum()
            for caracter in password
        ):
            errores_password.append(
                "La contraseña debe incluir un signo especial."
            )

        if errores_password:
            for error in errores_password:
                messages.error(request, error)

            return render(
                request,
                "app_libros/registro.html",
                {
                    "username": username,
                },
            )

        # Validadores de seguridad incorporados en Django.
        usuario_temporal = User(username=username)

        try:
            validate_password(
                password,
                user=usuario_temporal,
            )
        except ValidationError as errores:
            for error in errores.messages:
                messages.error(request, error)

            return render(
                request,
                "app_libros/registro.html",
                {
                    "username": username,
                },
            )

        usuario = User.objects.create_user(
            username=username,
            password=password,
        )

        # Toda cuenta creada públicamente será cliente.
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.save()

        messages.success(
            request,
            "Tu cuenta fue creada correctamente. Ya puedes iniciar sesión.",
        )

        return redirect("login")

    return render(
        request,
        "app_libros/registro.html",
    )


# Alias por si urls.py utiliza registro_usuario.
registro_usuario = registro
registro_cliente = registro


# ============================================================
# AUTENTICACIÓN WEB
# ============================================================

def login_view(request):
    """
    Inicio de sesión web para clientes y administradores.
    JWT será agregado posteriormente por Eduardo en su rama.
    """

    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("inicio")

        return redirect("catalogo")

    if request.method == "POST":
        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        if not username or not password:
            messages.error(
                request,
                "Debes ingresar el usuario y la contraseña.",
            )

            return render(
                request,
                "app_libros/login_cliente.html",
                {
                    "username": username,
                },
            )

        usuario = authenticate(
            request,
            username=username,
            password=password,
        )

        if usuario is None:
            messages.error(
                request,
                "El nombre de usuario o la contraseña son incorrectos.",
            )

            return render(
                request,
                "app_libros/login_cliente.html",
                {
                    "username": username,
                },
            )

        if not usuario.is_active:
            messages.error(
                request,
                "Esta cuenta está desactivada.",
            )

            return render(
                request,
                "app_libros/login_cliente.html",
            )

        login(request, usuario)

        messages.success(
            request,
            f"Bienvenido, {usuario.username}.",
        )

        if usuario.is_staff:
            return redirect("inicio")

        return redirect("catalogo")

    return render(
        request,
        "app_libros/login_cliente.html",
    )


def cerrar_sesion(request):
    logout(request)

    messages.success(
        request,
        "La sesión fue cerrada correctamente.",
    )

    return redirect("login")


# Alias de compatibilidad.
login_usuario = login_view
login_cliente = login_view
logout_usuario = cerrar_sesion


# ============================================================
# ADMINISTRACIÓN DE PRODUCTOS
# ============================================================

def crear_libro(request):
    """
    Mantiene el nombre crear_libro para no romper las rutas antiguas,
    pero crea objetos del modelo Producto.
    """

    if not request.user.is_authenticated:
        messages.error(
            request,
            "Debes iniciar sesión para acceder.",
        )
        return redirect("login")

    if not request.user.is_staff:
        messages.error(
            request,
            "No tienes autorización para crear productos.",
        )
        return redirect("catalogo")

    categorias = Categoria.objects.filter(
        activa=True,
    ).order_by("nombre")

    if request.method == "POST":
        nombre = request.POST.get(
            "nombre",
            request.POST.get("titulo", ""),
        ).strip()

        descripcion = request.POST.get(
            "descripcion",
            "",
        ).strip()

        categoria_id = request.POST.get(
            "categoria",
            "",
        )

        precio = request.POST.get(
            "precio",
            "",
        )

        stock = request.POST.get(
            "stock",
            "",
        )

        imagen = request.FILES.get("imagen")

        if not nombre:
            messages.error(
                request,
                "El nombre del producto es obligatorio.",
            )

            return render(
                request,
                "app_libros/crear.html",
                {
                    "categorias": categorias,
                },
            )

        if not descripcion:
            messages.error(
                request,
                "La descripción es obligatoria.",
            )

            return render(
                request,
                "app_libros/crear.html",
                {
                    "categorias": categorias,
                },
            )

        categoria = get_object_or_404(
            Categoria,
            id=categoria_id,
            activa=True,
        )

        try:
            producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                precio=precio,
                stock=stock,
                imagen=imagen,
                activo=True,
            )

            producto.full_clean()
            producto.save()

        except ValidationError as errores:
            for campo, mensajes_campo in errores.message_dict.items():
                for mensaje in mensajes_campo:
                    messages.error(
                        request,
                        f"{campo}: {mensaje}",
                    )

            return render(
                request,
                "app_libros/crear.html",
                {
                    "categorias": categorias,
                },
            )

        messages.success(
            request,
            "Producto creado correctamente.",
        )

        return redirect("inicio")

    return render(
        request,
        "app_libros/crear.html",
        {
            "categorias": categorias,
        },
    )


def editar_libro(request, id):
    """
    Mantiene el nombre editar_libro por compatibilidad.
    """

    if not request.user.is_authenticated:
        messages.error(
            request,
            "Debes iniciar sesión para acceder.",
        )
        return redirect("login")

    if not request.user.is_staff:
        messages.error(
            request,
            "No tienes autorización para editar productos.",
        )
        return redirect("catalogo")

    producto = get_object_or_404(
        Producto,
        id=id,
    )

    categorias = Categoria.objects.filter(
        activa=True,
    ).order_by("nombre")

    if request.method == "POST":
        producto.nombre = request.POST.get(
            "nombre",
            request.POST.get("titulo", producto.nombre),
        ).strip()

        producto.descripcion = request.POST.get(
            "descripcion",
            producto.descripcion,
        ).strip()

        categoria_id = request.POST.get(
            "categoria",
            producto.categoria_id,
        )

        producto.categoria = get_object_or_404(
            Categoria,
            id=categoria_id,
            activa=True,
        )

        producto.precio = request.POST.get(
            "precio",
            producto.precio,
        )

        producto.stock = request.POST.get(
            "stock",
            producto.stock,
        )

        producto.activo = (
            request.POST.get("activo") == "on"
            or request.POST.get("activo") == "true"
            or request.POST.get("activo") == "1"
        )

        nueva_imagen = request.FILES.get("imagen")

        if nueva_imagen:
            producto.imagen = nueva_imagen

        try:
            producto.full_clean()
            producto.save()

        except ValidationError as errores:
            for campo, mensajes_campo in errores.message_dict.items():
                for mensaje in mensajes_campo:
                    messages.error(
                        request,
                        f"{campo}: {mensaje}",
                    )

            return render(
                request,
                "app_libros/editar.html",
                {
                    "producto": producto,
                    "libro": producto,
                    "categorias": categorias,
                },
            )

        messages.success(
            request,
            "Producto actualizado correctamente.",
        )

        return redirect("inicio")

    return render(
        request,
        "app_libros/editar.html",
        {
            "producto": producto,
            # Compatibilidad temporal con los templates antiguos.
            "libro": producto,
            "categorias": categorias,
        },
    )


def eliminar_libro(request, id):
    """
    Mantiene el nombre eliminar_libro por compatibilidad.
    """

    if not request.user.is_authenticated:
        messages.error(
            request,
            "Debes iniciar sesión para acceder.",
        )
        return redirect("login")

    if not request.user.is_staff:
        messages.error(
            request,
            "No tienes autorización para eliminar productos.",
        )
        return redirect("catalogo")

    producto = get_object_or_404(
        Producto,
        id=id,
    )

    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()

        messages.success(
            request,
            f'El producto "{nombre}" fue eliminado.',
        )

        return redirect("inicio")

    return render(
        request,
        "app_libros/eliminar.html",
        {
            "producto": producto,
            # Compatibilidad temporal con el template antiguo.
            "libro": producto,
        },
    )


# Alias nuevos para cuando se actualicen urls.py.
crear_producto = crear_libro
editar_producto = editar_libro
eliminar_producto = eliminar_libro

def admin_panel(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_staff:
        return redirect("catalogo")

    productos = Producto.objects.all().order_by("nombre")

    return render(
        request,
        "app_libros/admin_panel.html",
        {
            "productos": productos,
        },
    )

class LibrosAPIView(APIView):
    """
    GET: lista los productos activos.

    POST: crea un producto.
    Solo puede utilizarlo un administrador.
    """

    permission_classes = [
        IsAuthenticated,
        SoloAdministradorOModoLectura,
    ]

    parser_classes = [
        JSONParser,
        FormParser,
        MultiPartParser,
    ]

    def get(self, request):
        productos = (
            Producto.objects
            .filter(activo=True)
            .select_related("categoria")
            .order_by("nombre")
        )

        serializer = ProductoSerializer(
            productos,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "cantidad": productos.count(),
                "resultados": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = ProductoSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        if not serializer.is_valid():
            return Response(
                {
                    "error": "Los datos enviados no son válidos.",
                    "detalles": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto = serializer.save()

        respuesta = ProductoSerializer(
            producto,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "mensaje": "Producto creado correctamente.",
                "producto": respuesta.data,
            },
            status=status.HTTP_201_CREATED,
        )

class LibroDetalleAPIView(APIView):
    """
    GET: obtiene un producto.

    PUT: reemplaza los datos de un producto.

    PATCH: actualiza parcialmente un producto.

    DELETE: elimina un producto.
    """

    permission_classes = [
        IsAuthenticated,
        SoloAdministradorOModoLectura,
    ]

    parser_classes = [
        JSONParser,
        FormParser,
        MultiPartParser,
    ]

    def obtener_producto(self, id):
        return get_object_or_404(
            Producto.objects.select_related("categoria"),
            id=id,
        )

    def get(self, request, id):
        producto = self.obtener_producto(id)

        serializer = ProductoSerializer(
            producto,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, id):
        producto = self.obtener_producto(id)

        serializer = ProductoSerializer(
            producto,
            data=request.data,
            context={
                "request": request,
            },
        )

        if not serializer.is_valid():
            return Response(
                {
                    "error": "Los datos enviados no son válidos.",
                    "detalles": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto = serializer.save()

        respuesta = ProductoSerializer(
            producto,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "mensaje": "Producto actualizado correctamente.",
                "producto": respuesta.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, id):
        producto = self.obtener_producto(id)

        serializer = ProductoSerializer(
            producto,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        if not serializer.is_valid():
            return Response(
                {
                    "error": "Los datos enviados no son válidos.",
                    "detalles": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        producto = serializer.save()

        respuesta = ProductoSerializer(
            producto,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "mensaje": "Producto actualizado parcialmente.",
                "producto": respuesta.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        producto = self.obtener_producto(id)
        producto.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

LibrosApiView = LibrosAPIView
LibroDetalleApiView = LibroDetalleAPIView
ProductosAPIView = LibrosAPIView
ProductoDetalleAPIView = LibroDetalleAPIView

# ============================================================
# ALIAS DE COMPATIBILIDAD CON URLS ANTIGUAS
# ============================================================

login_pagina = login_view
iniciar_sesion = login_view
login_web = login_view

registro_pagina = registro
registrar_usuario = registro
registro_web = registro

cerrar_sesion_web = cerrar_sesion

crear = crear_libro
editar = editar_libro
eliminar = eliminar_libro

TareasApiView = LibrosAPIView
TareaDetalleApiView = LibroDetalleAPIView