from django.db.models import Max
from datetime import timedelta, datetime
from django.http import HttpResponse
from reportlab.lib.pagesizes import portrait
from .forms import ViajeForm, AgregarPedidoPendienteForm
from django.http import HttpResponse, JsonResponse
from datetime import date, datetime
from django.utils import timezone
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
from django.db import transaction
from django.db.models import Case, When, IntegerField, Q, Count, Sum, Max
from .models import (
    Pedido_cliente,
    Comercio,
    Productos,
    Entrada,
    DetallePedido,
    Pedido,
    Proveedor,
    Empleados,
    Carrito,
    ItemCarrito,
    Cliente,
    Viaje,
    Cortes,
    Frigorifico,
    Camiones,
    purge_expired_reservations,
    IncidenteEntrega,
    IncidenteEntregaItem,
)
from .forms import ProductoForm, PedidoForm, AgregarProductoForm, PedidoEditForm, PedidoNuevoForm, PerfilForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from carneclick.decorators import group_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from datetime import timedelta
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django import forms
import time


@group_required('Encargado')
def notifications_json(request):
    """Devuelve conteos de notificaciones importantes en JSON."""
    from django.urls import reverse
    # Clientes pendientes
    try:
        grupo_pendiente = Group.objects.get(name='Cliente_Pendiente')
        n_clientes = User.objects.filter(groups=grupo_pendiente).count()
    except Group.DoesNotExist:
        n_clientes = 0

    # Pedidos pendientes de clientes
    n_pedidos = Pedido_cliente.objects.filter(estado='pendiente').count()

    # Productos por vencer en los próximos 3 días
    ahora = timezone.now()
    candidatos = Productos.objects.filter(estado__in=['en stock', 'preparado'])
    por_vencer = 0
    for p in candidatos:
        try:
            venc = p.fecha_vencimiento()
            if ahora <= venc <= ahora + timedelta(days=3):
                por_vencer += 1
        except Exception:
            continue

    # Viajes activos
    n_viajes = Viaje.objects.filter(
        pedido__estado__estado='activo').distinct().count()

    total = n_clientes + n_pedidos + por_vencer

    return JsonResponse({
        'total': total,
        'items': [
            {
                'label': 'Clientes pendientes',
                'count': n_clientes,
                'url': reverse('encargado:clientes_pendientes_e'),
                'icon': 'bi-person-exclamation',
                'color': 'warning',
            },
            {
                'label': 'Pedidos pendientes',
                'count': n_pedidos,
                'url': reverse('encargado:pedidos_pendientes'),
                'icon': 'bi-clock-history',
                'color': 'danger',
            },
            {
                'label': 'Productos por vencer (3 días)',
                'count': por_vencer,
                'url': reverse('encargado:reporte_vencimientos'),
                'icon': 'bi-calendar-x',
                'color': 'warning',
            },
            {
                'label': 'Viajes activos',
                'count': n_viajes,
                'url': reverse('encargado:viajes_activos'),
                'icon': 'bi-truck',
                'color': 'success',
            },
        ]
    })


@group_required('Encargado')
def home(request):
    # Limpia reservas vencidas de manera oportunista
    try:
        purged = purge_expired_reservations()
    except Exception:
        purged = 0
    # KPIs
    pendientes_clientes = Pedido_cliente.objects.filter(
        estado='pendiente').count()
    pedidos_activos = Pedido.objects.filter(estado__estado='activo').count()
    viajes_activos = Viaje.objects.filter(
        pedido__estado__estado='activo').distinct().count()
    # Kilos disponibles (en stock menos reservados)
    agg = Productos.objects.filter(estado='en stock').aggregate(
        total_kilos=Sum('kilos'), total_reservados=Sum('reserved_kilos'))
    stock_kg = (agg.get('total_kilos') or 0) - \
        (agg.get('total_reservados') or 0)

    # Vencimientos próximos (por defecto 3 días)
    from datetime import timedelta
    dias = int(request.GET.get('vencen_en', 3))
    ahora = timezone.now()
    candidatos = Productos.objects.filter(estado__in=['en stock', 'preparado']).select_related(
        'fecha_entrada', 'temperatura', 'nombre')
    por_vencer_lista = []
    for p in candidatos:
        try:
            venc = p.fecha_vencimiento()
            if ahora <= venc <= ahora + timedelta(days=dias):
                por_vencer_lista.append((p, venc))
        except Exception:
            continue
    por_vencer_lista.sort(key=lambda t: t[1])
    por_vencer_count = len(por_vencer_lista)
    por_vencer_top = por_vencer_lista[:5]

    # Gráfico: pedidos por estado (global)
    pedidos_por_estado = (Pedido.objects.values('estado__estado')
                          .annotate(cant=Count('id'))
                          .order_by('estado__estado'))

    # Gráfico: stock por corte (solo en stock)
    stock_por_corte = (Productos.objects.filter(estado='en stock')
                       .values('nombre__nombre')
                       .annotate(kilos=Sum('kilos'))
                       .order_by('nombre__nombre'))

    # Gráfico: ocupación por cámara (capacidad en productos vs ocupados)
    frigos = Frigorifico.objects.all().order_by('nombre')
    ocupacion = (Productos.objects.filter(estado='en stock')
                 .values('frigorificop_id', 'frigorificop__nombre')
                 .annotate(kilos=Sum('kilos'), productos=Count('id')))
    occ_by_id = {o['frigorificop_id']: o for o in ocupacion}
    home_frigo_resumen = []
    for f in frigos:
        occ = occ_by_id.get(f.id, {'kilos': 0, 'productos': 0})
        productos_count = int(occ.get('productos') or 0)
        capacidad = float(getattr(f, 'capacidad', 0)
                          or 0)  # capacidad en productos
        ocupacion_pct = (productos_count / capacidad *
                         100.0) if capacidad > 0 else 0.0
        restante_prod = max(capacidad - productos_count, 0)
        home_frigo_resumen.append({
            'nombre': f.nombre,
            'capacidad': int(capacidad),
            'productos': productos_count,
            'restante': int(restante_prod),
        })

    # Gráfico: vencimientos por fecha (conteo)
    from collections import Counter
    venc_por_fecha = Counter([v.date() for _, v in por_vencer_lista])
    venc_fechas = [{'fecha': k, 'cant': v}
                   for k, v in sorted(venc_por_fecha.items())]

    # Gráfico: pedidos por fecha de viaje (conteo por día)
    pedidos_por_viaje_fecha = (Pedido.objects.exclude(viaje__isnull=True)
                               .values('viaje__fecha__date')
                               .annotate(cant=Count('id'))
                               .order_by('viaje__fecha__date'))

    # Últimos movimientos
    ult_pedidos_preparados = Pedido.objects.filter(estado__estado='preparado').select_related(
        'cliente__comercio').order_by('-creado_en')[:5]
    ult_pedidos_entregados = Pedido.objects.filter(estado__estado='entregado').select_related(
        'cliente__comercio').order_by('-creado_en')[:5]

    # Incidentes recientes y pendientes
    try:
        incidentes_no_atendidos = IncidenteEntrega.objects.filter(
            atendido=False).count()
        ult_incidentes = IncidenteEntrega.objects.select_related(
            'pedido', 'cliente').order_by('-creado_en')[:5]
    except Exception:
        incidentes_no_atendidos = 0
        ult_incidentes = []

    context = {
        'pendientes_clientes': pendientes_clientes,
        'pedidos_activos': pedidos_activos,
        'viajes_activos': viajes_activos,
        'stock_kg': stock_kg,
        'reservas_purgadas': purged,
        'por_vencer_count': por_vencer_count,
        'por_vencer_top': por_vencer_top,
        'vencen_en': dias,
        'ult_pedidos_preparados': ult_pedidos_preparados,
        'ult_pedidos_entregados': ult_pedidos_entregados,
        'pedidos_por_estado': pedidos_por_estado,
        'stock_por_corte': stock_por_corte,
        'home_frigo_resumen': home_frigo_resumen,
        'venc_fechas': venc_fechas,
        'pedidos_por_viaje_fecha': pedidos_por_viaje_fecha,
        'incidentes_no_atendidos': incidentes_no_atendidos,
        'ult_incidentes': ult_incidentes,
    }
    return render(request, 'html/encargado.html', context)


