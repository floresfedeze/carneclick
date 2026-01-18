from encargado import models
from django.forms import ModelForm
from django import forms


class ClienteForm(ModelForm):
    class Meta:
        model = models.Cliente
        exclude = ["user"]
        fields = ['nombre', 'apellido', 'dni',
                  'direccion', 'telefono', 'comercio']


class ComercioForm(ModelForm):
    class Meta:
        model = models.Comercio
        fields = ['nombre', 'cuit', 'direccion']
