from django.shortcuts import render, redirect
from django.shortcuts import render
from django.http import JsonResponse
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

@funcionario_required
def alunos_funcionario(request):
    mensagem = None
    status = None
    alunos = []  # Lista para armazenar os alunos

    if request.method == 'POST':
        # Obter os dados enviados pelo formulário
        p_nome = request.POST.get('p_nome')
        u_nome = request.POST.get('u_nome')
        email = request.POST.get('email')
        password = request.POST.get('password')
        telefone = request.POST.get('telefone')
        localidade = request.POST.get('localidade')

        try:
            # Chamar o procedimento armazenado no banco de dados
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_aluno_insert(%s, %s, %s, %s, %s, %s)
                """, [
                    p_nome,      
                    u_nome,      
                    email,      
                    password,   
                    telefone,    
                    localidade   
                ])

            # Mensagem de sucesso
            mensagem = "Aluno criado com sucesso!"
            status = "success"
        except Exception as e:
            # Mensagem de erro
            mensagem = f"Erro ao criar aluno: {str(e)}"
            status = "error"

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM f_listar_alunos()")
            alunos = cursor.fetchall()  


        return render(request, 'pagina_principal/main.html', {
            'default_content': 'alunos_funcionario',
            'alunos': alunos,
            'mensagem': mensagem,
            'status': status,
        })

    # GET: Renderizar a página inicial
    return render(request, 'pagina_principal/main.html', {'default_content': 'alunos_funcionario'})


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