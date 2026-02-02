from administrador import views
from django.urls import path
from . import views


app_name = 'administrador'

urlpatterns = [
    path('empleados/', views.empleados, name='empleados'),
    path('empleados/entrada_empleado/',
         views.entrada_empleado, name='entrada_empleado'),
    path('empleados/editar/<int:pk>/',
         views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:pk>/',
         views.eliminar_empleado, name='eliminar_empleado'),
    path('camiones/', views.camiones, name='camiones'),
    path('camiones/entrada_camion/',
         views.entrada_camion, name='entrada_camion'),
    path('camiones/editar/<int:pk>/', views.editar_camion, name='editar_camion'),
    path('camiones/eliminar/<int:pk>/',
         views.eliminar_camion, name='eliminar_camion'),
    path('proveedores/', views.proveedores, name='proveedores'),
    path('proveedores/entrada_proveedor/',
         views.entrada_proveedor, name='entrada_proveedor'),
    path('proveedores/editar/<int:pk>/',
         views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:pk>/',
         views.eliminar_proveedor, name='eliminar_proveedor'),

    # Cortes
    path('cortes/', views.cortes, name='cortes'),
    path('cortes/entrada_corte/', views.entrada_corte, name='entrada_corte'),
    path('cortes/editar/<int:pk>/', views.editar_corte, name='editar_corte'),
    path('cortes/eliminar/<int:pk>/',
         views.eliminar_corte, name='eliminar_corte'),

    # Camaras
    path('camaras/', views.camaras, name='camaras'),
    path('camaras/entrada_camara/', views.entrada_camara, name='entrada_camara'),
    path('camaras/editar/<int:pk>/', views.editar_camara, name='editar_camara'),
    path('camaras/eliminar/<int:pk>/',
         views.eliminar_camara, name='eliminar_camara'),

]
