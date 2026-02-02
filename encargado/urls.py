from encargado import views
from django.urls import path, include


app_name = 'encargado'

urlpatterns = [
    path('', views.home, name='home'),
    path('nuevopedido/', views.nuevo_pedido, name='nuevo_pedido'),
    path('stock/', views.stock, name='stock'),
    path('productos/ver_todos/', views.ver_todos_productos,
         name='ver_todos_productos'),
    path('stock/entrada_stock/', views.entrada_stock, name='entrada_stock'),
    path('stock/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('stock/generar_ticket/<int:pk>/',
         views.generar_ticket_producto, name='generar_ticket_producto'),
    path('stock/ver/<int:pk>/', views.ver_producto, name='ver_producto'),
    path('stock/entrada/<int:entrada_id>/',
         views.entrada_detalle, name='entrada_detalle'),
    path('stock/generar_ticket_entrada/<int:entrada_id>/',
         views.generar_ticket_entrada, name='generar_ticket_entrada'),
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
    path(
        'pedidos/<int:pedido_id>/finalizar/',
        views.finalizar_pedido,
        name='finalizar_pedido'
    ),
    path(
        'pedidos_preparados/',
        views.pedidos_preparados,
        name='pedidos_preparados'
    ),
    path(
        'pedidos_preparados/<int:pedido_id>/detalles/',
        views.detalles_pedido_preparado,
        name='detalles_pedido_preparado'
    ),
    path(
        'pedidos_preparados/<int:pedido_id>/editar/',
        views.editar_pedido_preparado,
        name='editar_pedido_preparado'
    ),
    path(
        'pedidos_preparados/<int:pedido_id>/agregar/',
        views.agregar_producto_preparado,
        name='agregar_producto_preparado'
    ),
    path(
        'pedidos_preparados/item/<int:item_id>/eliminar/',
        views.eliminar_item_preparado,
        name='eliminar_item_preparado'
    ),
    path(
        'pedidos_preparados/<int:pedido_id>/eliminar/',
        views.eliminar_pedido_preparado,
        name='eliminar_pedido_preparado'
    ),
    path(
        'pedidos/nuevo/',
        views.nuevo_pedido_manual,
        name='nuevo_pedido_manual'
    ),
    path(
        'pedidos_entregados/',
        views.pedidos_entregados,
        name='pedidos_entregados'
    ),

    # Viajes
    path('viajes/nuevo/', views.nuevo_viaje, name='nuevo_viaje'),
    path('viajes/activos/', views.viajes_activos, name='viajes_activos'),
    path('viajes/finalizados/', views.viajes_finalizados,
         name='viajes_finalizados'),
    path('viajes/<int:viaje_id>/', views.gestionar_viaje, name='gestionar_viaje'),
    path('viajes/<int:viaje_id>/iniciar/',
         views.iniciar_viaje, name='iniciar_viaje'),
    path('viajes/<int:viaje_id>/agregar_pendiente/',
         views.agregar_pedido_desde_pendiente, name='agregar_pedido_desde_pendiente'),
    path('viajes/<int:viaje_id>/agregar_manual/',
         views.agregar_pedido_manual_a_viaje, name='agregar_pedido_manual_a_viaje'),
    # Reportes
    path('reportes/stock/', views.reporte_stock, name='reporte_stock'),
    path('reportes/pedidos/', views.reporte_pedidos, name='reporte_pedidos'),
    # Consolidado
    path('reportes/consolidado/', views.reporte_consolidado,
         name='reporte_consolidado'),
    path('reportes/por_vencer/', views.reporte_vencimientos,
         name='reporte_vencimientos'),
    path('chart/', views.get_chart, name='get_chart'),
]