@group_required('Encargado')
def reporte_stock(request):
    estado = request.GET.get('estado', '')
    corte = request.GET.get('corte', '')
    frigorifico = request.GET.get('frigorifico', '')

    qs = Productos.objects.all().select_related('nombre', 'frigorificop')
    if estado:
        qs = qs.filter(estado=estado)
    if corte.isdigit():
        qs = qs.filter(nombre_id=int(corte))
    if frigorifico.isdigit():
        qs = qs.filter(frigorificop_id=int(frigorifico))

    # Aggregación por corte y estado
    resumen = (qs.values('nombre__nombre', 'estado')
               .annotate(total=Count('id'), kilos=Sum('kilos'))
               .order_by('nombre__nombre', 'estado'))

    cortes = Cortes.objects.all().order_by('nombre')
    frigos = Frigorifico.objects.all().order_by('nombre')

    # Resumen por cámara (frigorífico): capacidad (cantidad de productos) y ocupación en productos
    qs_en_stock = Productos.objects.filter(estado='en stock')
    if frigorifico.isdigit():
        qs_en_stock = qs_en_stock.filter(frigorificop_id=int(frigorifico))

    ocupacion = (qs_en_stock.values('frigorificop_id', 'frigorificop__nombre')
                 .annotate(kilos=Sum('kilos'), productos=Count('id')))

    # Mapear ocupación por id para acceso rápido
    occ_by_id = {o['frigorificop_id']: o for o in ocupacion}
    frigo_resumen = []
    for f in frigos:
        occ = occ_by_id.get(f.id, {'kilos': 0, 'productos': 0})
        usados_kg = float(occ.get('kilos') or 0)
        productos_count = int(occ.get('productos') or 0)
        # capacidad en cantidad de productos
        capacidad = float(f.capacidad or 0)
        ocupacion_pct = (productos_count / capacidad *
                         100.0) if capacidad > 0 else 0.0
        restante_prod = max(capacidad - productos_count, 0)
        low_stock = (ocupacion_pct < 30.0) or (productos_count < 3)
        frigo_resumen.append({
            'id': f.id,
            'nombre': f.nombre,
            'capacidad': capacidad,
            'kilos': usados_kg,
            'restante': restante_prod,
            'productos': productos_count,
            'ocupacion_pct': round(ocupacion_pct, 2),
            'low_stock': low_stock,
        })

    # Conteo de cantidad de productos por corte (no por kilos)
    counts_by_corte = (
        qs.values('nombre__nombre')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return render(request, 'html/reportes/stock.html', {
        'resumen': resumen,
        'cortes': cortes,
        'frigorificos': frigos,
        'frigo_resumen': frigo_resumen,
        'counts_by_corte': counts_by_corte,
        'estado_sel': estado,
        'corte_sel': int(corte) if corte.isdigit() else None,
        'frigorifico_sel': int(frigorifico) if frigorifico.isdigit() else None,
    })


@group_required('Encargado')
def reporte_pedidos(request):
    estado = request.GET.get('estado', '')
    comercio = request.GET.get('comercio', '')
    fecha_desde = request.GET.get('desde', '')
    fecha_hasta = request.GET.get('hasta', '')

    qs = Pedido.objects.select_related('cliente__comercio', 'estado').all()
    if estado:
        qs = qs.filter(estado__estado=estado)
    if comercio.isdigit():
        qs = qs.filter(cliente__comercio_id=int(comercio))
    if fecha_desde:
        qs = qs.filter(creado_en__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(creado_en__date__lte=fecha_hasta)

    total = qs.count()
    por_estado = (qs.values('estado__estado')
                  .annotate(cant=Count('id'))
                  .order_by('estado__estado'))

    comercios = Comercio.objects.all().order_by('nombre')

    return render(request, 'html/reportes/pedidos.html', {
        'pedidos': qs.order_by('-creado_en')[:200],
        'total': total,
        'por_estado': por_estado,
        'comercios': comercios,
        'estado_sel': estado,
        'comercio_sel': int(comercio) if comercio.isdigit() else None,
        'desde': fecha_desde,
        'hasta': fecha_hasta,
    })


@group_required('Encargado')
def reporte_viajes(request):
    chofer = request.GET.get('chofer', '')
    camion = request.GET.get('camion', '')
    fecha = request.GET.get('fecha', '')
    fecha_desde = request.GET.get('desde', '')
    fecha_hasta = request.GET.get('hasta', '')

    qs = Viaje.objects.select_related(
        'chofer', 'ayudante', 'camion_viaje').all()
    if chofer.isdigit():
        qs = qs.filter(chofer_id=int(chofer))
    if camion.isdigit():
        qs = qs.filter(camion_viaje_id=int(camion))
    if fecha:
        qs = qs.filter(fecha__date=fecha)
    if fecha_desde:
        qs = qs.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__date__lte=fecha_hasta)

    viajes = []
    for v in qs.order_by('-fecha')[:200]:
        pedidos = Pedido.objects.filter(viaje=v).select_related(
            'estado', 'cliente__comercio')
        viajes.append({
            'viaje': v,
            'activos': pedidos.filter(estado__estado='activo').count(),
            'entregados': pedidos.filter(estado__estado='entregado').count(),
            'total_pedidos': pedidos.count(),
        })

    return render(request, 'html/reportes/viajes.html', {
        'viajes': viajes,
        'chofer_sel': int(chofer) if chofer.isdigit() else None,
        'camion_sel': int(camion) if camion.isdigit() else None,
        'fecha_sel': fecha,
        'desde': fecha_desde,
        'hasta': fecha_hasta,
        'choferes': Empleados.objects.all().order_by('nombre'),
        'camiones': Camiones.objects.all().order_by('dominio'),
    })


@group_required('Encargado')
def reporte_vencimientos(request):
    dias = int(request.GET.get('dias', 7))
    ahora = timezone.now()
    candidatos = Productos.objects.filter(estado__in=['en stock', 'preparado']).select_related(
        'fecha_entrada', 'temperatura', 'nombre', 'frigorificop')
    lista = []
    for p in candidatos:
        try:
            venc = p.fecha_vencimiento()
            if ahora <= venc <= ahora + timedelta(days=dias):
                lista.append({'prod': p, 'venc': venc})
        except Exception:
            continue
    lista.sort(key=lambda x: x['venc'])

    return render(request, 'html/reportes/por_vencer.html', {
        'items': lista,
        'dias': dias,
    })


@group_required('Encargado')
def reporte_consolidado(request):
    """Reporte consolidado con filtros por fecha, estado, corte y comercio.
    Incluye resumenes y exportación CSV.
    """
    # Filtros
    estado = request.GET.get('estado', '').strip()
    corte_id = request.GET.get('corte', '').strip()
    comercio_id = request.GET.get('comercio', '').strip()
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()

    pedidos = Pedido.objects.select_related(
        'cliente__comercio', 'estado').all()
    if estado:
        pedidos = pedidos.filter(estado__estado=estado)
    if corte_id.isdigit():
        # Filtrar pedidos que contienen detalles con ese corte
        pedidos = pedidos.filter(
            detallepedido__producto_id__nombre_id=int(corte_id)).distinct()
    if comercio_id.isdigit():
        pedidos = pedidos.filter(cliente__comercio_id=int(comercio_id))
    if desde:
        pedidos = pedidos.filter(creado_en__date__gte=desde)
    if hasta:
        pedidos = pedidos.filter(creado_en__date__lte=hasta)

    # Resúmenes
    total_pedidos = pedidos.count()
    por_estado = (pedidos.values('estado__estado')
                  .annotate(cant=Count('id'))
                  .order_by('estado__estado'))
    # Top cortes por kg de productos asociados en pedidos filtrados
    detalles = DetallePedido.objects.filter(pedido_id__in=pedidos.values('id'))
    # Incluir product id para poder enlazar al detalle del producto desde el reporte
    top_cortes = (
        detalles.values('producto_id', 'producto_id__nombre__nombre')
        .annotate(kg=Sum('producto_id__kilos'), cant=Count('id'))
        .order_by('-kg')[:10]
    )

    # Catálogos para filtros
    comercios = Comercio.objects.all().order_by('nombre')
    cortes = Cortes.objects.all().order_by('nombre')

    context = {
        'total_pedidos': total_pedidos,
        'por_estado': por_estado,
        'top_cortes': top_cortes,
        'comercios': comercios,
        'cortes': cortes,
        'estado_sel': estado,
        'corte_sel': int(corte_id) if corte_id.isdigit() else None,
        'comercio_sel': int(comercio_id) if comercio_id.isdigit() else None,
        'desde': desde,
        'hasta': hasta,
    }
    return render(request, 'html/reportes/consolidado.html', context)


@group_required('Encargado')
def nuevo_pedido(request):
    productos = Productos.objects.all()
    return render(request, 'html/nuevo_pedido.html', {'productos': productos})


@group_required('Encargado')
def nuevo_pedido_manual(request):
    """Crea un pedido desde cero seleccionando el cliente (sucursal destino)."""
    if request.method == 'POST':
        form = PedidoNuevoForm(request.POST)
        if form.is_valid():
            from .models import EstadoPedidos
            estado_inicial, _ = EstadoPedidos.objects.get_or_create(
                estado='preparado')

            pedido = Pedido.objects.create(
                cliente=form.cleaned_data['cliente'],
                comercio_origen=form.cleaned_data.get('comercio_origen'),
                observaciones=form.cleaned_data.get('observaciones', ''),
                estado=estado_inicial,
                user_id=request.user,
                creado_en=timezone.now(),
            )
            messages.success(request, 'Pedido creado correctamente')
            return redirect('encargado:editar_pedido_preparado', pedido_id=pedido.id)
    else:
        form = PedidoNuevoForm()

    return render(request, 'html/pedidos/nuevo_pedido_manual.html', {
        'form': form,
    })


def generar_ticket_pdf(producto):

    fecha_entrada = producto.fecha_entrada.fecha

    try:
        fecha_entrada_local = timezone.localtime(fecha_entrada)
    except Exception:
        fecha_entrada_local = fecha_entrada

    dias = producto.temperatura.dias
    fecha_vencimiento = fecha_entrada_local + timedelta(days=dias)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="ticket_trazabilidad.pdf"'

    # TAMAÑO ETIQUETA (similar frigorífico)
    width = 10 * cm
    height = 7 * cm

    c = canvas.Canvas(response, pagesize=(width, height))

    y = height - 0.5 * cm

    # ---------- ENCABEZADO ----------
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2, y, "CarneClick - Trazabilidad")
    y -= 0.4 * cm

    c.setFont("Helvetica", 7)

    c.line(0.3 * cm, y, width - 0.3 * cm, y)
    y -= 0.4 * cm

    # ---------- DATOS ----------

    # proveedor
    proveedor_nombre = ''
    try:
        entrada = producto.fecha_entrada
        if entrada and getattr(entrada, 'proveedor', None):
            proveedor_nombre = entrada.proveedor.nombre
    except:
        pass

    c.drawString(0.4 * cm, y, f"Proveedor: {proveedor_nombre}")
    y -= 0.35 * cm

    # lote
    lote_numero = ''
    try:
        lote_numero = getattr(entrada, 'numero_lote', '') or ''
    except:
        pass

    if lote_numero:
        c.drawString(0.4 * cm, y, f"Tropa/Lote: {lote_numero}")
        y -= 0.35 * cm

    # fechas
    fecha_entrada_str = fecha_entrada_local.strftime("%d/%m/%Y")
    fecha_vencimiento_str = fecha_vencimiento.strftime("%d/%m/%Y")

    c.drawString(0.4 * cm, y, f"Entrada: {fecha_entrada_str}")
    y -= 0.35 * cm

    c.drawString(0.4 * cm, y, f"Venc: {fecha_vencimiento_str}")
    y -= 0.5 * cm

    c.line(0.3 * cm, y, width - 0.3 * cm, y)
    y -= 0.7 * cm

    # ---------- CODIGO GRANDE ----------
    codigo = getattr(producto, 'codigo', '')

    if not codigo:
        prod_id = getattr(producto, 'id', None)
        if prod_id:
            codigo = f"{prod_id:07d}"
        else:
            try:
                max_id = Productos.objects.aggregate(
                    max_id=Max('id'))['max_id'] or 0
                codigo = f"{max_id+1:07d}"
            except:
                codigo = datetime.now().strftime("%H%M%S")

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, y, codigo)

    y -= 0.6 * cm

    # Etiqueta pequeña indicando que es el número de identificación
    c.setFont("Helvetica", 6)
    c.drawCentredString(width / 2, y, "N° Identificación")

    # Mostrar nombre, kilos por unidad y cantidad debajo del código
    try:
        nombre_str = str(getattr(producto, 'nombre', '') or '')
    except Exception:
        nombre_str = ''
    try:
        kilos_val = float(getattr(producto, 'kilos', 0) or 0)
        kilos_str = f"{kilos_val:.2f} kg"
    except Exception:
        kilos_str = "0.00 kg"
    try:
        cantidad_val = int(getattr(producto, 'cantidad', 1) or 1)
        cantidad_str = f"Cantidad: {cantidad_val}"
    except Exception:
        cantidad_str = "Cantidad: 1"

    y -= 0.35 * cm
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, y, nombre_str)
    y -= 0.35 * cm
    # mostrar kilos y cantidad en la misma línea separadas por un punto
    c.drawCentredString(width / 2, y, f"{kilos_str} • {cantidad_str}")

    c.showPage()
    c.save()

    return response


