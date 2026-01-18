from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import F, Sum, FloatField
from datetime import timedelta
# Create your models here.


class Entrada(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    proveedor = models.ForeignKey(
        'Proveedor', on_delete=models.RESTRICT, default=1)

    def __str__(self):
        return str(self.fecha)


class Rol_empleado(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Tipo_frigorifico(models.Model):
    nombre = models.CharField(max_length=100)
    dias = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class Cortes(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Frigorifico(models.Model):
    nombre = models.CharField(max_length=200)
    capacidad = models.FloatField()

    def __str__(self):
        return self.nombre


class Productos(models.Model):
    nombre = models.ForeignKey(Cortes, on_delete=models.CASCADE)
    kilos = models.FloatField()
    fecha_entrada = models.ForeignKey(Entrada, on_delete=models.RESTRICT)
    temperatura = models.ForeignKey(
        Tipo_frigorifico, on_delete=models.CASCADE, default=1)
    frigorificop = models.ForeignKey(Frigorifico, on_delete=models.RESTRICT)

    def fecha_vencimiento(self):
        fecha = self.fecha_entrada.fecha
        dias = self.temperatura.dias
        return fecha + timedelta(days=dias)


class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    cuit = models.IntegerField()
    direccion = models.CharField(max_length=200)
    telefono = models.IntegerField()

    def __str__(self):
        return self.nombre


class Estado(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
    ]

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='disponible',
    )

    def __str__(self):
        return self.estado


class Empleados(models.Model):
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    dni = models.IntegerField()
    direccion = models.CharField(max_length=200)
    telefono = models.IntegerField()
    disponibilidad = models.ForeignKey(Estado, on_delete=models.PROTECT)
    rol_empleado = models.ForeignKey(
        Rol_empleado, on_delete=models.PROTECT, default=1)


class Rol(models.Model):
    ADMINISTRADOR = 'administrador'
    ENCARGADO = 'encargado'

    ROLES_CHOICES = [
        (ADMINISTRADOR, 'Administrador'),
        (ENCARGADO, 'Encargado'),
    ]

    rol = models.CharField(max_length=20, choices=ROLES_CHOICES)

    def __str__(self):
        return self.rol


class Usuarios(models.Model):
    nombre = models.CharField(max_length=200)
    dni = models.IntegerField()
    direccion = models.CharField(max_length=200)
    telefono = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.nombre


class Camiones(models.Model):
    marca = models.CharField(max_length=200)
    dominio = models.CharField(max_length=7)
    disponibilidad = models.ForeignKey(Estado, on_delete=models.PROTECT)


class Viaje(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    chofer = models.ForeignKey(
        Empleados, on_delete=models.RESTRICT, related_name='viajes_como_chofer')
    ayudante = models.ForeignKey(
        Empleados, on_delete=models.RESTRICT, related_name='viajes_como_ayudante')
    camion_viaje = models.ForeignKey(Camiones, on_delete=models.RESTRICT)


class Comercio(models.Model):
    nombre = models.CharField(max_length=200)
    cuit = models.IntegerField()
    direccion = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    dni = models.IntegerField()
    direccion = models.CharField(max_length=200)
    telefono = models.IntegerField()
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    comercio_origen = models.ForeignKey(
        Comercio, on_delete=models.RESTRICT, null=True,
        blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    viaje = models.ForeignKey(
        Viaje, on_delete=models.RESTRICT, null=True, blank=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    creado_en = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Pedido {self.id} - Cliente: {self.cliente.nombre} {self.cliente.apellido}'

    @property
    def total(self):
        return self.detallepedido_set.aggregate(

            total=models.Sum(F('producto_id__kilos') *
                             F('cantidad'), output_field=FloatField())
        )['total'] or 0

    class Meta:
        db_table = 'pedido'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['id']


class DetallePedido(models.Model):
    producto_id = models.ForeignKey(
        Productos, on_delete=models.CASCADE, default=1)
    pedido_id = models.ForeignKey(Pedido, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f'DetallePedido {self.cantidad} - Pedido: {self.producto_id.nombre}'

    class Meta:
        db_table = 'detallepedido'
        verbose_name = 'Detalle Pedido'
        verbose_name_plural = 'Detalles Pedidos'
        ordering = ['id']


class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    def total_items(self):
        return sum(item.cantidad for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        related_name="items",
        on_delete=models.CASCADE
    )
    corte = models.ForeignKey(
        Cortes,
        on_delete=models.CASCADE, default=1
    )
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.corte.nombre} x {self.cantidad}"


class Pedido_cliente(models.Model):
    ESTADOS = (
        ("pendiente", "Pendiente"),
        ("enviado", "Enviado"),
        ("finalizado", "Finalizado"),
        ("cancelado", "Cancelado"),
    )

    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="activo")

    def total_items(self):
        return sum(item.cantidad for item in self.items.all())

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.username}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(
        Pedido_cliente, related_name="items", on_delete=models.CASCADE)
    corte = models.ForeignKey("Cortes", on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
