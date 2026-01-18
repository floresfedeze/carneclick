from django.shortcuts import render
from encargado.models import Camiones, Empleados
from django.http import HttpResponse, HttpResponseRedirect
from .forms import CamionesForm, EmpleadoForm
from carneclick.decorators import group_required
# Create your views here.


@group_required('Encargado')
def empleados(request):
    empleados = Empleados.objects.all()
    return render(request, 'empleados.html', {'empleados': empleados})


@group_required('Encargado')
def camiones(request):
    camiones = Camiones.objects.all()
    return render(request, 'camiones.html', {'camiones': camiones})


@group_required('Encargado')
def entrada_camion(request):
    if request.method == 'POST':
        form = CamionesForm(request.POST)
        if form.is_valid():
            accion = request.POST.get('accion')

            if accion == 'Guardar':
                form.save()
                return HttpResponseRedirect('/administrador/camiones/')
            elif accion == 'Cancelar':
                return HttpResponseRedirect('/administrador/camiones/')
    else:
        form = CamionesForm()  # ← IMPORTANTE

    return render(request, 'html/camiones/entrada_camion.html', {
        'form': form,
    })


@group_required('Encargado')
def editar_camion(request, pk):
    """Editar un camion existente."""
    try:
        camion = Camiones.objects.get(pk=pk)
    except Camiones.DoesNotExist:
        return HttpResponseRedirect('/administrador/camiones/')

    if request.method == 'POST':
        form = CamionesForm(request.POST, instance=camion)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/administrador/camiones/')
    else:
        form = CamionesForm(instance=camion)

    return render(request, 'html/camiones/editar_camion.html', {
        'form': form,
        'camion': camion,
    })


@group_required('Encargado')
def eliminar_camion(request, pk):
    """Confirmar y eliminar un producto."""
    try:
        camion = Camiones.objects.get(pk=pk)
    except Camiones.DoesNotExist:
        return HttpResponseRedirect('/administrador/camiones/')

    if request.method == 'POST':
        camion.delete()
        return HttpResponseRedirect('/administrador/camiones/')

    return render(request, 'html/camiones/confirm_deletee.html', {
        'camion': camion,
    })


def cancelar(request):

    return HttpResponseRedirect('/administrador/empleados/')


@group_required('Encargado')
def entrada_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            accion = request.POST.get('accion')

            if accion == 'Guardar':
                form.save()
                return HttpResponseRedirect('/administrador/empleados/')
            elif accion == 'Cancelar':
                return HttpResponseRedirect('/administrador/empleados/')
    else:
        form = EmpleadoForm()  # ← IMPORTANTE

    return render(request, 'html/empleados/entrada_empleado.html', {
        'form': form,
    })


@group_required('Encargado')
def editar_empleado(request, pk):
    """Editar un empleado existente."""
    try:
        empleado = Empleados.objects.get(pk=pk)
    except Empleados.DoesNotExist:
        return HttpResponseRedirect('/administrador/empleados/')

    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/administrador/empleados/')
    else:
        form = EmpleadoForm(instance=empleado)

    return render(request, 'html/empleados/editar_empleado.html', {
        'form': form,
        'empleado': empleado,
    })


@group_required('Encargado')
def eliminar_empleado(request, pk):
    """Confirmar y eliminar un producto."""
    try:
        empleado = Empleados.objects.get(pk=pk)
    except Empleados.DoesNotExist:
        return HttpResponseRedirect('/administrador/empleados/')

    if request.method == 'POST':
        empleado.delete()
        return HttpResponseRedirect('/administrador/empleados/')

    return render(request, 'html/empleados/confirm_deletee.html', {
        'empleado': empleado,
    })