@group_required('Encargado')
def perfil(request):
    """Vista de configuración de perfil para el encargado: editar usuario/email y cambiar contraseña."""
    user = request.user
    if request.method == 'POST':
        if 'save_profile' in request.POST:
            perfil_form = PerfilForm(request.POST, instance=user)
            pwd_form = PasswordChangeForm(user)
            for f in pwd_form.fields.values():
                f.widget.attrs.setdefault('class', 'form-control')
            if perfil_form.is_valid():
                perfil_form.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('encargado:perfil')
        elif 'change_password' in request.POST:
            perfil_form = PerfilForm(instance=user)
            pwd_form = PasswordChangeForm(user, request.POST)
            for f in pwd_form.fields.values():
                f.widget.attrs.setdefault('class', 'form-control')
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)
                messages.success(
                    request, 'Contraseña actualizada correctamente.')
                return redirect('encargado:perfil')
    else:
        perfil_form = PerfilForm(instance=user)
        pwd_form = PasswordChangeForm(user)
        for f in pwd_form.fields.values():
            f.widget.attrs.setdefault('class', 'form-control')

    return render(request, 'html/configuracion/perfil.html', {
        'perfil_form': perfil_form,
        'pwd_form': pwd_form,
    })


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
    productos = Productos.objects.filter(estado='en stock')
    return render(request, 'html/productos/stock.html', {'productos': productos})


