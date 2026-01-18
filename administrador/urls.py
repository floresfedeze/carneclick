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
]
