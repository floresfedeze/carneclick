from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
from .models import PedidoItem, EstadoPedidos, Pedido_cliente, Camiones, Rol_empleado, Cliente, Comercio, Tipo_frigorifico, Cortes, Pedido, Productos, DetallePedido, Frigorifico, Viaje, Usuarios, Empleados, Rol, Proveedor, Entrada, Estado, StockReservation, Lote
# Register your models here.


class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'corte', 'cantidad')


class Pedido_clienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'estado')


class Rol_empleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


class EntradaAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'fecha', 'proveedor')


class CortesAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


class Tipo_frigorificoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dias')


class ProductosAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'codigo', 'nombre', 'kilos', 'reserved_kilos',
                    'fecha_entrada', 'frigorificop', 'temperatura', 'estado')
    list_filter = ('estado', 'frigorificop', 'temperatura', 'nombre')
    search_fields = ('id', 'codigo', 'nombre__nombre')
    readonly_fields = ('reserved_kilos',)


class FrigorificoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'capacidad')


class EmpleadosAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'dni',
                    'direccion', 'telefono', 'disponibilidad', 'rol_empleado')


class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni',
                    'direccion', 'telefono', 'user', 'rol')


class RolAdmin(admin.ModelAdmin):
    list_display = ('id', 'rol')


class CamionesAdmin(admin.ModelAdmin):
    list_display = ('id', 'marca', 'dominio',
                    'disponibilidad')


class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'dni',
                    'direccion', 'telefono', 'comercio', 'user')


class ComercioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'cuit', 'direccion')


class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'cuit', 'direccion', 'telefono')


class DetallePedidoAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'pedido_id', 'producto_id', 'cantidad')
    search_fields = ('pedido_id__id', 'producto_id__nombre')
    list_filter = ('pedido_id', 'producto_id')


class EstadoPedidosAdmin(admin.ModelAdmin):
    list_display = ('id', 'estado')


class PedidoAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'cliente', 'comercio_origen',
                    'observaciones', 'estado', 'creado_en')
    search_fields = ('id', 'cliente__nombre', 'cliente__apellido')
    list_filter = ('estado', 'creado_en')
    readonly_fields = ('id', 'creado_en')


class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'pedido_item',
                    'kilos_reserved', 'created_at', 'expires_at')
    list_filter = ('expires_at', 'producto')
    search_fields = ('producto__id', 'pedido_item__id')


class ViajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'chofer', 'ayudante', 'camion_viaje')


class LoteAdmin(SimpleHistoryAdmin):
    list_display = ('numero_lote', 'producto', 'kilos_disponibles',
                    'fecha_entrada', 'fecha_vencimiento')
    search_fields = ('numero_lote', 'producto__id')
    list_filter = ('fecha_vencimiento',)


class EstadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'estado')


admin.site.register(Cortes, CortesAdmin)
admin.site.register(Tipo_frigorifico, Tipo_frigorificoAdmin)
admin.site.register(Productos, ProductosAdmin)
admin.site.register(Frigorifico, FrigorificoAdmin)
admin.site.register(Pedido, PedidoAdmin)
admin.site.register(Viaje, ViajeAdmin)
admin.site.register(DetallePedido, DetallePedidoAdmin)
admin.site.register(Empleados, EmpleadosAdmin)
admin.site.register(Usuarios, UsuariosAdmin)
admin.site.register(Comercio, ComercioAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Camiones, CamionesAdmin)
admin.site.register(Rol, RolAdmin)
admin.site.register(Proveedor, ProveedorAdmin)
admin.site.register(Entrada, EntradaAdmin)
admin.site.register(Estado, EstadoAdmin)
admin.site.register(Rol_empleado, Rol_empleadoAdmin)
admin.site.register(Pedido_cliente, Pedido_clienteAdmin)
admin.site.register(PedidoItem, PedidoItemAdmin)
admin.site.register(EstadoPedidos, EstadoPedidosAdmin)
admin.site.register(StockReservation, StockReservationAdmin)
admin.site.register(Lote, LoteAdmin)