@group_required('Encargado')
def ver_todos_productos(request):
    """Lista todos los productos con cualquier estado, ordenando por estado.
    Orden: en stock -> preparado -> de viaje -> entregado.
    """
    order_case = Case(
        When(estado='en stock', then=0),
        When(estado='preparado', then=1),
        When(estado='de viaje', then=2),
        When(estado='entregado', then=3),
        default=4,
        output_field=IntegerField()
    )
    productos = Productos.objects.annotate(
        order_key=order_case).order_by('order_key', 'id')
    return render(request, 'html/productos/ver_todos_productos.html', {
        'productos': productos
    })


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


@group_required('Encargado')
def entrada_detalle(request, entrada_id):
    """Muestra todos los productos cargados en una `Entrada`."""
    entrada = get_object_or_404(Entrada, id=entrada_id)
    productos = (Productos.objects
                 .filter(fecha_entrada=entrada)
                 .select_related('nombre', 'frigorificop', 'temperatura'))

    total_items = productos.count()
    total_kilos = sum(float(p.kilos or 0) for p in productos)

    return render(request, 'html/productos/entrada_detalle.html', {
        'entrada': entrada,
        'productos': productos,
        'total_items': total_items,
        'total_kilos': total_kilos,
    })


@group_required('Encargado')
def generar_ticket_entrada(request, entrada_id):
    """Genera una boleta PDF para una `Entrada` con sus productos, fecha y proveedor."""
    entrada = get_object_or_404(Entrada, id=entrada_id)
    productos = (Productos.objects
                 .filter(fecha_entrada=entrada)
                 .select_related('nombre', 'frigorificop', 'temperatura'))

    buffer = BytesIO()
    # Usar A4 en orientación apaisada para más espacio horizontal
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    x_margin = 2 * cm
    y = height - 2 * cm

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x_margin, y, f"Boleta de Entrada #{entrada.id}")
    y -= 1 * cm

    c.setFont("Helvetica", 11)
    if entrada.fecha:
        try:
            fecha_local = timezone.localtime(entrada.fecha)
        except Exception:
            fecha_local = entrada.fecha
        fecha_str = fecha_local.strftime("%d/%m/%Y %H:%M")
    else:
        try:
            fecha_local = timezone.localtime(timezone.now())
        except Exception:
            fecha_local = timezone.now()
        fecha_str = fecha_local.strftime("%d/%m/%Y %H:%M")
    proveedor_nombre = getattr(
        entrada.proveedor, 'nombre', '-') if getattr(entrada, 'proveedor', None) else '-'
    c.drawString(x_margin, y, f"Fecha: {fecha_str}")
    y -= 0.7 * cm
    c.drawString(x_margin, y, f"Proveedor: {proveedor_nombre}")
    y -= 0.7 * cm
    if getattr(entrada, 'numero_lote', None):
        c.drawString(x_margin, y, f"Lote: {entrada.numero_lote}")
        y -= 0.7 * cm

    # Separador
    c.line(x_margin, y, width - x_margin, y)
    y -= 0.8 * cm

    # Tabla productos
    # Encabezado de tabla más compacto
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Código")
    c.drawString(x_margin + 2.8 * cm, y, "Descripción")
    c.drawRightString(x_margin + 11.0 * cm, y, "Kilos (c/u)")
    c.drawRightString(x_margin + 14.0 * cm, y, "Cantidad")
    c.drawRightString(x_margin + 17.0 * cm, y, "Kilos tot.")
    c.drawString(x_margin + 19.2 * cm, y, "Frigorífico")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)

    for p in productos:
        if y < 2.5 * cm:
            c.showPage()
            # nuevo header en página siguiente
            y = height - 2 * cm
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Código")
            c.drawString(x_margin + 2.8 * cm, y, "Descripción")
            c.drawRightString(x_margin + 11.0 * cm, y, "Kilos (c/u)")
            c.drawRightString(x_margin + 14.0 * cm, y, "Cantidad")
            c.drawRightString(x_margin + 17.0 * cm, y, "Kilos tot.")
            c.drawString(x_margin + 19.2 * cm, y, "Frigorífico")
            y -= 0.5 * cm
            c.setFont("Helvetica", 10)

        codigo = getattr(p, 'codigo', '') or f"P{p.id:06d}"
        frigorifico_nombre = getattr(
            p.frigorificop, 'nombre', str(p.frigorificop))
        desc = getattr(p.nombre, 'nombre', str(p.nombre))
        kilos_val = getattr(p, 'kilos', 0) or 0
        cantidad_val = getattr(p, 'cantidad', 1) or 1
        try:
            kilos_tot = float(kilos_val) * int(cantidad_val)
        except Exception:
            kilos_tot = 0

        # pintar fila con alineación numérica a la derecha
        c.drawString(x_margin, y, f"{codigo}")
        # limitar descripción para evitar overflow
        desc_short = (desc[:60] + '...') if len(desc) > 63 else desc
        c.drawString(x_margin + 2.8 * cm, y, desc_short)
        c.drawRightString(x_margin + 11.0 * cm, y, f"{float(kilos_val):.2f}")
        c.drawRightString(x_margin + 14.0 * cm, y, f"{int(cantidad_val)}")
        c.drawRightString(x_margin + 17.0 * cm, y, f"{kilos_tot:.2f}")
        c.drawString(x_margin + 19.2 * cm, y, frigorifico_nombre)
        y -= 0.55 * cm

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="boleta_entrada_{entrada.id}.pdf"'
    return response


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
        # Nueva entrada: limpiar payload previo para no bloquear el primer agregado
        request.session.pop('last_entry_payload', None)
        request.session.pop('last_entry_payload_ts', None)
        request.session.modified = True

    # Asegurar que la entrada tenga número de lote autogenerado
    try:
        if not getattr(entrada_actual, 'numero_lote', None):
            entrada_actual.save()
    except Exception:
        pass

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.fecha_entrada = entrada_actual
            # cantidad indicada en el formulario: crea múltiples Productos si >1
            try:
                cantidad = int(request.POST.get('cantidad') or 1)
            except Exception:
                cantidad = 1

            # Si se envió un proveedor para la entrada, guardarlo en la Entrada
            entrada_proveedor_id = request.POST.get('entrada_proveedor')
            if entrada_proveedor_id:
                try:
                    entrada_actual.proveedor_id = int(entrada_proveedor_id)
                    entrada_actual.save()
                except (ValueError, Proveedor.DoesNotExist):
                    pass

            # 🧾 Generar ticket: NO guardar producto, solo generar PDF
            if 'ticket' in request.POST:
                # No persistimos el producto, solo usamos los datos del formulario
                return generar_ticket_pdf(producto)

            # Sin bloqueo por valores repetidos: permitir mismo kilaje/campos

            accion = request.POST.get('accion')

            # ➕ Guardar y seguir
            if accion == 'Agregar otro producto':
                # Estado por defecto: en stock
                producto.estado = 'en stock'
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
                # Estado por defecto: en stock
                producto.estado = 'en stock'
                producto.save()
                # limpiar sesión relacionada con la entrada y último producto
                request.session.pop('entrada_id', None)
                request.session.pop('ultimo_producto', None)
                request.session.modified = True
                return HttpResponseRedirect('/encargado/productos/ver_todos/')

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
        return HttpResponseRedirect('/encargado/productos/ver_todos/')

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/encargado/productos/ver_todos/')
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
        return HttpResponseRedirect('/encargado/productos/ver_todos/')

    if request.method == 'POST':
        producto.delete()
        return HttpResponseRedirect('/encargado/productos/ver_todos/')

    return render(request, 'html/productos/confirm_delete.html', {
        'producto': producto,
    })


@group_required('Encargado')
def ver_producto(request, pk):
    """Muestra detalle completo de un `Productos` incluyendo su `Entrada` de origen."""
    producto = get_object_or_404(
        Productos.objects.select_related(
            'fecha_entrada__proveedor', 'nombre', 'frigorificop', 'temperatura'),
        pk=pk
    )

    # Calcular fecha de vencimiento segura
    try:
        fecha_venc = producto.fecha_vencimiento()
    except Exception:
        fecha_venc = None

    entrada = producto.fecha_entrada

    context = {
        'producto': producto,
        'entrada': entrada,
        'proveedor': getattr(entrada, 'proveedor', None),
        'fecha_vencimiento': fecha_venc,
    }

    return render(request, 'html/productos/producto_detalle.html', context)


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


