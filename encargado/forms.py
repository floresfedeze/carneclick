from . import models
from django.forms import ModelForm
from django import forms


class ProductoForm(ModelForm):
    class Meta:
        model = models.Productos
        fields = ['nombre', 'kilos', 'temperatura', 'frigorificop']


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
        self.fields['chofer'].queryset = models.Empleados.objects.filter(
            disponibilidad__estado='disponible'
        )
        self.fields['ayudante'].queryset = models.Empleados.objects.filter(
            disponibilidad__estado='disponible'
        )
        self.fields['camion_viaje'].queryset = models.Camiones.objects.filter(
            disponibilidad__estado='disponible'
        )


class AgregarPedidoPendienteForm(forms.Form):
    pedido_pendiente = forms.ModelChoiceField(
        queryset=models.Pedido_cliente.objects.filter(estado="pendiente"),
        label="Pedido pendiente",
        required=True,
        help_text="Selecciona un pedido pendiente para convertirlo en pedido del viaje"
    )
