from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.db.models import F, Sum, FloatField
from datetime import timedelta
# Create your models here.


class Entrada(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    proveedor = models.ForeignKey(
        'Proveedor', on_delete=models.RESTRICT, null=True, blank=True)
    numero_lote = models.CharField(
        max_length=30, unique=True, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.fecha)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        # Generar número de lote único basado en ID si no existe
        if (creating and not self.numero_lote) or (not self.numero_lote):
            self.numero_lote = f"L{self.id:06d}"
            super().save(update_fields=['numero_lote'])


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
    ESTADOS = [
        ('en stock', 'En stock'),
        ('preparado', 'preparado'),
        ('de viaje', 'De viaje'),
        ('entregado', 'Entregado'),
    ]
    nombre = models.ForeignKey(Cortes, on_delete=models.CASCADE)
    kilos = models.FloatField()
    # Kilos reservados temporalmente para pedidos pendientes
    reserved_kilos = models.FloatField(default=0)
    # Código legible para identificación en pedidos y tickets
    codigo = models.CharField(
        max_length=20, unique=True, blank=True, null=True)
    fecha_entrada = models.ForeignKey(Entrada, on_delete=models.RESTRICT)
    temperatura = models.ForeignKey(
        Tipo_frigorifico, on_delete=models.CASCADE, default=1)
    frigorificop = models.ForeignKey(Frigorifico, on_delete=models.RESTRICT)
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='en stock'
    )
    history = HistoricalRecords()

    def fecha_vencimiento(self):
        fecha = self.fecha_entrada.fecha
        dias = self.temperatura.dias
        return fecha + timedelta(days=dias)

    def __str__(self):
        return f' {self.id} - {self.nombre} {self.kilos}kg'

    def available_kilos(self):
        try:
            return max(0.0, float(self.kilos or 0) - float(self.reserved_kilos or 0))
        except Exception:
            return float(self.kilos or 0)


class StockReservation(models.Model):
    """Reserva de kilos de un producto para un `PedidoItem`.
    Se usa para evitar sobreventa cuando hay pedidos pendientes.
    """
    producto = models.ForeignKey(
        Productos, on_delete=models.CASCADE, related_name='reservations')
    pedido_item = models.ForeignKey(
        'PedidoItem', on_delete=models.CASCADE, related_name='reservations')
    kilos_reserved = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'Reserva {self.kilos_reserved}kg en Prod#{self.producto_id} para Item#{self.pedido_item_id}'


class Lote(models.Model):
    """Control de lotes por producto con FIFO según vencimiento."""
    producto = models.OneToOneField(
        Productos, on_delete=models.CASCADE, related_name='lote')
    numero_lote = models.CharField(max_length=30, unique=True)
    fecha_entrada = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField()
    kilos_disponibles = models.FloatField(default=0)
    history = HistoricalRecords()

    def __str__(self):
        return f'Lote {self.numero_lote} Prod#{self.producto_id}'

    def recalculate(self):
        try:
            self.fecha_entrada = self.producto.fecha_entrada.fecha
        except Exception:
            self.fecha_entrada = timezone.now()
        try:
            self.fecha_vencimiento = self.producto.fecha_vencimiento()
        except Exception:
            self.fecha_vencimiento = self.fecha_entrada
        self.kilos_disponibles = float(self.producto.available_kilos())
        self.save()


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

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.rol_empleado.nombre}"


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

    def __str__(self):
        return f"{self.marca} - {self.dominio}"


