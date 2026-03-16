from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib import messages
from urllib.parse import urlencode
import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.core.mail import send_mail, BadHeaderError


def register(request):
    if request.method == 'GET':
        return render(request, 'html/register.html')

    password = request.POST['password']

    if password != request.POST['password2']:
        return render(request, 'html/register.html', {
            'error': 'No coinciden las contraseñas'
        })

    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        return render(request, 'html/register.html', {
            'error': 'La contraseña debe tener al menos 8 caracteres, incluido un número y una letra mayúscula.'
        })

    try:
        user = User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password'],
            email=request.POST['email'],
        )

        # 👉 asignar grupo CLIENTE
        grupo_cliente = Group.objects.get(name='Cliente_Pendiente')
        user.groups.add(grupo_cliente)

        login(request, user)
        return redirect("cliente:register_comercio")

    except IntegrityError:
        return render(request, 'html/register.html', {
            'error': 'Este usuario ya existe'
        })


def login_view(request):
    if request.method == 'GET':
        return render(request, 'html/login.html')

    user = authenticate(
        request,
        username=request.POST['usuario'],
        password=request.POST['contraseña']
    )

    if user is None:
        messages.error(
            request, "Usuario o contraseña incorrectos")
        return render(request, 'html/login.html')

    login(request, user)

    # 👉 redirección según grupo
    if user.groups.filter(name='Encargado').exists():
        return redirect('encargado:home')

    if user.groups.filter(name='Cliente').exists():
        return redirect('cliente:home')

    if user.groups.filter(name='Cliente_Pendiente').exists():
        logout(request)
        messages.warning(
            request, "Su registro está pendiente de aprobación por el encargado")

        return redirect('login_view')

    # fallback de seguridad
    return redirect('/')


@login_required(login_url='login_view')
def CerrarSesion(request):
    logout(request)
    return redirect('/')


def set_language(request):
    lang = request.GET.get('lang')
    if lang in ('en', 'es'):
        request.session['lang'] = lang
        messages.success(request, 'Idioma cambiado a {}.'.format(
            'English' if lang == 'en' else 'Español'))
    next_url = request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)


def serve_doc(request, doc_name):
    """Sirve PDFs estáticos que están en la raíz del proyecto.
    Mapear nombres lógicos a ficheros físicos.
    """
    mapping = {
        'condiciones': 'Condiciones_de_Servicio_Carneclick.pdf',
        'terminos': 'Terminos_y_Condiciones_de_Uso_Carneclick.pdf',
        'politica': 'Politica_de_Privacidad_Carneclick.pdf',
        'manual': 'Manual_de_usuario_Carneclick.pdf',
        'carpeta': 'Carneclick.pdf',
    }
    filename = mapping.get(doc_name)
    if not filename:
        raise Http404("Documento no encontrado")
    # Ahora los PDFs se encuentran dentro de la carpeta 'pdf' en la raíz del proyecto
    filepath = os.path.join(settings.BASE_DIR, 'pdf', filename)
    if not os.path.exists(filepath):
        raise Http404("Archivo no encontrado")
    response = FileResponse(open(filepath, 'rb'),
                            content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def contact_support(request):
    """Formulario de contacto para enviar email al soporte."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'Soporte CarneClick').strip()
        message = request.POST.get('message', '').strip()

        if not email or not message:
            messages.error(request, 'Por favor complete su correo y mensaje.')
            return render(request, 'html/contact_support.html', {'name': name, 'email': email, 'subject': subject, 'message': message})

        full_message = f"Desde: {name} <{email}>\n\n{message}"
        try:
            send_mail(subject, full_message, settings.DEFAULT_FROM_EMAIL, [
                      settings.EMAIL_HOST_USER])
            messages.success(
                request, 'Mensaje enviado correctamente. Responderemos a la brevedad.')
            return redirect('login_view')
        except BadHeaderError:
            messages.error(request, 'Encabezado inválido en el correo.')
        except Exception:
            messages.error(
                request, 'No se pudo enviar el correo. Intente más tarde.')

        return render(request, 'html/contact_support.html', {'name': name, 'email': email, 'subject': subject, 'message': message})

    return render(request, 'html/contact_support.html')