# =====================
# Vistas de Pedidos
# =====================

@group_required('Encargado')
def iniciar_pedido(request, pedido_pendiente_id):
    # Pedido pendiente del cliente (pedido de carrito previo)
    pedido_pendiente = get_object_or_404(
        Pedido_cliente, id=pedido_pendiente_id)

    # Cliente (perfil) asociado al usuario del pedido pendiente
    cliente = get_object_or_404(Cliente, user=pedido_pendiente.cliente)

    # Crear/obtener un Pedido vinculado a este pedido_pendiente
    try:
        pedido = Pedido.objects.get(pedido_pendiente=pedido_pendiente)
    except Pedido.DoesNotExist:
        # Estado inicial (preparado) asegurado
        from .models import EstadoPedidos
        estado_inicial, _ = EstadoPedidos.objects.get_or_create(
            estado='preparado')

        pedido = Pedido.objects.create(
            cliente=cliente,
            pedido_pendiente=pedido_pendiente,
            estado=estado_inicial,
            user_id=request.user,
        )

    # Persistir en sesión para navegación
    request.session['pedido_id'] = pedido.id
    request.session['pedido_pendiente_id'] = pedido_pendiente.id

    # Form (solo se muestran comercio_origen y observaciones en el template)
    pedido_form = PedidoForm(instance=pedido)

    return render(request, 'html/pedidos/iniciar_pedido.html', {
        'pedido': pedido,
        'cliente': cliente,
        'pedido_form': pedido_form,
    })


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

    # ENCABEZADO
    elements.append(Paragraph(
        "<b>DOCUMENTO NO VÁLIDO COMO FACTURA</b>",
        styles["Title"]
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
        f"<b>Observaciones:</b> {pedido.observaciones or ''}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"<b>REMITO Nº:</b> R{pedido.id:04d} &nbsp;&nbsp;"
        f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 15))

    # TABLA DE PRODUCTOS
    data = [
        ["Código", "Descripción", "Kilos", "Cantidad"]
    ]

    for item in pedido.detallepedido_set.all():
        prod = item.producto_id
        kilos_val = getattr(prod, 'kilos', 0) or 0
        try:
            kilos_str = f"{float(kilos_val):.2f}"
        except Exception:
            kilos_str = str(kilos_val)
        data.append([
            str(getattr(prod, 'id', '')),
            str(getattr(prod, 'nombre', '')),
            str(kilos_str),
            str(getattr(item, 'cantidad', ''))
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

    # FIRMAS
    elements.append(Paragraph(
        "Firma: ________________________________",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        "Aclaración: ____________________________",
        styles["Normal"]
    ))

    doc.build(elements)
    return response


@group_required('Encargado')
def agregar_producto_por_id(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido_pendiente_id = request.session.get('pedido_pendiente_id')

    if not pedido_pendiente_id:
        messages.error(request, 'No hay pedido pendiente en sesión')
        return redirect('encargado:pedidos_pendientes')

    if request.method == 'POST':
        # Permitir ID o Código
        producto_id_str = request.POST.get('producto_id', '').strip()
        producto_codigo = request.POST.get('producto_codigo', '').strip()
        try:
            cantidad_pedido = max(
                1, int(request.POST.get('cantidad_pedido', 1) or 1))
        except (ValueError, TypeError):
            cantidad_pedido = 1

        if not producto_id_str and not producto_codigo:
            messages.error(
                request, 'Debes ingresar un ID o Código de producto')
        else:
            producto = None
            if producto_id_str:
                try:
                    producto_id = int(producto_id_str)
                    producto = Productos.objects.filter(id=producto_id).first()
                except ValueError:
                    messages.error(request, 'El ID debe ser un número')
                    return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)
            if not producto and producto_codigo:
                producto = Productos.objects.filter(
                    codigo=producto_codigo).first()
            if not producto:
                messages.error(request, 'El producto indicado no existe')
            else:
                # Operación crítica: bloquear fila del producto
                with transaction.atomic():
                    try:
                        producto_locked = Productos.objects.select_for_update().get(id=producto.id)
                    except Productos.DoesNotExist:
                        messages.error(
                            request, 'El producto indicado no existe')
                        return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)

                    if producto_locked.estado != 'en stock':
                        messages.warning(
                            request, 'Solo se pueden agregar productos en estado "en stock"')
                    elif float(producto_locked.reserved_kilos or 0) > 0:
                        messages.warning(
                            request, 'El producto tiene reservas activas y no está disponible')
                    elif cantidad_pedido > producto_locked.cantidad:
                        messages.warning(
                            request,
                            f'Solo hay {producto_locked.cantidad} unidades disponibles de este producto')
                    elif DetallePedido.objects.filter(pedido_id=pedido, producto_id=producto_locked).exists():
                        messages.info(
                            request, 'El producto ya estaba agregado a este pedido')
                    else:
                        if cantidad_pedido == producto_locked.cantidad:
                            # Usar el producto completo
                            DetallePedido.objects.create(
                                pedido_id=pedido,
                                producto_id=producto_locked,
                                cantidad=cantidad_pedido
                            )
                            producto_locked.estado = 'preparado'
                            producto_locked.save(update_fields=['estado'])
                        else:
                            # Split: reducir original y crear registro preparado
                            producto_locked.cantidad -= cantidad_pedido
                            producto_locked.save(update_fields=['cantidad'])
                            nuevo = Productos.objects.create(
                                nombre=producto_locked.nombre,
                                kilos=producto_locked.kilos,
                                cantidad=cantidad_pedido,
                                reserved_kilos=0,
                                fecha_entrada=producto_locked.fecha_entrada,
                                temperatura=producto_locked.temperatura,
                                frigorificop=producto_locked.frigorificop,
                                estado='preparado',
                            )
                            DetallePedido.objects.create(
                                pedido_id=pedido,
                                producto_id=nuevo,
                                cantidad=cantidad_pedido
                            )
                        messages.success(
                            request, 'Producto agregado correctamente')

    return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)


@group_required('Encargado')
def eliminar_producto_pedido(request, item_id):
    item = get_object_or_404(DetallePedido, id=item_id)
    pedido_pendiente_id = request.session.get('pedido_pendiente_id')
    # Al eliminar del pedido, el producto vuelve a 'en stock'
    with transaction.atomic():
        producto = Productos.objects.select_for_update().get(id=item.producto_id.id)
        producto.estado = 'en stock'
        producto.save(update_fields=['estado'])
        item.delete()
    messages.success(request, 'Producto eliminado del pedido')
    if not pedido_pendiente_id:
        return redirect('encargado:pedidos_pendientes')
    return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)


@group_required('Encargado')
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido_pendiente_id = request.session.get('pedido_pendiente_id')

    # Revertir estado de todos los productos del pedido a 'en stock'
    with transaction.atomic():
        for item in pedido.detallepedido_set.select_related('producto_id').all():
            prod = Productos.objects.select_for_update().get(id=item.producto_id.id)
            prod.estado = 'en stock'
            prod.save(update_fields=['estado'])

    # Eliminar el pedido (Detalles se borran por cascada)
    pedido.delete()

    # Eliminar también el pedido pendiente
    if pedido_pendiente_id:
        Pedido_cliente.objects.filter(id=pedido_pendiente_id).delete()

    # Limpiar sesión
    request.session.pop('pedido_pendiente_id', None)
    request.session.pop('pedido_id', None)

    messages.warning(request, 'Pedido cancelado correctamente')
    return redirect('encargado:pedidos_pendientes')


