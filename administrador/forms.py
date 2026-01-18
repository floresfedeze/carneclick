from encargado import models
from django.forms import ModelForm


class EmpleadoForm(ModelForm):
    class Meta:
        model = models.Empleados
        fields = ['nombre', 'apellido', 'dni',
                  'direccion', 'telefono', 'disponibilidad']


class CamionesForm(ModelForm):
    class Meta:
        model = models.Camiones
        fields = ['marca', 'dominio', 'disponibilidad']
