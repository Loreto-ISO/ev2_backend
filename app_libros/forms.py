from django import forms

from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto

        fields = (
            "nombre",
            "descripcion",
            "categoria",
            "precio",
            "stock",
            "imagen",
            "activo",
        )

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": 120,
                    "placeholder": "Nombre del producto",
                },
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "maxlength": 1000,
                    "placeholder": "Descripción del producto",
                },
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "form-select",
                },
            ),
            "precio": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "step": 1,
                },
            ),
            "stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": 1,
                },
            ),
            "imagen": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/png,image/jpeg,image/webp",
                },
            ),
            "activo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                },
            ),
        }


# Alias temporal para evitar romper imports antiguos.
LibroForm = ProductoForm