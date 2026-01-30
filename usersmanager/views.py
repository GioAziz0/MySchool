from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import Ruolo


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Custom login view with role-based redirect.
    """
    if request.user.is_authenticated:
        return redirect('usersmanager:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Benvenuto, {user.get_full_name()}!')
            return redirect('usersmanager:dashboard')
        else:
            messages.error(request, 'Credenziali non valide.')

    return render(request, 'usersmanager/login.html')


@login_required
def logout_view(request):
    """
    Logout view.
    """
    logout(request)
    messages.info(request, 'Logout effettuato con successo.')
    return redirect('usersmanager:login')


@login_required
def dashboard_view(request):
    """
    Dashboard view that redirects based on user role.
    """
    user = request.user

    if user.is_superuser or (user.ruolo and user.ruolo.nome == Ruolo.ADMIN):
        return render(request, 'usersmanager/dashboard_admin.html', {
            'user': user,
            'permissions': user.get_all_permissions_list()
        })
    elif user.ruolo and user.ruolo.nome == Ruolo.INSEGNANTE:
        return render(request, 'usersmanager/dashboard_insegnante.html', {
            'user': user,
            'permissions': user.get_all_permissions_list()
        })
    elif user.ruolo and user.ruolo.nome == Ruolo.STUDENTE:
        return render(request, 'usersmanager/dashboard_studente.html', {
            'user': user,
            'permissions': user.get_all_permissions_list()
        })
    else:
        # Default dashboard for users without a role
        return render(request, 'usersmanager/dashboard_default.html', {
            'user': user,
            'permissions': user.get_all_permissions_list()
        })