@group_required('Encargado')
def finalizar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido_pendiente_id = request.session.get('pedido_pendiente_id')

    # Debe tener al menos un producto
    if not pedido.detallepedido_set.exists():
        messages.warning(request, 'El pedido no tiene productos')
        return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)

    if request.method != 'POST':
        # No renderizar ningún template: redirigir a iniciar_pedido
        return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)

    comercio_origen_id = request.POST.get('comercio_origen')
    if not comercio_origen_id:
        messages.warning(request, 'Debes seleccionar una sucursal de origen')
        return redirect('encargado:iniciar_pedido', pedido_pendiente_id=pedido_pendiente_id)

    comercio_origen = get_object_or_404(Comercio, id=comercio_origen_id)

    # Actualizar campos del pedido
    pedido.comercio_origen = comercio_origen
    pedido.observaciones = request.POST.get('observaciones', '')
    pedido.viaje = None
    pedido.user_id = request.user
    pedido.creado_en = timezone.now()

    # Estado entregado asegurado
    from .models import EstadoPedidos
    estado_final, _ = EstadoPedidos.objects.get_or_create(estado='preparado')
    pedido.estado = estado_final

    pedido.save()

    # Desvincular el OneToOne antes de eliminar el pedido pendiente
    # (si no, CASCADE borrará el Pedido también)
    if pedido_pendiente_id:
        pedido.pedido_pendiente = None
        pedido.save(update_fields=['pedido_pendiente'])
        Pedido_cliente.objects.filter(id=pedido_pendiente_id).delete()
    request.session.pop('pedido_pendiente_id', None)
    request.session.pop('pedido_id', None)

    messages.success(request, 'Pedido finalizado correctamente')
    return redirect('encargado:pedidos_pendientes')


@group_required('Encargado')
def boleta_pedido(request, pedido_id):
    """Genera un PDF (boleta) con estilo similar al ejemplo proporcionado."""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    cliente = pedido.cliente
    detalles = pedido.detallepedido_set.select_related(
        'producto_id', 'producto_id__nombre')

    buffer = BytesIO()
    # Usar mitad de hoja A4 (alto reducido) para imprimir 2 boletas por hoja
    half_height = A4[1] / 2.0
    c = canvas.Canvas(buffer, pagesize=(A4[0], half_height))
    width, height = (A4[0], half_height)

    # Márgenes más compactos
    left = 1.5 * cm
    right = width - 1.5 * cm
    y = height - 1.2 * cm

    # Header central compacto
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(width / 2.0, y, 'DOCUMENTO NO VALIDO COMO FACTURA')

    # Remito número arriba a la derecha
    remito_str = f'REMITO N\u00ba  R{pedido.id:04d}'
    c.setFont('Helvetica-Bold', 9)
    c.drawRightString(right, y + 6, remito_str)

    # Fecha arriba a la derecha (alineado bajo el remito)
    fecha_str = pedido.creado_en.strftime(
        '%d/%m/%Y') if pedido.creado_en else timezone.now().strftime('%d/%m/%Y')
    c.setFont('Helvetica', 8)
    c.drawRightString(right, y - 8, f'Fecha: {fecha_str}')

    y -= 14

    # Caja con sucursal origen / destino y observaciones (a la izquierda)
    box_h = 38
    c.setLineWidth(0.5)
    c.rect(left, y - box_h, right - left, box_h, stroke=1, fill=0)

    # Dentro de la caja: origen, destino, observaciones
    inner_x = left + 6
    inner_y = y - 10
    origen_nombre = str(getattr(pedido.comercio_origen, 'nombre', '-'))
    destino_nombre = str(getattr(cliente.comercio, 'nombre', '-'))
    observ = pedido.observaciones or ''

    c.setFont('Helvetica-Bold', 8)
    c.drawString(inner_x, inner_y, 'Sucursal Origen:')
    c.setFont('Helvetica', 8)
    c.drawString(inner_x + 80, inner_y, origen_nombre[:50])

    c.setFont('Helvetica-Bold', 8)
    c.drawString(inner_x, inner_y - 12, 'Sucursal Destino:')
    c.setFont('Helvetica', 8)
    c.drawString(inner_x + 80, inner_y - 12, destino_nombre[:50])

    c.setFont('Helvetica-Bold', 8)
    c.drawString(inner_x, inner_y - 24, 'Observaciones:')
    c.setFont('Helvetica', 8)
    c.drawString(inner_x + 80, inner_y - 24, observ[:80])

    y = y - box_h - 10

    # Tabla: encabezado
    col_codigo = left + 6
    col_descrip = left + 50
    col_kilos = right - 100
    col_cant = right - 30

    c.setFont('Helvetica-Bold', 9)
    c.drawString(col_codigo, y, 'Codigo')
    c.drawString(col_descrip, y, 'Descripcion')
    c.drawRightString(col_kilos + 40, y, 'Kilos')
    c.drawRightString(col_cant + 20, y, 'Cantidad')
    y -= 10

    c.setLineWidth(0.3)
    # dibujar líneas de cabecera
    c.line(left + 2, y + 6, right - 2, y + 6)

    c.setFont('Helvetica', 8)
    row_h = 10
    for item in detalles:
        if y < 1.5 * cm:
            c.showPage()
            # resetear posición en nueva media-hoja
            y = height - 1.2 * cm
        prod = item.producto_id
        codigo = str(getattr(prod, 'id', ''))
        nombre = str(getattr(prod, 'nombre', ''))
        # Añadir id interno entre paréntesis si se desea
        codigo_val = getattr(
            prod, 'codigo', '') or f"ID:{getattr(prod, 'id', '')}"
        descripcion = f"{nombre} ({codigo_val})"
        kilos = f"{getattr(prod, 'kilos', '')}"
        cantidad = str(getattr(item, 'cantidad', ''))

        c.drawString(col_codigo, y, codigo)
        # limitar descripción si es muy larga
        c.drawString(col_descrip, y, descripcion[:60])
        c.drawRightString(col_kilos + 40, y, kilos)
        c.drawRightString(col_cant + 20, y, cantidad)

        # línea separadora
        c.line(left + 2, y - 2, right - 2, y - 2)
        y -= row_h

    # Firmas (reducidas)
    sig_y = 2.2 * cm
    c.line(left + 30, sig_y, left + 140, sig_y)
    c.drawString(left + 60, sig_y - 12, 'Firma')

    c.line(right - 140, sig_y, right - 30, sig_y)
    c.drawString(right - 120, sig_y - 12, 'Aclaracion')

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="boleta_pedido_{pedido.id}.pdf"'
    return response


@group_required('Encargado')
def pedidos_preparados(request):
    # Filtrar pedidos cuyo estado (FK) tenga valor 'preparado'
    pedidos = Pedido.objects.filter(estado__estado='preparado')
    return render(request, 'html/pedidos/pedidos_preparados.html', {'pedidos': pedidos})


@group_required('Encargado')
def incidentes_list(request):
    """Lista incidentes reportados por clientes."""
    incidentes = IncidenteEntrega.objects.select_related(
        'pedido', 'cliente').order_by('-creado_en')
    return render(request, 'html/incidentes/list.html', {'incidentes': incidentes})


@group_required('Encargado')
def incidente_detail(request, incidente_id):
    incidente = get_object_or_404(IncidenteEntrega, id=incidente_id)
    items = incidente.items.select_related('detalle_pedido', 'producto').all()
    if request.method == 'POST':
        # marcar atendido
        incidente.atendido = True
        incidente.save(update_fields=['atendido'])
        messages.success(request, 'Incidente marcado como atendido')
        return redirect('encargado:incidentes_list')
    return render(request, 'html/incidentes/detail.html', {'incidente': incidente, 'items': items})


