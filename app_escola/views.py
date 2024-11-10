from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required


def home(request):
    try:
        # Tenta fazer uma consulta simples ao banco de dados
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")  # Consulta simples para verificar a conexão
        status = "OK"
    except Exception as e:
        # Se houver qualquer erro na conexão, define como "Not OK"
        status = "Not OK"

    # Renderiza o template home.html com o status da conexão
    return render(request, 'pagina_login/home.html', {'db_status': status})

def login_view(request):
    try:
        # Verifica a conexão com o banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status = "OK"
    except Exception as e:
        status = "Not OK"

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Verificar se as credenciais correspondem a um registro no banco de dados
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM public."Perfil_Utilizador" WHERE email = %s AND password = %s', [email, password])
            user = cursor.fetchone()

        if user:
            # Se o usuário foi encontrado, redireciona para a página principal
            return redirect('loading_page')

        else:
            # Senão, exibe uma mensagem de erro
            messages.error(request, 'Credenciais inválidas, tente novamente.')

    return render(request, 'pagina_login/home.html', {'db_status': status})

def loading_page(request):
    return render(request, 'pagina_login/carregamento.html')

def pagina_principal(request):
    # Renderiza o template base com o conteúdo do Dashboard como padrão
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard'})


def dashboard(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard'})


def calendario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'calendario'})

def pessoas(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pessoas'})

def aulas(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'aulas'})

def pagamentos(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pagamentos'})

def relatorios(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'relatorios'})

def gestao_escola(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola'})

