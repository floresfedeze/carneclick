from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib import messages


def register(request):
    if request.method == 'GET':
        return render(request, 'html/register.html')

    if request.POST['password'] != request.POST['password2']:
        return render(request, 'html/register.html', {
            'error': 'No coinciden las contraseñas'
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