@group_required('Encargado')
def detalles_pedido_preparado(request, pedido_id):
    """Muestra los productos (DetallePedido) de un pedido preparado."""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles = pedido.detallepedido_set.select_related(
        'producto_id',
        'producto_id__nombre',
        'producto_id__frigorificop',
        'producto_id__temperatura'
    )
    # Totales simples para presentación
    total_items = detalles.count()
    total_kilos = sum(getattr(d.producto_id, 'kilos', 0) for d in detalles)

    return render(request, 'html/pedidos/detalles_pedido_preparado.html', {
        'pedido': pedido,
        'cliente': pedido.cliente,
        'detalles': detalles,
        'total_items': total_items,
        'total_kilos': total_kilos,
    })


@group_required('Encargado')
def editar_pedido_preparado(request, pedido_id):
    """Permite editar campos básicos del pedido preparado."""
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Listado de productos actuales
    detalles = pedido.detallepedido_set.select_related(
        'producto_id', 'producto_id__nombre', 'producto_id__frigorificop', 'producto_id__temperatura'
    )
    agregar_form = AgregarProductoForm()

    if request.method == 'POST':
        form = PedidoEditForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pedido actualizado correctamente')
            # Si este pedido pertenece a un viaje, volver a gestionarlo
            if pedido.viaje_id:
                return redirect('encargado:gestionar_viaje', viaje_id=pedido.viaje_id)
            return redirect('encargado:detalles_pedido_preparado', pedido_id=pedido.id)
    else:
        form = PedidoEditForm(instance=pedido)

    return render(request, 'html/pedidos/editar_pedido_preparado.html', {
        'pedido': pedido,
        'form': form,
        'detalles': detalles,
        'agregar_form': agregar_form,
    })


@group_required('Encargado')
def agregar_producto_preparado(request, pedido_id):
    """Agrega un producto por ID al pedido preparado y marca su estado como 'preparado'."""
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        producto_id_str = request.POST.get('producto_id', '').strip()
        try:
            cantidad_pedido = max(
                1, int(request.POST.get('cantidad_pedido', 1) or 1))
        except (ValueError, TypeError):
            cantidad_pedido = 1

        if not producto_id_str:
            messages.error(request, 'Debes ingresar un ID de producto')
        else:
            # Permitir ID o Código
            producto = None
            try:
                producto_id = int(producto_id_str)
                producto = Productos.objects.filter(id=producto_id).first()
            except ValueError:
                # Si no es número, intentar por código
                producto = Productos.objects.filter(
                    codigo=producto_id_str).first()
            if not producto:
                messages.error(request, 'El producto indicado no existe')
            else:
                # Solo permitir productos en estado 'en stock'
                if producto.estado != 'en stock':
                    messages.warning(
                        request, 'Solo se pueden agregar productos en estado "en stock"')
                elif float(producto.reserved_kilos or 0) > 0:
                    messages.warning(
                        request, 'El producto tiene reservas activas y no está disponible')
                elif cantidad_pedido > producto.cantidad:
                    messages.warning(
                        request,
                        f'Solo hay {producto.cantidad} unidades disponibles de este producto')
                elif DetallePedido.objects.filter(pedido_id=pedido, producto_id=producto).exists():
                    messages.info(
                        request, 'El producto ya estaba agregado a este pedido')
                else:
                    with transaction.atomic():
                        producto_locked = Productos.objects.select_for_update().get(id=producto.id)
                        if cantidad_pedido == producto_locked.cantidad:
                            # Usar el producto completo
                            DetallePedido.objects.create(
                                pedido_id=pedido,
                                producto_id=producto_locked,
                                cantidad=cantidad_pedido
                            )
                            producto_locked.estado = 'preparado'
                            producto_locked.save(update_fields=['estado'])
                        else:
                            # Split: reducir original y crear registro preparado
                            producto_locked.cantidad -= cantidad_pedido
                            producto_locked.save(update_fields=['cantidad'])
                            nuevo = Productos.objects.create(
                                nombre=producto_locked.nombre,
                                kilos=producto_locked.kilos,
                                cantidad=cantidad_pedido,
                                reserved_kilos=0,
                                fecha_entrada=producto_locked.fecha_entrada,
                                temperatura=producto_locked.temperatura,
                                frigorificop=producto_locked.frigorificop,
                                estado='preparado',
                            )
                            DetallePedido.objects.create(
                                pedido_id=pedido,
                                producto_id=nuevo,
                                cantidad=cantidad_pedido
                            )
                    messages.success(
                        request, 'Producto agregado correctamente')

    return redirect('encargado:editar_pedido_preparado', pedido_id=pedido.id)


@group_required('Encargado')
def eliminar_item_preparado(request, item_id):
    """Elimina un item del pedido preparado y revierte el producto a 'en stock'."""
    item = get_object_or_404(DetallePedido, id=item_id)
    pedido = item.pedido_id
    from django.db import transaction
    with transaction.atomic():
        producto = Productos.objects.select_for_update().get(id=item.producto_id.id)
        producto.estado = 'en stock'
        producto.save(update_fields=['estado'])
        item.delete()
    messages.success(request, 'Producto eliminado del pedido')
    return redirect('encargado:editar_pedido_preparado', pedido_id=pedido.id)


