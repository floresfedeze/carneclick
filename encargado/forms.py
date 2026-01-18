from . import models
from django.forms import ModelForm


class ProductoForm(ModelForm):
    class Meta:
        model = models.Productos
        fields = ['nombre', 'kilos', 'temperatura', 'frigorificop']
