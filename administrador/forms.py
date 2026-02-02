from encargado import models
from django.forms import ModelForm


class EmpleadoForm(ModelForm):
    class Meta:
        model = models.Empleados
        fields = ['nombre', 'apellido', 'dni',
                  'direccion', 'telefono', 'rol_empleado']


class CamionesForm(ModelForm):
    class Meta:
        model = models.Camiones
        fields = ['marca', 'dominio', 'disponibilidad']


class ProveedorForm(ModelForm):
    class Meta:
        model = models.Proveedor
        fields = ['nombre', 'cuit', 'direccion', 'telefono']


class CorteForm(ModelForm):
    class Meta:
        model = models.Cortes
        fields = ['nombre']


class CamaraForm(ModelForm):
    class Meta:
        model = models.Frigorifico
        fields = ['nombre', 'capacidad']
