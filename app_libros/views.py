from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Categoria, Producto
from .permissions import SoloAdministradorOModoLectura
from .serializers import ProductoSerializer


# ============================================================
# FUNCIONES AUXILIARES Y DECORADORES
# ============================================================

def es_administrador(usuario):
    """
    Indica si el usuario está autenticado y es administrador.
    """

    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_staff
    )


def administrador_requerido(vista):
    """
    Protege las páginas web de gestión.

    Si el usuario no inició sesión, se envía al login.
    Si está autenticado pero no es administrador,
    se envía al catálogo.
    """

    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Debes iniciar sesión para acceder a la gestión.",
            )
            return redirect("login")

        if not request.user.is_staff:
            messages.error(
                request,
                "No tienes autorización para administrar productos.",
            )
            return redirect("catalogo")

        return vista(request, *args, **kwargs)

    return wrapper


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

    categorias = (
        Categoria.objects
        .filter(activa=True)
        .order_by("nombre")
    )

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
    Catálogo público con búsqueda y filtro por categoría.

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
    categoria_slug = request.GET.get(
        "categoria",
        "",
    ).strip()

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

    categorias = (
        Categoria.objects
        .filter(activa=True)
        .order_by("nombre")
    )

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
    Muestra el detalle público de un producto activo.
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
    Registra únicamente cuentas de clientes.

    Las cuentas administrativas deben crearse mediante
    createsuperuser o desde Django Admin.
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

        if User.objects.filter(
            username__iexact=username,
        ).exists():
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

        errores_password = []

        if len(password) < 8:
            errores_password.append(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if not any(
            caracter.isupper()
            for caracter in password
        ):
            errores_password.append(
                "La contraseña debe incluir una letra mayúscula."
            )

        if not any(
            caracter.islower()
            for caracter in password
        ):
            errores_password.append(
                "La contraseña debe incluir una letra minúscula."
            )

        if not any(
            caracter.isdigit()
            for caracter in password
        ):
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

        usuario_temporal = User(
            username=username,
        )

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

        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.save()

        messages.success(
            request,
            (
                "Tu cuenta fue creada correctamente. "
                "Ya puedes iniciar sesión."
            ),
        )

        return redirect("login")

    return render(
        request,
        "app_libros/registro.html",
    )


# Alias de compatibilidad.
registro_usuario = registro
registro_cliente = registro
registro_pagina = registro
registrar_usuario = registro
registro_web = registro


# ============================================================
# AUTENTICACIÓN WEB
# ============================================================

def login_view(request):
    """
    Inicio de sesión web para clientes y administradores.
    """

    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_panel")

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
                (
                    "El nombre de usuario o la contraseña "
                    "son incorrectos."
                ),
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

        login(
            request,
            usuario,
        )

        messages.success(
            request,
            f"Bienvenido, {usuario.username}.",
        )

        if usuario.is_staff:
            return redirect("admin_panel")

        return redirect("catalogo")

    return render(
        request,
        "app_libros/login_cliente.html",
    )


def cerrar_sesion(request):
    """
    Cierra la sesión web administrada por Django.
    """

    logout(request)

    messages.success(
        request,
        "La sesión fue cerrada correctamente.",
    )

    return redirect("login")


# Alias de compatibilidad.
login_usuario = login_view
login_cliente = login_view
login_pagina = login_view
iniciar_sesion = login_view
login_web = login_view

logout_usuario = cerrar_sesion
cerrar_sesion_web = cerrar_sesion


# ============================================================
# ADMINISTRACIÓN WEB DE PRODUCTOS
# ============================================================

@administrador_requerido
def admin_panel(request):
    """
    Panel principal de gestión para administradores.
    """

    productos = (
        Producto.objects
        .select_related("categoria")
        .order_by("nombre")
    )

    total_productos = productos.count()
    productos_sin_stock = productos.filter(
        stock=0,
    ).count()

    productos_activos = productos.filter(
        activo=True,
    ).count()

    total_categorias = Categoria.objects.count()

    return render(
        request,
        "app_libros/admin_panel.html",
        {
            "productos": productos,
            "total_productos": total_productos,
            "productos_sin_stock": productos_sin_stock,
            "productos_activos": productos_activos,
            "total_categorias": total_categorias,
        },
    )


@administrador_requerido
def crear_libro(request):
    """
    Crea un producto desde la interfaz web.

    Se conserva el nombre crear_libro para mantener
    compatibilidad con las rutas y templates anteriores.
    """

    categorias = (
        Categoria.objects
        .filter(activa=True)
        .order_by("nombre")
    )

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

        if not categoria_id:
            messages.error(
                request,
                "Debes seleccionar una categoría.",
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
            if hasattr(errores, "message_dict"):
                for campo, mensajes_campo in (
                    errores.message_dict.items()
                ):
                    for mensaje in mensajes_campo:
                        messages.error(
                            request,
                            f"{campo}: {mensaje}",
                        )
            else:
                for mensaje in errores.messages:
                    messages.error(request, mensaje)

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

        return redirect("admin_panel")

    return render(
        request,
        "app_libros/crear.html",
        {
            "categorias": categorias,
        },
    )


@administrador_requerido
def editar_libro(request, id):
    """
    Edita un producto desde la interfaz web.
    """

    producto = get_object_or_404(
        Producto,
        id=id,
    )

    categorias = (
        Categoria.objects
        .filter(activa=True)
        .order_by("nombre")
    )

    if request.method == "POST":
        producto.nombre = request.POST.get(
            "nombre",
            request.POST.get(
                "titulo",
                producto.nombre,
            ),
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

        valor_activo = request.POST.get("activo")

        if valor_activo is not None:
            producto.activo = valor_activo in (
                "on",
                "true",
                "1",
            )

        nueva_imagen = request.FILES.get("imagen")

        if nueva_imagen:
            producto.imagen = nueva_imagen

        try:
            producto.full_clean()
            producto.save()

        except ValidationError as errores:
            if hasattr(errores, "message_dict"):
                for campo, mensajes_campo in (
                    errores.message_dict.items()
                ):
                    for mensaje in mensajes_campo:
                        messages.error(
                            request,
                            f"{campo}: {mensaje}",
                        )
            else:
                for mensaje in errores.messages:
                    messages.error(request, mensaje)

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

        return redirect("admin_panel")

    return render(
        request,
        "app_libros/editar.html",
        {
            "producto": producto,
            "libro": producto,
            "categorias": categorias,
        },
    )


@administrador_requerido
def eliminar_libro(request, id):
    """
    Elimina un producto desde la interfaz web.
    """

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

        return redirect("admin_panel")

    return render(
        request,
        "app_libros/eliminar.html",
        {
            "producto": producto,
            "libro": producto,
        },
    )


# Alias para nombres nuevos.
crear_producto = crear_libro
editar_producto = editar_libro
eliminar_producto = eliminar_libro

# Alias de compatibilidad.
crear = crear_libro
editar = editar_libro
eliminar = eliminar_libro


# ============================================================
# API REST DE PRODUCTOS
# ============================================================

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

    @extend_schema(
        summary="Listar productos activos",
        description=(
            "Devuelve todos los productos activos. "
            "Requiere un Access Token JWT válido."
        ),
        responses={
            200: ProductoSerializer(many=True),
            401: OpenApiResponse(
                description=(
                    "Access Token ausente, inválido o vencido."
                ),
            ),
        },
        tags=["Productos"],
    )
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

    @extend_schema(
        summary="Crear producto",
        description=(
            "Crea un producto nuevo. "
            "La operación está reservada para administradores."
        ),
        request=ProductoSerializer,
        responses={
            201: ProductoSerializer,
            400: OpenApiResponse(
                description="Datos inválidos.",
            ),
            401: OpenApiResponse(
                description="Access Token ausente o inválido.",
            ),
            403: OpenApiResponse(
                description=(
                    "El usuario no tiene permiso administrativo."
                ),
            ),
        },
        tags=["Productos"],
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
                    "error": (
                        "Los datos enviados no son válidos."
                    ),
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

    PUT: reemplaza todos los datos editables.

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

    @extend_schema(
        summary="Consultar producto por ID",
        responses={
            200: ProductoSerializer,
            401: OpenApiResponse(
                description="Usuario no autenticado.",
            ),
            404: OpenApiResponse(
                description="Producto inexistente.",
            ),
        },
        tags=["Productos"],
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

    @extend_schema(
        summary="Reemplazar producto",
        description=(
            "Reemplaza los datos editables de un producto. "
            "Solo administradores."
        ),
        request=ProductoSerializer,
        responses={
            200: ProductoSerializer,
            400: OpenApiResponse(
                description="Datos inválidos.",
            ),
            401: OpenApiResponse(
                description="Usuario no autenticado.",
            ),
            403: OpenApiResponse(
                description="Sin permiso administrativo.",
            ),
            404: OpenApiResponse(
                description="Producto inexistente.",
            ),
        },
        tags=["Productos"],
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
                    "error": (
                        "Los datos enviados no son válidos."
                    ),
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
                "mensaje": (
                    "Producto actualizado correctamente."
                ),
                "producto": respuesta.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Actualizar parcialmente un producto",
        description=(
            "Actualiza uno o más campos del producto. "
            "Solo administradores."
        ),
        request=ProductoSerializer,
        responses={
            200: ProductoSerializer,
            400: OpenApiResponse(
                description="Datos inválidos.",
            ),
            401: OpenApiResponse(
                description="Usuario no autenticado.",
            ),
            403: OpenApiResponse(
                description="Sin permiso administrativo.",
            ),
            404: OpenApiResponse(
                description="Producto inexistente.",
            ),
        },
        tags=["Productos"],
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
                    "error": (
                        "Los datos enviados no son válidos."
                    ),
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
                "mensaje": (
                    "Producto actualizado parcialmente."
                ),
                "producto": respuesta.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Eliminar producto",
        description=(
            "Elimina definitivamente un producto. "
            "Solo administradores."
        ),
        responses={
            204: OpenApiResponse(
                description="Producto eliminado.",
            ),
            401: OpenApiResponse(
                description="Usuario no autenticado.",
            ),
            403: OpenApiResponse(
                description="Sin permiso administrativo.",
            ),
            404: OpenApiResponse(
                description="Producto inexistente.",
            ),
        },
        tags=["Productos"],
    )
    def delete(self, request, id):
        producto = self.obtener_producto(id)
        producto.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


# Alias de compatibilidad para las rutas API.
LibrosApiView = LibrosAPIView
LibroDetalleApiView = LibroDetalleAPIView
ProductosAPIView = LibrosAPIView
ProductoDetalleAPIView = LibroDetalleAPIView

TareasApiView = LibrosAPIView
TareaDetalleApiView = LibroDetalleAPIView


# ============================================================
# LOGOUT Y REVOCACIÓN JWT
# ============================================================

class LogoutAPIView(APIView):
    """
    Revoca el Refresh Token mediante la blacklist de SimpleJWT.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        summary="Cerrar sesión JWT",
        description=(
            "Revoca el Refresh Token mediante blacklist. "
            "El Access Token seguirá siendo válido hasta expirar."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "refresh": {
                        "type": "string",
                    },
                },
                "required": [
                    "refresh",
                ],
            },
        },
        responses={
            200: OpenApiResponse(
                description="Refresh Token revocado.",
            ),
            400: OpenApiResponse(
                description=(
                    "Refresh Token ausente, inválido, "
                    "vencido o ya revocado."
                ),
            ),
            401: OpenApiResponse(
                description=(
                    "Access Token ausente, inválido o vencido."
                ),
            ),
        },
        tags=["Autenticación"],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "error": (
                        "Debes enviar el Refresh Token "
                        "en el campo 'refresh'."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:
            return Response(
                {
                    "error": (
                        "El Refresh Token es inválido, "
                        "está vencido o ya fue revocado."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "mensaje": (
                    "Sesión cerrada correctamente."
                ),
            },
            status=status.HTTP_200_OK,
        )
    