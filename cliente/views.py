from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from carneclick.decorators import group_required
from .forms import ClienteForm, ComercioForm
from encargado.models import Cortes, Productos, Carrito, ItemCarrito, Pedido_cliente, PedidoItem, Pedido, Cliente, EstadoPedidos, IncidenteEntrega, Viaje
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
# Create your views here.


@group_required('Cliente')
def home(request):
    # Métricas del cliente
    carrito = None
    try:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    except Exception:
        pass

    # Perfil cliente
    cliente = Cliente.objects.filter(user=request.user).first()

    # Contadores Pedido_cliente (pendientes)
    pendientes_count = Pedido_cliente.objects.filter(
        cliente_id=request.user.id,
        estado='pendiente'
    ).count()
    pendientes_ultimos = Pedido_cliente.objects.filter(
        cliente_id=request.user.id,
        estado='pendiente'
    ).order_by('-fecha')[:5]

    # Contadores Pedido (logística)
    activos_count = 0
    entregas_count = 0
    activos_ultimos = []
    if cliente:
        activos_qs = Pedido.objects.filter(
            cliente=cliente,
            estado__estado='activo'
        ).order_by('-creado_en')
        activos_count = activos_qs.count()
        activos_ultimos = activos_qs[:5]

        entregas_count = Pedido.objects.filter(
            cliente=cliente,
            estado__estado='entregado'
        ).count()

    return render(request, 'cliente/home.html', {
        'carrito': carrito,
        'pendientes_count': pendientes_count,
        'pendientes_ultimos': pendientes_ultimos,
        'activos_count': activos_count,
        'activos_ultimos': activos_ultimos,
        'entregas_count': entregas_count,
    })


@group_required('Cliente')
@group_required('Cliente')
def nuevo_pedido(request):
    cortes = Cortes.objects.annotate(
        stock=Count('productos'),
    )

    # Asegurar que el template tenga el `carrito` para mostrar la insignia en la navbar
    carrito = None
    try:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    except Exception:
        pass

    return render(
        request,
        'cliente/nuevo_pedido.html',
        {
            'cortes': cortes,
            'carrito': carrito,
        }
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
    return HttpResponseRedirect("/cliente/nuevo_pedido/")


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
    # Pedidos del sistema de logística (encargado.Pedido) en estado 'activo'
    cliente = Cliente.objects.filter(user=request.user).first()
    pedidos = []
    if cliente:
        pedidos = Pedido.objects.filter(
            cliente=cliente,
            estado__estado='activo'
        ).order_by('-creado_en')

    return render(request, "cliente/pedidos_activos.html", {
        "pedidos": pedidos
    })


@login_required
def entregas(request):
    """Lista pedidos entregados para el cliente logueado."""
    cliente = Cliente.objects.filter(user=request.user).first()
    pedidos = []
    if cliente:
        pedidos = Pedido.objects.filter(
            cliente=cliente,
            estado__estado='entregado'
        ).order_by('-creado_en')

    return render(request, 'cliente/entregas.html', {
        'pedidos': pedidos
    })


@login_required
def pedidos_pendientes_cliente(request):
    """Pedidos pendientes del cliente (tabla Pedido_cliente)."""
    pedidos = Pedido_cliente.objects.filter(
        cliente_id=request.user.id,
        estado='pendiente'
    ).order_by('-fecha')

    return render(request, 'cliente/pedidos_pendientes.html', {
        'pedidos': pedidos
    })


@login_required
def pedido_detalle(request, pedido_id):
    """Detalle de un Pedido (encargado.Pedido) del cliente logueado."""
    cliente = Cliente.objects.filter(user=request.user).first()
    if not cliente:
        return redirect('cliente:pedidos_activos')

    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    detalles = pedido.detallepedido_set.select_related(
        'producto_id', 'producto_id__nombre', 'producto_id__frigorificop'
    )
    total_items = detalles.count()
    total_kilos = sum(getattr(d.producto_id, 'kilos', 0) for d in detalles)

    return render(request, 'cliente/pedido_detalle.html', {
        'pedido': pedido,
        'detalles': detalles,
        'total_items': total_items,
        'total_kilos': total_kilos,
    })


@login_required
def pedido_marcar_entregado(request, pedido_id):
    """Marca como entregado un Pedido del cliente logueado."""
    if request.method != 'POST':
        return redirect('cliente:pedidos_activos')

    cliente = Cliente.objects.filter(user=request.user).first()
    if not cliente:
        return redirect('cliente:pedidos_activos')

    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    estado_entregado, _ = EstadoPedidos.objects.get_or_create(
        estado='entregado')
    pedido.estado = estado_entregado
    pedido.save(update_fields=['estado'])

    # Marcar todos los productos del pedido como "entregado"
    detalles = pedido.detallepedido_set.select_related('producto_id').all()
    for det in detalles:
        prod = det.producto_id
        if prod and prod.estado != 'entregado':
            prod.estado = 'entregado'
            prod.save(update_fields=['estado'])

    # Finalizar viaje si existe
    if pedido.viaje_id:
        Viaje.objects.filter(id=pedido.viaje_id).update(estado='finalizado')

    messages.success(
        request, f"El pedido #{pedido.id} fue marcado como entregado.")
    return redirect('cliente:entregas')


@login_required
def pedido_reportar_problema(request, pedido_id):
    cliente = Cliente.objects.filter(user=request.user).first()
    if not cliente:
        return redirect('cliente:pedidos_activos')

    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)

    if request.method == 'POST':
        mensaje = request.POST.get('mensaje', '').strip()
        if not mensaje:
            messages.error(request, 'Por favor ingrese un mensaje.')
            return redirect('cliente:pedido_reportar_problema', pedido_id=pedido.id)
        IncidenteEntrega.objects.create(
            pedido=pedido,
            cliente=cliente,
            mensaje=mensaje,
        )
        messages.success(request, 'Tu mensaje fue enviado al encargado.')
        return redirect('cliente:pedidos_activos')

    return render(request, 'cliente/pedido_reportar.html', {
        'pedido': pedido,
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