@group_required('Encargado')
def eliminar_pedido_preparado(request, pedido_id):
    """Elimina por completo un pedido en estado 'preparado'.
    - Revierte todos los productos del pedido a estado 'en stock'.
    - Borra el pedido (cascada elimina detalles).
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Permitir solo eliminación por POST y solo si está 'preparado'
    if request.method != 'POST':
        messages.error(
            request, 'Operación no permitida. Debe usar POST para eliminar.')
        return redirect('encargado:pedidos_preparados')

    if getattr(pedido.estado, 'estado', None) != 'preparado':
        messages.warning(
            request, 'Solo se pueden eliminar pedidos en estado "preparado".')
        return redirect('encargado:pedidos_preparados')

    # Revertir estado de productos
    detalles = pedido.detallepedido_set.select_related('producto_id').all()
    from django.db import transaction
    with transaction.atomic():
        for det in detalles:
            prod = Productos.objects.select_for_update().get(id=det.producto_id.id)
            if prod and prod.estado != 'en stock':
                prod.estado = 'en stock'
                prod.save(update_fields=['estado'])

    # Eliminar pedido (cascade borra detalles)
    pedido.delete()
    messages.success(request, 'Pedido preparado eliminado correctamente.')
    return redirect('encargado:pedidos_preparados')


@group_required('Encargado')
def pedidos_entregados(request):
    """Lista de pedidos con estado 'entregado' con filtros por comercio y búsqueda.
    Filtros GET:
    - comercio: id del comercio (cliente.comercio_id)
    - q: texto para buscar por ID de pedido, nombre de comercio u observaciones
    """
    pedidos = (Pedido.objects
               .filter(estado__estado='entregado')
               .select_related('cliente__comercio', 'comercio_origen', 'estado')
               .order_by('-creado_en'))

    comercio_id = request.GET.get('comercio', '').strip()
    q = request.GET.get('q', '').strip()

    if comercio_id.isdigit():
        pedidos = pedidos.filter(cliente__comercio_id=int(comercio_id))

    if q:
        pedidos = pedidos.filter(
            Q(id__icontains=q) |
            Q(cliente__comercio__nombre__icontains=q) |
            Q(observaciones__icontains=q)
        )

    # Opciones de comercio disponibles en entregados
    comercios = (Cliente.objects
                 .filter(pedido__estado__estado='entregado')
                 .values('comercio_id', 'comercio__nombre')
                 .distinct()
                 .order_by('comercio__nombre'))

    context = {
        'pedidos': pedidos,
        'comercios': comercios,
        'comercio_id': int(comercio_id) if comercio_id.isdigit() else None,
        'q': q,
    }
    return render(request, 'html/pedidos/pedidos_entregados.html', context)


# =====================
# Vistas de Viajes
# =====================


@group_required('Encargado')
def nuevo_viaje(request):
    """Crea un nuevo viaje (chofer, ayudante, camión) y redirige a gestionarlo."""
    if request.method == 'POST':
        form = ViajeForm(request.POST)
        if form.is_valid():
            viaje = form.save()
            # Marcar recursos como ocupados
            from .models import Estado
            estado_ocupado, _ = Estado.objects.get_or_create(estado='ocupado')
            # Empleados
            if viaje.chofer:
                viaje.chofer.disponibilidad = estado_ocupado
                viaje.chofer.save(update_fields=['disponibilidad'])
            if viaje.ayudante:
                viaje.ayudante.disponibilidad = estado_ocupado
                viaje.ayudante.save(update_fields=['disponibilidad'])
            # Camión
            if viaje.camion_viaje:
                viaje.camion_viaje.disponibilidad = estado_ocupado
                viaje.camion_viaje.save(update_fields=['disponibilidad'])
            messages.success(request, 'Viaje creado correctamente')
            return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)
    else:
        form = ViajeForm()

    return render(request, 'html/viajes/nuevo_viaje.html', {
        'form': form,
    })


@group_required('Encargado')
def gestionar_viaje(request, viaje_id):
    """Pantalla para gestionar un viaje: listar pedidos, agregar desde pendientes o manual."""
    viaje = get_object_or_404(Viaje, id=viaje_id)

    pedidos_viaje = Pedido.objects.filter(viaje=viaje).select_related(
        'cliente', 'cliente__comercio', 'estado')

    form_pendiente = AgregarPedidoPendienteForm()
    form_manual = PedidoNuevoForm()

    return render(request, 'html/viajes/gestionar_viaje.html', {
        'viaje': viaje,
        'pedidos': pedidos_viaje,
        'form_pendiente': form_pendiente,
        'form_manual': form_manual,
    })


@group_required('Encargado')
def agregar_pedido_desde_pendiente(request, viaje_id):
    """Agrega un pedido al viaje a partir de un Pedido que esté en estado 'preparado'."""
    viaje = get_object_or_404(Viaje, id=viaje_id)
    if request.method != 'POST':
        return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)

    form = AgregarPedidoPendienteForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Selecciona un pedido preparado válido')
        return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)

    # Ahora seleccionamos un Pedido (modelo Pedido) que ya está en estado 'preparado'
    pedido = form.cleaned_data['pedido_pendiente']

    # Asociar el pedido seleccionado al viaje si aún no está asociado
    if pedido.viaje_id != viaje.id:
        pedido.viaje = viaje
        pedido.save(update_fields=['viaje'])

    messages.success(request, f'Pedido #{pedido.id} agregado al viaje.')
    # Permanecer en la pantalla de gestión del viaje
    return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)


@group_required('Encargado')
def agregar_pedido_manual_a_viaje(request, viaje_id):
    """Crea un pedido manual y lo asocia al viaje."""
    viaje = get_object_or_404(Viaje, id=viaje_id)
    if request.method != 'POST':
        return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)

    form = PedidoNuevoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Completa los datos del pedido manual')
        return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)

    from .models import EstadoPedidos
    estado_preparado, _ = EstadoPedidos.objects.get_or_create(
        estado='preparado')

    pedido = Pedido.objects.create(
        cliente=form.cleaned_data['cliente'],
        comercio_origen=form.cleaned_data.get('comercio_origen'),
        observaciones=form.cleaned_data.get('observaciones', ''),
        estado=estado_preparado,
        user_id=request.user,
        creado_en=timezone.now(),
        viaje=viaje,
    )

    messages.success(
        request, f'Pedido #{pedido.id} creado y agregado al viaje.')
    return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)


@group_required('Encargado')
def cancelar_viaje(request, viaje_id):
    """Cancela un viaje: devuelve pedidos asociados a estado 'preparado' y elimina el viaje."""
    viaje = get_object_or_404(Viaje, id=viaje_id)
    if request.method != 'POST':
        return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)

    # Estado 'preparado' asegurado
    from .models import EstadoPedidos, Estado
    estado_preparado, _ = EstadoPedidos.objects.get_or_create(
        estado='preparado')
    estado_disponible, _ = Estado.objects.get_or_create(estado='disponible')

    # Revertir pedidos asociados: quitar viaje y poner estado preparado
    pedidos = Pedido.objects.filter(viaje=viaje)
    for p in pedidos:
        p.viaje = None
        p.estado = estado_preparado
        p.save(update_fields=['viaje', 'estado'])

    # Liberar disponibilidad de chofer/ayudante/camion si estaban ocupados
    try:
        if viaje.chofer:
            viaje.chofer.disponibilidad = estado_disponible
            viaje.chofer.save(update_fields=['disponibilidad'])
    except Exception:
        pass
    try:
        if viaje.ayudante:
            viaje.ayudante.disponibilidad = estado_disponible
            viaje.ayudante.save(update_fields=['disponibilidad'])
    except Exception:
        pass
    try:
        if viaje.camion_viaje:
            viaje.camion_viaje.disponibilidad = estado_disponible
            viaje.camion_viaje.save(update_fields=['disponibilidad'])
    except Exception:
        pass

    viaje.delete()
    messages.warning(
        request, f'Viaje #{viaje_id} cancelado y pedidos devueltos a "preparado"')
    return redirect('encargado:viajes_activos')


def iniciar_viaje(request, viaje_id):
    """Pone el viaje en marcha: pedidos a 'activo' y productos a 'de viaje'."""
    viaje = get_object_or_404(Viaje, id=viaje_id)

    from .models import EstadoPedidos
    estado_activo, _ = EstadoPedidos.objects.get_or_create(estado='activo')

    pedidos = Pedido.objects.filter(viaje=viaje)
    if not pedidos.exists():
        messages.warning(request, 'El viaje no tiene pedidos asociados')
        return redirect('encargado:gestionar_viaje', viaje_id=viaje.id)

    # Cambiar estados de pedidos y productos con bloqueo
    from django.db import transaction
    with transaction.atomic():
        for pedido in pedidos:
            pedido.estado = estado_activo
            pedido.save(update_fields=['estado'])
            for item in pedido.detallepedido_set.select_related('producto_id'):
                prod = Productos.objects.select_for_update().get(id=item.producto_id.id)
                prod.estado = 'de viaje'
                prod.save(update_fields=['estado'])

    messages.success(
        request, 'Viaje iniciado: pedidos activos y productos de viaje')
    return redirect('encargado:viajes_activos')


@group_required('Encargado')
def viajes_activos(request):
    """Lista viajes que tienen al menos un pedido en estado 'activo'."""
    viajes = Viaje.objects.filter(pedido__estado__estado='activo').distinct()

    # Preparar datos de pedidos por viaje
    viajes_data = []
    for v in viajes:
        pedidos = Pedido.objects.filter(viaje=v, estado__estado='activo').select_related(
            'cliente', 'cliente__comercio')
        viajes_data.append({
            'viaje': v,
            'pedidos': pedidos,
            'cantidad_pedidos': pedidos.count(),
        })

    return render(request, 'html/viajes/activos.html', {
        'viajes': viajes_data
    })


@group_required('Encargado')
def viajes_finalizados(request):
    """Lista viajes finalizados: aquellos sin pedidos 'activo' ni 'preparado' y con al menos uno 'entregado'."""
    viajes = (Viaje.objects
              .filter(pedido__estado__estado='entregado')
              .exclude(pedido__estado__estado__in=['activo', 'preparado'])
              .distinct())

    viajes_data = []
    for v in viajes:
        pedidos = (Pedido.objects
                   .filter(viaje=v, estado__estado='entregado')
                   .select_related('cliente__comercio'))
        viajes_data.append({
            'viaje': v,
            'pedidos': pedidos,
            'cantidad_pedidos': pedidos.count(),
        })

    return render(request, 'html/viajes/finalizados.html', {
        'viajes': viajes_data
    })


def get_chart(_request):
    chart = {}
    return JsonResponse(chart)
