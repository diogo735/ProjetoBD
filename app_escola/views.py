from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
import psycopg2
from .utils import aluno_required, professor_required, funcionario_required

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



def obter_nome_id_user(email, user_type):
    with connection.cursor() as cursor:
        # Chamar a função SQL do banco de dados que você criou
        cursor.execute("SELECT * FROM get_user_info(%s, %s)", [email, user_type])
        result = cursor.fetchone()

        if result:
            user_id, first_name, last_name = result
            return {
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
            }
        return None

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
            cursor.execute(f"SELECT * FROM public.{user_type.lower()} WHERE email = %s", [email])
            user = cursor.fetchone()

            if user:
                # Extrair os nomes das colunas do cursor
                columns = [col[0] for col in cursor.description]
                # Mapear os valores da tupla para um dicionário
                user_dict = dict(zip(columns, user))

                # Verifica se a senha está correta
                if user_dict['password'] == password:
                    # Chamar a função para obter nome e ID do usuário diretamente do banco de dados
                    user_info = obter_nome_id_user(email, user_type)
                    if user_info:
                        # Armazenar informações na sessão
                        request.session['user_id'] = user_info['user_id']
                        request.session['user_name'] = f"{user_info['first_name']} {user_info['last_name']}"
                        request.session['user_type'] = user_type
 # Determinar qual avatar usar
                        if user_type.lower() == 'aluno':
                            request.session['user_avatar'] = 'images/aluno.png' if user_info['first_name'][-1].lower() != 'a' else 'images/aluna.png'
                        elif user_type.lower() == 'professor':
                            request.session['user_avatar'] = 'images/professor.png' if user_info['first_name'][-1].lower() != 'a' else 'images/professora.png'
                        elif user_type.lower() == 'funcionario':
                            request.session['user_avatar'] = 'images/funcionario.png' if user_info['first_name'][-1].lower() != 'a' else 'images/funcionaria.png'
                    return redirect('loading_page')
                else:
                    messages.error(request, 'Senha incorreta, tente novamente.')
            else:
                messages.error(request, 'Email não encontrado, tente novamente.')

    return render(request, 'pagina_login/home.html', {'db_status': status})



def loading_page(request):
    # return render(request, 'pagina_login/carregamento.html')

    user_type = request.session.get('user_type', None)

    # Redireciona para o dashboard correto com base no tipo de utilizador
    if user_type == 'Aluno':
        return redirect('dashboard_aluno')  # URL para o dashboard do aluno
    elif user_type == 'Professor':
        return redirect('dashboard_professor')  # URL para o dashboard do professor
    elif user_type == 'Funcionario':
        return redirect('dashboard_funcionario')  # URL para o dashboard do administrador
    else:
        # Caso não exista um tipo de utilizador válido, redireciona para a página de login
        messages.error(request, 'Sessão inválida. Por favor, faça login novamente.')
        return redirect('login')

# def pagina_principal(request):
#     user_type = request.session.get('user_type', None)
#     return render(request, 'pagina_principal/base_main.html', {'user_type': user_type})

@aluno_required
def dashboard_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard_aluno'})

@professor_required
def dashboard_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard_professor'})

@funcionario_required
def dashboard_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'dashboard_funcionario'})

@aluno_required
def horarios_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'horarios_aluno'})

@professor_required
def horarios_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'horarios_professor'})

@aluno_required
def professores_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'professores_aluno'})

@funcionario_required
def professores_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'professores_funcionario'})

@aluno_required
def avaliacoes_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'avaliacoes_aluno'})

@professor_required
def avaliacoes_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'avaliacoes_professor'})

@funcionario_required
def avaliacoes_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'avaliacoes_funcionario'})

@aluno_required
def pagamentos_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pagamentos_aluno'})

@funcionario_required
def pagamentos_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pagamentos_funcionario'})

@aluno_required
def matricula_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'matricula_aluno'})

@funcionario_required
def matricula_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'matricula_funcionario'})

@aluno_required
def gestao_escola_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola_aluno'})

@professor_required
def unidades_curriculares_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'unidades_curriculares_professor'})

@funcionario_required
def unidades_curriculares_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'unidades_curriculares_funcionario'})

@professor_required
def gestao_escola_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola_professor'})

@funcionario_required
def gestao_escola_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola_funcionario'})