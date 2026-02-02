from django.shortcuts import render
from encargado.models import Camiones, Empleados, Estado, Proveedor, Cortes, Frigorifico
from django.http import HttpResponse, HttpResponseRedirect
from .forms import CamionesForm, EmpleadoForm, ProveedorForm, CorteForm, CamaraForm
from carneclick.decorators import group_required
# Create your views here.


@group_required('Encargado')
def empleados(request):
    empleados = Empleados.objects.all()
    return render(request, 'html/empleados/empleados.html', {'empleados': empleados})


@group_required('Encargado')
def camiones(request):
    camiones = Camiones.objects.all()
    return render(request, 'html/camiones/camiones.html', {'camiones': camiones})


@group_required('Encargado')
def entrada_camion(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'Cancelar':
            return HttpResponseRedirect('/administrador/camiones/')
        form = CamionesForm(request.POST)
        if form.is_valid():
            if accion == 'Guardar':
                form.save()
                return HttpResponseRedirect('/administrador/camiones/')
    else:
        form = CamionesForm()

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
        accion = request.POST.get('accion')
        if accion == 'Cancelar':
            return HttpResponseRedirect('/administrador/empleados/')
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            if accion == 'Guardar':
                empleado = form.save(commit=False)
                # Disponibilidad por defecto: Estado id=1 (o crear 'disponible')
                try:
                    estado_defecto = Estado.objects.get(id=1)
                except Estado.DoesNotExist:
                    estado_defecto, _ = Estado.objects.get_or_create(
                        estado='disponible')

                empleado.disponibilidad = estado_defecto
                empleado.save()
                return HttpResponseRedirect('/administrador/empleados/')
    else:
        form = EmpleadoForm()

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


@group_required('Encargado')
def proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'html/proveedores/proveedores.html', {'proveedores': proveedores})


def cancelar_proveedor(request):

    return HttpResponseRedirect('/administrador/proveedores/')


@group_required('Encargado')
def entrada_proveedor(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'Cancelar':
            return HttpResponseRedirect('/administrador/proveedores/')
        form = ProveedorForm(request.POST)
        if form.is_valid():
            if accion == 'Guardar':
                proveedor = form.save(commit=False)
                proveedor.save()
                return HttpResponseRedirect('/administrador/proveedores/')
    else:
        form = ProveedorForm()

    return render(request, 'html/proveedores/entrada_proveedor.html', {
        'form': form,
    })


@group_required('Encargado')
def editar_proveedor(request, pk):
    """Editar un empleado existente."""
    try:
        proveedor = Proveedor.objects.get(pk=pk)
    except Empleados.DoesNotExist:
        return HttpResponseRedirect('/administrador/proveedores/')

    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/administrador/proveedores/')
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'html/proveedores/editar_proveedores.html', {
        'form': form,
        'proveedor': proveedor,
    })


@group_required('Encargado')
def eliminar_proveedor(request, pk):
    """Confirmar y eliminar un proveedor."""
    try:
        proveedor = Proveedor.objects.get(pk=pk)
    except Proveedor.DoesNotExist:
        return HttpResponseRedirect('/administrador/proveedores/')

    if request.method == 'POST':
        proveedor.delete()
        return HttpResponseRedirect('/administrador/proveedores/')

    return render(request, 'html/proveedores/confirm_deletee.html', {
        'proveedor': proveedor,
    })


@group_required('Encargado')
def cortes(request):
    cortes = Cortes.objects.all().order_by('nombre')
    return render(request, 'html/cortes/cortes.html', {'cortes': cortes})


@group_required('Encargado')
def entrada_corte(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'Cancelar':
            return HttpResponseRedirect('/administrador/cortes/')
        form = CorteForm(request.POST)
        if form.is_valid():
            if accion == 'Guardar':
                form.save()
                return HttpResponseRedirect('/administrador/cortes/')
    else:
        form = CorteForm()
    return render(request, 'html/cortes/entrada_corte.html', {'form': form})


@group_required('Encargado')
def camaras(request):
    camaras = Frigorifico.objects.all().order_by('nombre')
    return render(request, 'html/camaras/camaras.html', {'camaras': camaras})


@group_required('Encargado')
def entrada_camara(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'Cancelar':
            return HttpResponseRedirect('/administrador/camaras/')
        form = CamaraForm(request.POST)
        if form.is_valid():
            if accion == 'Guardar':
                form.save()
                return HttpResponseRedirect('/administrador/camaras/')
    else:
        form = CamaraForm()
    return render(request, 'html/camaras/entrada_camara.html', {'form': form})


@group_required('Encargado')
def editar_camara(request, pk):
    try:
        camara = Frigorifico.objects.get(pk=pk)
    except Frigorifico.DoesNotExist:
        return HttpResponseRedirect('/administrador/camaras/')

    if request.method == 'POST':
        form = CamaraForm(request.POST, instance=camara)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/administrador/camaras/')
    else:
        form = CamaraForm(instance=camara)
    return render(request, 'html/camaras/editar_camara.html', {'form': form, 'camara': camara})


@group_required('Encargado')
def eliminar_camara(request, pk):
    try:
        camara = Frigorifico.objects.get(pk=pk)
    except Frigorifico.DoesNotExist:
        return HttpResponseRedirect('/administrador/camaras/')

    if request.method == 'POST':
        camara.delete()
        return HttpResponseRedirect('/administrador/camaras/')
    return render(request, 'html/camaras/confirm_deletee.html', {'camara': camara})


@group_required('Encargado')
def editar_corte(request, pk):
    try:
        corte = Cortes.objects.get(pk=pk)
    except Cortes.DoesNotExist:
        return HttpResponseRedirect('/administrador/cortes/')

    if request.method == 'POST':
        form = CorteForm(request.POST, instance=corte)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/administrador/cortes/')
    else:
        form = CorteForm(instance=corte)
    return render(request, 'html/cortes/editar_corte.html', {'form': form, 'corte': corte})


@group_required('Encargado')
def eliminar_corte(request, pk):
    try:
        corte = Cortes.objects.get(pk=pk)
    except Cortes.DoesNotExist:
        return HttpResponseRedirect('/administrador/cortes/')

    if request.method == 'POST':
        corte.delete()
        return HttpResponseRedirect('/administrador/cortes/')
    return render(request, 'html/cortes/confirm_deletee.html', {'corte': corte})
