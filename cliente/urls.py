from cliente import views
from django.urls import path


app_name = 'cliente'

urlpatterns = [
    path('', views.home, name='home'),
    path('nuevo_pedido/', views.nuevo_pedido, name='nuevo_pedido'),
    path("carrito/", views.ver_carrito, name="ver_carrito"),
    path("carrito/agregar/<int:corte_id>/",
         views.agregar_carrito, name="agregar_carrito"),
    path("carrito/restar/<int:item_id>/",
         views.restar_cantidad, name="restar_carrito"),
    path("carrito/quitar/<int:item_id>/",
         views.quitar_del_carrito, name="quitar_carrito"),
    path("pedidoconfirmar/", views.confirmar_pedido, name="confirmar_pedido"),
    path("pedidosactivos/", views.pedidos_activos, name="pedidos_activos"),
    path("entregas/", views.entregas, name="entregas"),
    path("pedidospendientes/", views.pedidos_pendientes_cliente,
         name="pedidos_pendientes_cliente"),
    path("pedido/<int:pedido_id>/", views.pedido_detalle, name="pedido_detalle"),
    path("pedido/<int:pedido_id>/entregado/",
         views.pedido_marcar_entregado, name="pedido_marcar_entregado"),
    path("pedido/<int:pedido_id>/problema/",
         views.pedido_reportar_problema, name="pedido_reportar_problema"),
    path('registercliente/', views.register_cliente, name='register_cliente'),
    path("registercomercio/", views.register_comercio, name="register_comercio"),
]
