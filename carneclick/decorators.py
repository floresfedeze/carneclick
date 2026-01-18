from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def group_required(group_name):
    """
    Decorador que requiere que el usuario esté autenticado y pertenezca a un grupo específico.

    Uso:
        @group_required('Cliente')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login_view')
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            else:
                return redirect('login_view')
        return wrapper
    return decorator
