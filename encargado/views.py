from django.http import HttpResponse
from datetime import date, datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import Pedido_cliente, Comercio, Productos, Entrada, DetallePedido,  Pedido, Proveedor, Empleados, Carrito, ItemCarrito, Cliente
from .forms import ProductoForm
from django.contrib.auth.models import User, Group
from carneclick.decorators import group_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from datetime import timedelta
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings


@group_required('Encargado')
def home(request):
    return render(request, 'html/encargado.html')


@group_required('Encargado')
def nuevo_pedido(request):
    productos = Productos.objects.all()
    return render(request, 'html/nuevo_pedido.html', {'productos': productos})


def generar_ticket_pdf(producto):
    # Ajusta 'fecha' según tu modelo Entrada
    fecha_entrada = producto.fecha_entrada.fecha

    # Calculamos la fecha de vencimiento sumando los días de temperatura
    dias = producto.temperatura.dias
    fecha_vencimiento = fecha_entrada + timedelta(days=dias)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="ticket_producto.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 3 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(3 * cm, y, "Ticket de Entrada de Stock")
    y -= 1 * cm

    c.setFont("Helvetica", 11)
    c.drawString(3 * cm, y, f"Producto: {producto.nombre}")
    y -= 0.7 * cm
    c.drawString(3 * cm, y, f"Kilos: {producto.kilos}")
    y -= 0.7 * cm
    # Obtener proveedor desde la Entrada (producto.fecha_entrada puede ser instancia o id)
    proveedor_nombre = ''
    try:
        entrada = producto.fecha_entrada
        if entrada and getattr(entrada, 'proveedor', None):
            proveedor_nombre = entrada.proveedor.nombre
    except Exception:
        proveedor_nombre = ''

    c.drawString(3 * cm, y, f"Proveedor: {proveedor_nombre}")
    y -= 0.7 * cm

    c.drawString(3 * cm, y, f"Frigorífico: {producto.frigorificop}")
    y -= 0.7 * cm

    c.drawString(
        3 * cm,
        y,
        f"Fecha de entrada: {producto.fecha_entrada}"
    )
    y -= 0.7 * cm

    c.drawString(
        3 * cm,
        y,
        f"Fecha de vencimiento: {fecha_vencimiento}"
    )
    y -= 1 * cm

    c.line(3 * cm, y, width - 3 * cm, y)

    c.showPage()
    c.save()

    return response


def finalizar_entrada(request):
    entrada_id = request.session.get('entrada_id')

    if entrada_id:
        try:
            entrada_actual = Entrada.objects.get(id=entrada_id)
            # Verificar si esta entrada tiene productos asociados
            productos_agregados = Productos.objects.filter(
                fecha_entrada=entrada_actual)
            if not productos_agregados.exists():
                # Si no hay productos, eliminamos la entrada "fantasma"
                entrada_actual.delete()
        except Entrada.DoesNotExist:
            pass

    # Limpiar la sesión
    request.session.pop('entrada_id', None)

    return HttpResponseRedirect('/encargado/stock/')


@group_required('Encargado')
def stock(request):
    productos = Productos.objects.all()
    return render(request, 'html/productos/stock.html', {'productos': productos})


@group_required('Encargado')
def clientes_pendientes_e(request):
    # Obtenemos solo los usuarios del grupo Cliente_Pendiente
    grupo_pendiente = Group.objects.get(name='Cliente_Pendiente')
    clientes = User.objects.filter(groups=grupo_pendiente)

    return render(request, 'html/clientes/clientes_pendientes.html', {'clientes': clientes})


@group_required('Encargado')
def entrada_pruducto(request):
    entradas = Entrada.objects.all()
    return render(request, 'html/productos/entradas.html', {'entradas': entradas})


@group_required('Encargado')
def generar_ticket_producto(request, pk):
    """Generar ticket PDF para el producto indicado por pk."""
    try:
        producto = Productos.objects.get(pk=pk)
    except Productos.DoesNotExist:
        return HttpResponseRedirect('/encargado/stock/')

    return generar_ticket_pdf(producto)


