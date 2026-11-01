from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Libro(models.Model):
    titulo = models.CharField(max_length=150, verbose_name="Título del Libro")
    autor = models.CharField(max_length=150, verbose_name="Autor")
    precio = models.IntegerField(
        validators=[
            MinValueValidator(1000, message="El precio mínimo es $1.000"),
            MaxValueValidator(150000, message="Un libro no puede costar más de $150.000")
        ]
    )
    stock = models.IntegerField(
        validators=[
            MinValueValidator(0, message="El stock no puede ser negativo"),
            MaxValueValidator(500, message="El límite de bodega es 500 unidades")
        ]
    )

    def __str__(self):
        return f"{self.titulo} - {self.autor}"