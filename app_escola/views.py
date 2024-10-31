from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

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
            return redirect('pagina_principal')
        else:
            # Senão, exibe uma mensagem de erro
            messages.error(request, 'Credenciais inválidas, tente novamente.')

    return render(request, 'pagina_login/home.html', {'db_status': status})


def pagina_principal(request):
    return render(request, 'pagina_principal/main.html')
