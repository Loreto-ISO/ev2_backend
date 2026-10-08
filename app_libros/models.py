from django.db import models
from django.core.validators import MinValueValidator

class Libro(models.Model):
    titulo = models.CharField(max_length=150, verbose_name="Título del Libro")
    autor = models.CharField(max_length=150, verbose_name="Autor")
    precio = models.IntegerField(
        validators=[MinValueValidator(1, message="El precio debe ser mayor a cero")]
    )
    stock = models.IntegerField(
        validators=[MinValueValidator(0, message="El stock no puede ser negativo")]
    )

    def __str__(self):
        return f"{self.titulo} - {self.autor}"
    