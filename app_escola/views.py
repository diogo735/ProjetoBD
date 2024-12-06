import json
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
import psycopg2
from .utils import aluno_required, professor_required, funcionario_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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

#@funcionario_required
#def unidades_curriculares_funcionario(request):
 #   return render(request, 'pagina_principal/main.html', {'default_content': 'unidades_curriculares_funcionario'})
@funcionario_required
def unidades_curriculares_funcionario(request):
    turnos = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM listar_turnos_ativos()")
        columns = [col[0] for col in cursor.description]
        turnos = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'pagina_principal/main.html', {
        'default_content': 'unidades_curriculares_funcionario',
        'turnos': turnos,
    })


@funcionario_required
def obter_horarios_turno(request, id_turno):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM listar_horarios_por_turno(%s)", [id_turno])
        columns = [col[0] for col in cursor.description]
        horarios = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return JsonResponse(horarios, safe=False)

@funcionario_required
def obter_cursos(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM listar_cursos()")  # Supondo que `listar_cursos` é a função do banco
        cursos = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]  # Pega os nomes das colunas
    cursos_formatados = [dict(zip(colunas, curso)) for curso in cursos]  # Formata os dados
    return JsonResponse(cursos_formatados, safe=False)  # Retorna como JSON

@csrf_exempt
def criar_turno(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
    """
    CALL p_turno_insert(
        %s::INTEGER,
        %s::VARCHAR,
        %s::SMALLINT,
        %s::VARCHAR,
        %s::VARCHAR,
        %s::INTEGER,
        %s::INTEGER
    )
    """,
    [
        data['id_curso'],
        data['nome_turno'],
        0,  # Estado (fixo por padrão)
        data['ano_turno'],
        data['semestre_turno'],
        data['vagas_turno'],
        data['vagas_turno']
    ]
)

            return JsonResponse({'success': True})
        except Exception as e:
            print('Erro ao criar turno:', e)  # Mostra o erro no terminal do servidor
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método inválido'})



def buscar_turnos(request):
    # Obtém os parâmetros da requisição
    curso_id = request.GET.get('curso')
    ano = request.GET.get('ano')
    semestre = request.GET.get('semestre')

    # Log dos parâmetros recebidos
    print(f"Parâmetros recebidos: curso_id={curso_id}, ano={ano}, semestre={semestre}")

    # Verifica se todos os parâmetros foram fornecidos
    if not (curso_id and ano and semestre):
        print("Parâmetros incompletos")
        return JsonResponse({"error": "Parâmetros incompletos"}, status=400)

    # Consulta SQL usando a função do banco de dados
    query = """
        SELECT * FROM obter_turnos_filtrados(%s, %s, %s)
    """
    
    try:
        with connection.cursor() as cursor:
            # Executa a consulta com os parâmetros fornecidos
            print("Executando a consulta SQL...")
            cursor.execute(query, [curso_id.strip(), ano.strip(), semestre.strip()])
            rows = cursor.fetchall()

            # Log dos resultados da consulta
            print(f"Resultados da consulta: {rows}")

        # Formata os resultados para enviar como JSON
        dados = []
        for row in rows:
             dados.append({
                "id_turno": row[0],
                "turno_nome": row[1],
                "vagas_disponiveis": row[2],
                "vagas_totais": row[3],  # Inclua a coluna vagas_totais aqui
                "ano": row[4],
                "semestre": row[5],
                 "id_curso": row[6],
                 "curso_nome": row[7],
                 "estado": row[8]
           })


        # Retorna os dados como JSON
        print(f"Dados enviados: {dados}")
        return JsonResponse(dados, safe=False)

    except Exception as e:
        print(f"Erro ao executar a consulta: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)









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



@professor_required
def gestao_escola_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola_professor'})

@funcionario_required
def gestao_escola_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'gestao_escola_funcionario'})