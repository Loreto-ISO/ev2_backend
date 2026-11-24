from rest_framework import serializers

from .models import Categoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria

        fields = (
            "id",
            "nombre",
            "slug",
            "activa",
        )

        read_only_fields = (
            "id",
        )


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True,
    )

    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto

        fields = (
            "id",
            "nombre",
            "descripcion",
            "categoria",
            "categoria_nombre",
            "precio",
            "stock",
            "imagen",
            "imagen_url",
            "activo",
            "creado_en",
            "actualizado_en",
        )

        read_only_fields = (
            "id",
            "categoria_nombre",
            "imagen_url",
            "creado_en",
            "actualizado_en",
        )

    def get_imagen_url(self, producto):
        if not producto.imagen:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                producto.imagen.url,
            )

        return producto.imagen.url

    def validate_nombre(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 2 caracteres."
            )

        if len(value) > 120:
            raise serializers.ValidationError(
                "El nombre no puede superar 120 caracteres."
            )

        return value

    def validate_descripcion(self, value):
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "La descripción debe tener al menos 10 caracteres."
            )

        if len(value) > 1000:
            raise serializers.ValidationError(
                "La descripción no puede superar 1000 caracteres."
            )

        return value

    def validate_precio(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El precio debe ser mayor que cero."
            )

        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El stock no puede ser negativo."
            )

        return value