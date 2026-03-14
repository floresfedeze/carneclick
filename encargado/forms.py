from . import models
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User


class ProductoForm(ModelForm):
    class Meta:
        model = models.Productos
        fields = ['nombre', 'kilos', 'cantidad', 'temperatura', 'frigorificop']


class PedidoForm(forms.ModelForm):
    class Meta:
        model = models.Pedido
        fields = ['comercio_origen', 'observaciones', 'cliente',
                  'viaje', 'user_id', 'creado_en', 'estado']


class AgregarProductoForm(forms.Form):
    producto_id = forms.IntegerField(
        label="ID del producto",
    )


class PedidoEditForm(forms.ModelForm):
    class Meta:
        model = models.Pedido
        fields = ['comercio_origen', 'observaciones']


class PedidoNuevoForm(forms.ModelForm):
    class Meta:
        model = models.Pedido
        fields = ['cliente', 'comercio_origen', 'observaciones']


class ViajeForm(forms.ModelForm):
    class Meta:
        model = models.Viaje
        fields = ['chofer', 'ayudante', 'camion_viaje']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar empleados y camiones disponibles
        # `chofer` debe listar solo empleados cuyo rol sea chofer y disponibles
        self.fields['chofer'].queryset = models.Empleados.objects.filter(
            disponibilidad__estado='disponible',
            rol_empleado__nombre__icontains='chofer'
        )
        # `ayudante` listar todos los empleados (sin filtrar por rol)
        self.fields['ayudante'].queryset = models.Empleados.objects.all()
        self.fields['camion_viaje'].queryset = models.Camiones.objects.filter(
            disponibilidad__estado='disponible'
        )


class AgregarPedidoPendienteForm(forms.Form):
    pedido_pendiente = forms.ModelChoiceField(
        queryset=models.Pedido.objects.filter(estado__estado='preparado'),
        label="Pedido preparado",
        required=True,
        help_text="Selecciona un pedido preparado para agregarlo al viaje"
    )


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
