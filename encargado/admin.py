from django.contrib import admin

# Register your models here.
from .models import PedidoItem, Pedido_cliente, Camiones, Rol_empleado, Cliente, Comercio, Tipo_frigorifico, Cortes, Pedido, Productos, DetallePedido, Frigorifico, Viaje, Usuarios, Empleados, Rol, Proveedor, Entrada, Estado
# Register your models here.


class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'corte', 'cantidad')


class Pedido_clienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'estado')


class Rol_empleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


class EntradaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'proveedor')


class CortesAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')


class Tipo_frigorificoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dias')


class ProductosAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'kilos',
                    'fecha_entrada', 'frigorificop', 'temperatura')


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


class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto_id', 'pedido_id')


class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'viaje', 'user_id', 'creado_en', 'total')


class ViajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'chofer', 'ayudante', 'camion_viaje')


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
