from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from carneclick.decorators import group_required
from .forms import ClienteForm, ComercioForm
from encargado.models import Cortes, Productos, Carrito, ItemCarrito, Pedido_cliente, PedidoItem
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
# Create your views here.


@group_required('Cliente')
def home(request):
    return render(request, 'cliente.html')


@group_required('Cliente')
@group_required('Cliente')
def nuevo_pedido(request):
    cortes = Cortes.objects.annotate(
        stock=Count('productos'),
    )

    return render(
        request,
        'cliente/nuevo_pedido.html',
        {'cortes': cortes}
    )


@login_required
def agregar_carrito(request, corte_id):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    corte = get_object_or_404(Cortes, id=corte_id)

    cantidad = int(request.POST.get("cantidad", 1))

    # stock dinámico
    stock = Productos.objects.filter(nombre=corte).count()

    if cantidad > stock:
        return redirect("nuevo_pedido")

    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        corte=corte
    )

    if creado:
        item.cantidad = cantidad
    else:
        if item.cantidad + cantidad > stock:
            item.cantidad = stock
        else:
            item.cantidad += cantidad

    item.save()
    return HttpResponseRedirect("/cliente/carrito/")


def restar_cantidad(request, item_id):
    item = get_object_or_404(
        ItemCarrito,
        id=item_id,
        carrito__usuario=request.user
    )

    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()

    return HttpResponseRedirect("/cliente/carrito/")


@login_required
def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, "cliente/ver_carrito.html", {
        "carrito": carrito
    })


@login_required
def quitar_del_carrito(request, item_id):
    item = get_object_or_404(
        ItemCarrito,
        id=item_id,
        carrito__usuario=request.user
    )
    item.delete()
    return HttpResponseRedirect("/cliente/carrito/")


@login_required
def confirmar_pedido(request):
    carrito = get_object_or_404(
        Carrito, usuario=request.user)

    if not carrito.items.exists():
        return HttpResponseRedirect("/cliente/carrito/")

    pedido = Pedido_cliente.objects.create(
        cliente=request.user, estado='pendiente')

    for item in carrito.items.all():
        PedidoItem.objects.create(
            pedido=pedido,
            corte=item.corte,
            cantidad=item.cantidad
        )

    carrito.items.all().delete()

    return redirect("cliente:pedidos_activos")


@login_required
def pedidos_activos(request):
    pedidos = Pedido_cliente.objects.filter(
        cliente=request.user
    ).exclude(
        estado__in=["finalizado", "cancelado"]
    ).order_by("-fecha")

    return render(request, "cliente/pedidos_activos.html", {
        "pedidos": pedidos
    })


@login_required
def register_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)

        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.user = request.user
            cliente.save()
            messages.success(
                request, f"Registro completado, ahora debe esperar que el encargado lo apruebe.")
            logout(request)
            return redirect("login_view")
    else:
        form = ClienteForm()

    return render(request, "register_cliente.html", {
        "form": form
    })


@login_required
def register_comercio(request):
    if request.method == "POST":
        form = ComercioForm(request.POST)

        if form.is_valid():
            comercio = form.save()
            return redirect("cliente:register_cliente")
    else:
        form = ComercioForm()

    return render(request, "register_comercio.html", {
        "form": form
    })
