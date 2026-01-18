from encargado import views
from django.urls import path, include


app_name = 'encargado'

urlpatterns = [
    path('', views.home, name='home'),
    path('nuevopedido/', views.nuevo_pedido, name='nuevo_pedido'),
    path('stock/', views.stock, name='stock'),
    path('stock/entrada_stock/', views.entrada_stock, name='entrada_stock'),
    path('stock/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('stock/generar_ticket/<int:pk>/',
         views.generar_ticket_producto, name='generar_ticket_producto'),
    path('stock/eliminar/<int:pk>/',
         views.eliminar_producto, name='eliminar_producto'),
    path('stock/finalizar_entrada/',
         views.finalizar_entrada, name='finalizar_entrada'),
    path('stock/entrada', views.entrada_pruducto, name='entrada'),
    path('pedidos_pendientes/', views.pedidos_pendientes,
         name='pedidos_pendientes'),
    path('clientes_pendientes_e/', views.clientes_pendientes_e,
         name='clientes_pendientes_e'),
    path(
        'clientes/detalles/<int:user_id>/',
        views.ver_detalles_clientes,
        name='ver_detalles_clientes'
    ),
    path('clientes/aprobar/<int:user_id>/',
         views.aprobar_cliente, name='aprobar_cliente'),
    path('clientes/', views.clientes, name='clientes'),
    path(
        'pedidos/iniciar/<int:pedido_pendiente_id>/',
        views.iniciar_pedido,
        name='iniciar_pedido'
    ),

    path(
        'pedidos/<int:pedido_id>/agregar-por-id/',
        views.agregar_producto_por_id,
        name='agregar_producto_por_id'
    ),
    path(
        'pedidos/<int:pedido_id>/cancelar/',
        views.cancelar_pedido,
        name='cancelar_pedido'
    ),
    path(
        'pedidos/item/<int:item_id>/eliminar/',
        views.eliminar_producto_pedido,
        name='eliminar_producto_pedido'
    ),
    path(
        'pedidos/<int:pedido_id>/boleta/',
        views.boleta_pedido,
        name='boleta_pedido'
    ),
]
