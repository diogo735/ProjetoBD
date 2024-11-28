from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
import psycopg2

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
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status = "OK"
    except Exception as e:
        status = "Not OK"

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        with connection.cursor() as cursor:
            # Executa a consulta para verificar se o email existe no banco de dados
            cursor.execute(f'SELECT * FROM public.{user_type.lower()} WHERE email = %s', [email])
            user = cursor.fetchone()

            if user:
                # Extrair os nomes das colunas do cursor
                columns = [col[0] for col in cursor.description]
                # Mapear os valores da tupla para um dicionário
                user_dict = dict(zip(columns, user))

                # Verifica se a senha está correta
                if user_dict['password'] == password:
                    request.session['user_type'] = user_type
                    return redirect('loading_page')
                else:
                    messages.error(request, 'Senha incorreta, tente novamente.')
            else:
                messages.error(request, 'Email não encontrado, tente novamente.')

    return render(request, 'pagina_login/home.html', {'db_status': status})


def loading_page(request):
    return render(request, 'pagina_login/carregamento.html')

def pagina_principal(request):
    
    
    # Renderiza o template base com o conteúdo do Dashboard como padrão
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard'})


def dashboard(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard'})


def horarios(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'horarios'})

def professores(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'professores'})

def avaliacoes(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'avaliacoes'})

def pagamentos(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pagamentos'})

def matricula(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'matricula'})

def gestao_escola(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola'})