class Viaje(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    chofer = models.ForeignKey(
        Empleados, on_delete=models.RESTRICT, related_name='viajes_como_chofer')
    ayudante = models.ForeignKey(
        Empleados, on_delete=models.RESTRICT, related_name='viajes_como_ayudante')
    camion_viaje = models.ForeignKey(Camiones, on_delete=models.RESTRICT)
    ESTADOS = [
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo')


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
        return self.comercio.nombre


class EstadoPedidos(models.Model):
    ESTADOS = [
        ('preparado', 'Preparado'),
        ('activo', 'Activo'),
        ('entregado', 'Entregado')
    ]

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='preparado',
    )

    def __str__(self):
        return self.estado


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


class Pedido(models.Model):
    comercio_origen = models.ForeignKey(
        Comercio, on_delete=models.RESTRICT, null=True,
        blank=True)
    observaciones = models.CharField(max_length=100, null=True, blank=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.RESTRICT)
    pedido_pendiente = models.OneToOneField(
        Pedido_cliente,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    viaje = models.ForeignKey(
        Viaje, on_delete=models.RESTRICT, null=True, blank=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    creado_en = models.DateTimeField(default=timezone.now)
    estado = models.ForeignKey(
        EstadoPedidos, on_delete=models.CASCADE, default=1)
    history = HistoricalRecords()

    def __str__(self):
        return f'Pedido {self.id} - Cliente: {self.cliente.comercio.nombre}'

    class Meta:
        db_table = 'pedido'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['id']


class DetallePedido(models.Model):
    producto_id = models.ForeignKey(
        Productos, on_delete=models.CASCADE, default=1)
    pedido_id = models.ForeignKey(Pedido, on_delete=models.CASCADE, default=1)
    cantidad = models.PositiveIntegerField(default=1)
    history = HistoricalRecords()

    def __str__(self):
        return f'DetallePedido {self.cantidad} - Pedido: {self.producto_id.nombre}'

    class Meta:
        db_table = 'detallepedido'
        verbose_name = 'Detalle Pedido'
        verbose_name_plural = 'Detalles Pedidos'
        ordering = ['id']


class IncidenteEntrega(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    mensaje = models.TextField()
    creado_en = models.DateTimeField(default=timezone.now)
    atendido = models.BooleanField(default=False)

    def __str__(self):
        return f"Incidente #{self.id} - Pedido {self.pedido.id}"


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


class PedidoItem(models.Model):
    pedido = models.ForeignKey(
        Pedido_cliente, related_name="items", on_delete=models.CASCADE)
    corte = models.ForeignKey("Cortes", on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"Item {self.id} - {self.corte.nombre} x {self.cantidad}kg"


# =====================
# Utilidades de reservas de stock
# =====================


def reserve_stock_for_item(pedido_item):
    """Reserva `pedido_item.cantidad` kilos del corte indicado.
    Devuelve True si se pudo reservar completamente, False si parcial.
    """
    remaining = float(pedido_item.cantidad)
    # Ordenar por fecha de vencimiento más próxima para rotación
    productos_qs = (Productos.objects
                    .filter(estado='en stock', nombre=pedido_item.corte)
                    .select_related('fecha_entrada', 'temperatura', 'lote')
                    .order_by('lote__fecha_vencimiento', 'fecha_entrada__fecha'))
    with transaction.atomic():
        # Nota: en SQLite `select_for_update()` es ignorado; sigue siendo válido para otros motores.
        productos_lock = productos_qs.select_for_update()
        for p in productos_lock:
            available = float(p.kilos) - float(p.reserved_kilos or 0)
            if available <= 0:
                continue
            to_take = min(available, remaining)
            if to_take <= 0:
                break
            StockReservation.objects.create(
                producto=p,
                pedido_item=pedido_item,
                kilos_reserved=to_take,
                # Expira opcionalmente en 48 horas
                expires_at=timezone.now() + timedelta(hours=48)
            )
            p.reserved_kilos = float(p.reserved_kilos or 0) + to_take
            p.save(update_fields=['reserved_kilos'])
            # Actualizar lote si existe
            try:
                if hasattr(p, 'lote') and p.lote:
                    p.lote.kilos_disponibles = float(p.available_kilos())
                    p.lote.save(update_fields=['kilos_disponibles'])
            except Exception:
                pass
            remaining -= to_take
            if remaining <= 0:
                break
    return remaining <= 0


def release_reservations_for_item(pedido_item):
    """Libera las reservas asociadas a un `PedidoItem`."""
    with transaction.atomic():
        reservas = (StockReservation.objects
                    .filter(pedido_item=pedido_item)
                    .select_related('producto'))
        for r in reservas:
            p = r.producto
            p.reserved_kilos = max(0.0, float(
                p.reserved_kilos or 0) - float(r.kilos_reserved or 0))
            p.save(update_fields=['reserved_kilos'])
            try:
                if hasattr(p, 'lote') and p.lote:
                    p.lote.kilos_disponibles = float(p.available_kilos())
                    p.lote.save(update_fields=['kilos_disponibles'])
            except Exception:
                pass
        reservas.delete()


def purge_expired_reservations(now=None):
    """Elimina reservas vencidas y ajusta `reserved_kilos`.
    Retorna cantidad de reservas purgadas.
    """
    now = now or timezone.now()
    to_purge = (StockReservation.objects
                .filter(expires_at__isnull=False, expires_at__lte=now)
                .select_related('producto'))
    count = 0
    with transaction.atomic():
        for r in to_purge:
            p = r.producto
            p.reserved_kilos = max(0.0, float(
                p.reserved_kilos or 0) - float(r.kilos_reserved or 0))
            p.save(update_fields=['reserved_kilos'])
            r.delete()
            count += 1
    return count


# =====================
# Señales: reservar/liberar automáticamente
# =====================


@receiver(post_save, sender=PedidoItem)
def handle_pedido_item_saved(sender, instance, created, **kwargs):
    # Recalcular reservas: liberar anteriores y volver a reservar según cantidad actual
    release_reservations_for_item(instance)
    reserve_stock_for_item(instance)


@receiver(post_delete, sender=PedidoItem)
def handle_pedido_item_deleted(sender, instance, **kwargs):
    # Al eliminar el item, liberar sus reservas
    release_reservations_for_item(instance)


@receiver(post_save, sender=Productos)
def ensure_lote_for_producto(sender, instance, created, **kwargs):
    """Asegura que cada producto tenga un lote con datos sincronizados."""
    try:
        # Generar código si no existe (formato P000001)
        if not instance.codigo:
            code = f"P{instance.id:06d}"
            # update() evita disparar señales de nuevo
            Productos.objects.filter(id=instance.id).update(codigo=code)
        # Ya no se crea un Lote por producto. El número de lote vive en la Entrada.
    except Exception:
        pass