def entrada_stock(request):
    entrada_id = request.session.get('entrada_id')

    if entrada_id:
        try:
            entrada_actual = Entrada.objects.get(id=entrada_id)
        except Entrada.DoesNotExist:
            entrada_actual = Entrada.objects.create()
            request.session['entrada_id'] = entrada_actual.id
    else:
        entrada_actual = Entrada.objects.create()
        request.session['entrada_id'] = entrada_actual.id

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.fecha_entrada = entrada_actual

            # Si se envió un proveedor para la entrada, guardarlo en la Entrada
            entrada_proveedor_id = request.POST.get('entrada_proveedor')
            if entrada_proveedor_id:
                try:
                    entrada_actual.proveedor_id = int(entrada_proveedor_id)
                    entrada_actual.save()
                except (ValueError, Proveedor.DoesNotExist):
                    pass

            # 🧾 Generar ticket SIN guardar
            if 'ticket' in request.POST:
                return generar_ticket_pdf(producto)

            accion = request.POST.get('accion')

            # ➕ Guardar y seguir
            if accion == 'Agregar otro producto':
                producto.save()
                # 🔹 Guardar valores del último producto
                request.session['ultimo_producto'] = {
                    'nombre': producto.nombre_id,
                    'temperatura': producto.temperatura_id,
                    'frigorificop': producto.frigorificop_id,
                }
                request.session.modified = True
                return HttpResponseRedirect('/encargado/stock/entrada_stock/')

            # ✅ Guardar y terminar
            elif accion == 'Guardar y terminar':
                producto.save()
                # limpiar sesión relacionada con la entrada y último producto
                request.session.pop('entrada_id', None)
                request.session.pop('ultimo_producto', None)
                request.session.modified = True
                return HttpResponseRedirect('/encargado/stock/')

    else:
        initial_data = {'fecha_entrada': entrada_actual}

        ultimo = request.session.get('ultimo_producto')
        if ultimo:
            initial_data.update({
                'nombre': ultimo.get('nombre'),
                'temperatura': ultimo.get('temperatura'),
                'frigorificop': ultimo.get('frigorificop'),
            })
        form = ProductoForm(initial=initial_data)

    productos_agregados = Productos.objects.filter(
        fecha_entrada=entrada_actual
    )
    proveedores = Proveedor.objects.all()

    return render(request, 'html/productos/entrada_stock.html', {
        'form': form,
        'entrada_actual': entrada_actual,
        'productos_agregados': productos_agregados,
        'proveedores': proveedores,
    })


@group_required('Encargado')
def editar_producto(request, pk):
    """Editar un producto existente."""
    try:
        producto = Productos.objects.get(pk=pk)
    except Productos.DoesNotExist:
        return HttpResponseRedirect('/encargado/stock/')

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/encargado/stock/')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'html/productos/editar_producto.html', {
        'form': form,
        'producto': producto,
    })


@group_required('Encargado')
def eliminar_producto(request, pk):
    """Confirmar y eliminar un producto."""
    try:
        producto = Productos.objects.get(pk=pk)
    except Productos.DoesNotExist:
        return HttpResponseRedirect('/encargado/stock/')

    if request.method == 'POST':
        producto.delete()
        return HttpResponseRedirect('/encargado/stock/')

    return render(request, 'html/productos/confirm_delete.html', {
        'producto': producto,
    })


@group_required('Encargado')
def pedidos_pendientes(request):
    pedidos = Pedido_cliente.objects.filter(
        estado="pendiente"
    ).order_by("-fecha")

    return render(request, "html/pedidos/pedidos_pendientes.html", {
        "pedidos": pedidos
    })


@group_required('Encargado')
def ver_detalles_clientes(request, user_id):
    """
    Ver detalles de un cliente específico a partir de su User.
    """
    # Obtenemos el User
    user = get_object_or_404(User, pk=user_id)

    # Obtenemos el Cliente asociado
    cliente = get_object_or_404(Cliente, user=user)

    return render(request, 'html/clientes/detalles_clientes.html', {
        'clientes': cliente,
        'user': user,
    })


