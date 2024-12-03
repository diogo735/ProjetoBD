from django.shortcuts import redirect
from django.contrib import messages

def aluno_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('user_type') == 'Aluno':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Você não tem permissão para acessar esta página.')
            return redirect('login')  # Redireciona para o login ou outra página de erro
    return wrapper

def professor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('user_type') == 'Professor':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Você não tem permissão para acessar esta página.')
            return redirect('login')
    return wrapper

def funcionario_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('user_type') == 'Funcionario':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Você não tem permissão para acessar esta página.')
            return redirect('login')
    return wrapper