@group_required('Encargado')
def aprobar_cliente(request, user_id):
    """
    Aprueba un cliente: cambia su grupo de Cliente_Pendiente a Cliente
    """
    user = get_object_or_404(User, pk=user_id)

    grupo_pendiente = Group.objects.get(name='Cliente_Pendiente')
    grupo_cliente = Group.objects.get(name='Cliente')

    # Cambiamos grupos
    if grupo_pendiente in user.groups.all():
        user.groups.remove(grupo_pendiente)

    user.groups.add(grupo_cliente)
    user.save()

    # 📧 Enviar email (si tiene email)
    if user.email:
        try:
            send_mail(
                subject='Tu cuenta ha sido aprobada',
                message=(
                    f"Hola {user.username},\n\n"
                    "Nos complace informarte que tu cuenta ha sido aprobada.\n"
                    "Ya puedes iniciar sesión y utilizar el sistema.\n\n"
                    "Saludos,\n"
                    "El equipo de soporte de Carneclick"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            messages.warning(
                request,
                f"El usuario {user.username} fue aprobado, pero no se pudo enviar el correo."
            )

    # Mensaje principal
    messages.success(
        request,
        f"El usuario {user.username} ha sido aprobado correctamente."
    )

    return redirect('encargado:clientes_pendientes_e')


@group_required('Encargado')
def clientes(request):
    grupo_actuales = Group.objects.get(name='Cliente')
    clientes = User.objects.filter(groups=grupo_actuales)

    return render(request, 'html/clientes/abm_clientes.html', {'clientes': clientes})


@group_required('Encargado')
def iniciar_pedido(request, pedido_pendiente_id):
    request.session['pedido_pendiente_id'] = pedido_pendiente_id

    pedido_pendiente = get_object_or_404(
        Pedido_cliente,
        id=pedido_pendiente_id
    )

    cliente = get_object_or_404(
        Cliente,
        user=pedido_pendiente.cliente
    )

    pedido, creado = Pedido.objects.get_or_create(
        cliente=cliente,
        user_id=request.user
    )
    comercios = Comercio.objects.all()

    return render(request, 'html/pedidos/iniciar_pedido.html', {
        'pedido': pedido,
        'cliente': cliente,
        'comercios': comercios,
    })


@group_required('Encargado')
def agregar_producto_por_id(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    pedido_pendiente_id = request.session.get('pedido_pendiente_id')

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')

        try:
            producto = Productos.objects.get(id=producto_id)
        except Productos.DoesNotExist:
            messages.error(request, '❌ Producto no encontrado')
            return redirect(
                'encargado:iniciar_pedido',
                pedido_pendiente_id=pedido_pendiente_id
            )

        # 🚫 VALIDACIÓN: no duplicar producto
        existe = DetallePedido.objects.filter(
            pedido_id=pedido,
            producto_id=producto
        ).exists()

        if existe:
            messages.warning(
                request,
                '⚠️ Este producto ya fue agregado al pedido'
            )
            return redirect(
                'encargado:iniciar_pedido',
                pedido_pendiente_id=pedido_pendiente_id
            )

        # ✅ Crear detalle
        DetallePedido.objects.create(
            pedido_id=pedido,
            producto_id=producto,
        )

    return redirect(
        'encargado:iniciar_pedido',
        pedido_pendiente_id=pedido_pendiente_id
    )


@group_required('Encargado')
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Eliminar pedido real (borra DetallePedido por CASCADE)
    pedido.delete()

    # Limpiar sesión
    request.session.pop('pedido_pendiente_id', None)

    messages.warning(request, '🚫 Pedido cancelado correctamente')

    return redirect('encargado:pedidos_pendientes')


@group_required('Encargado')
def eliminar_producto_pedido(request, item_id):
    item = get_object_or_404(DetallePedido, id=item_id)

    pedido = item.pedido_id

    item.delete()

    messages.success(request, '🗑️ Producto eliminado del pedido')

    pedido_pendiente_id = request.session.get('pedido_pendiente_id')

    return redirect(
        'encargado:iniciar_pedido',
        pedido_pendiente_id=pedido_pendiente_id
    )


@group_required('Encargado')
def boleta_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="remito_pedido_{pedido.id}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = []

    # 🟦 ENCABEZADO
    elements.append(Paragraph(
        "<b>DOCUMENTO NO VÁLIDO COMO FACTURA</b>",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 10))

    comercio_origen = (
        pedido.comercio_origen.nombre
        if pedido.comercio_origen else "No especificado"
    )

    elements.append(Paragraph(
        f"<b>Sucursal origen:</b> {comercio_origen}",
        styles["Normal"]
    ))

    elements.append(Paragraph(
        f"<b>Sucursal destino:</b> "
        f"{pedido.cliente.comercio.nombre}",
        styles["Normal"]
    ))

    elements.append(Paragraph(
        f"<b>Observaciones:</b> {pedido.cliente.nombre}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"<b>REMITO Nº:</b> R{pedido.id:04d} &nbsp;&nbsp;"
        f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 15))

    # 🟦 TABLA DE PRODUCTOS
    data = [
        ["Código", "Descripción", "Kilos", "Cantidad"]
    ]

    for item in pedido.detallepedido_set.all():
        data.append([
            item.producto_id.id,
            str(item.producto_id.nombre),
            f"{item.producto_id.kilos:.2f}",
        ])

    table = Table(data, colWidths=[60, 250, 80, 80])

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 40))

    # ----------------- FIRMAS -----------------
    firmas = Table([
        ["__________________________", "__________________________"],
        ["Firma entrega", "Firma recibe"]
    ], colWidths=[250, 250])

    firmas.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elements.append(firmas)
    elements.append(Spacer(1, 30))

    doc.build(elements)
    return response
