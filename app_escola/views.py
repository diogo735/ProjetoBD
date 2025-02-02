import json
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import psycopg2
from .utils import aluno_required, professor_required, funcionario_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

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

TABLE_MAPPING = {
    'aluno': 'alunos',
    'professor': 'professores',
    'funcionario': 'funcionarios',
}

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

        table_name = TABLE_MAPPING.get(user_type.lower())

        if not table_name:
            messages.error(request, 'Tipo de utilizador inválido.')
            return render(request, 'pagina_login/home.html', {'db_status': status})


        with connection.cursor() as cursor:
            # Primeiro, verifica se o email existe na tabela correta
            cursor.execute(f"SELECT email FROM public.{table_name} WHERE email = %s", [email])

            email_check = cursor.fetchone()

            if email_check:  # Email existe
                # Agora, verifica se o email e a senha correspondem
                cursor.execute("SELECT id, p_nome, u_nome, email FROM public.check_login_credenciais(%s, %s, %s)", 
                               [email, password, user_type])
                user = cursor.fetchone()

                if user:  # Email e senha estão corretos
                    # Extrai os dados retornados pela função SQL
                    user_id, first_name, last_name, user_email = user

                    # Armazena as informações na sessão
                    request.session['user_id'] = user_id
                    request.session['user_name'] = f"{first_name} {last_name}"
                    request.session['user_type'] = user_type

                    # Define o avatar baseado no tipo de utilizador e no último caractere do nome
                    if user_type.lower() == 'aluno':
                        request.session['user_avatar'] = 'images/aluno.png' if first_name[-1].lower() != 'a' else 'images/aluna.png'
                    elif user_type.lower() == 'professor':
                        request.session['user_avatar'] = 'images/professor.png' if first_name[-1].lower() != 'a' else 'images/professora.png'
                    elif user_type.lower() == 'funcionario':
                        request.session['user_avatar'] = 'images/funcionario.png' if first_name[-1].lower() != 'a' else 'images/funcionaria.png'

                    # Redireciona para a página de carregamento
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
    # Obter o mês atual
    mes_atual = datetime.now().month
    
    # Determinar semestre atual
    if 9 <= mes_atual or mes_atual <= 2:  # Setembro a Fevereiro
        semestre_atual = '1ºSemestre'
    else:  # Março a Agosto
        semestre_atual = '2ºSemestre'
    
    # Consulta SQL para buscar turnos filtrados pelo semestre atual
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT semestre, ano, curso, nome_turno, vagas_totais 
            FROM diogo_vw_listar_turnos_por_curso
            WHERE semestre = %s
            ORDER BY curso, ano, nome_turno;
        """, [semestre_atual])
        
        colunas = [desc[0] for desc in cursor.description]
        turnos = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    
    # Renderizar o template com os dados do banco
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'unidades_curriculares_funcionario',
        'turnos': turnos,
    })



@funcionario_required
def obter_horarios_turno(request):
    turno_nome = request.GET.get('turno_nome')
    semestre = request.GET.get('semestre', '').replace(' ', '')  # Remove espaços extras
    ano = request.GET.get('ano', '').replace(' ', '')  # Remove espaços extras
    curso = request.GET.get('curso')

    print(f"Parâmetros recebidos: turno_nome={turno_nome}, semestre={semestre}, ano={ano}, curso={curso}")

    if not all([turno_nome, semestre, ano, curso]):
        return JsonResponse({'error': 'Parâmetros ausentes'}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM diogo_fn_obter_horarios_detalhados(%s, %s, %s, %s)
            """, [semestre, turno_nome, ano, curso])
            
            colunas = [col[0] for col in cursor.description]
            horarios = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        
        print(f"Dados retornados: {horarios}")
        return JsonResponse(horarios, safe=False)
    except Exception as e:
        print(f"Erro ao obter horários: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@funcionario_required
def obter_cursos(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM diogo_f_listar_cursos()")  # Supondo que `listar_cursos` é a função do banco
        cursos = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]  # Pega os nomes das colunas
    cursos_formatados = [dict(zip(colunas, curso)) for curso in cursos]  # Formata os dados
    print("Cursos carregados com sucesso:", cursos_formatados)
    return JsonResponse(cursos_formatados, safe=False)  # Retorna como JSON

@funcionario_required
def obter_anos(request):
    """
    View para obter os anos disponíveis usando a função SQL diogo_f_listar_anos()
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM diogo_f_listar_anos();")
        columns = [col[0] for col in cursor.description]
        anos = [dict(zip(columns, row)) for row in cursor.fetchall()]
    print("Anos carregados com sucesso:", anos)
    return JsonResponse(anos, safe=False)


@funcionario_required
def obter_semestres(request):
    """
    View para obter os semestres disponíveis usando a função SQL diogo_f_listar_semestres()
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM diogo_f_listar_semestres();")
        columns = [col[0] for col in cursor.description]
        semestres = [dict(zip(columns, row)) for row in cursor.fetchall()]
    print("Semestres carregados com sucesso:", semestres)
    return JsonResponse(semestres, safe=False)

@funcionario_required
def obter_nomes_turnos(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT turno_nome FROM turnos;")
        turnos = [row[0] for row in cursor.fetchall()]
    return JsonResponse(turnos, safe=False)

@funcionario_required
def obter_ucs(request):
    # Obter valores diretamente da requisição
    curso = request.GET.get('curso', '').strip()
    ano = request.GET.get('ano', '').strip()
    semestre = request.GET.get('semestre', '').strip()

    # Validar se todos os parâmetros foram fornecidos
    if not curso or not ano or not semestre:
        return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM diogo_f_listar_ucs_por_ano_semestre_curso(%s, %s, %s)
            """, [ano, semestre, curso])
            columns = [col[0] for col in cursor.description]
            ucs = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return JsonResponse(ucs, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




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
                        %s::INTEGER,
                        %s::INTEGER,
                        %s::VARCHAR,
                        %s::INTEGER
                    )
                    """,
                    [
                        int(data['id_uc']),
                        int(data['ano_turno']),
                        int(data['semestre_turno']),
                        data['nome_turno'],
                        int(data['vagas_turno'])
                    ]
                )
            return JsonResponse({'success': True, 'message': '✅ Turno criado com sucesso!'})
        except Exception as e:
            error_message = str(e)
            if 'Turno já existe' in error_message:
                return JsonResponse({'success': False, 'error': '❌ Turno já existe com os mesmos parâmetros!'})
            return JsonResponse({'success': False, 'error': '❌ Erro desconhecido: ' + error_message})
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
        SELECT id_turno, turno_nome, vagas_totais, vagas_restantes, nome_uc 
        FROM diogo_f_obter_turnos_filtrados(%s, %s, %s)
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
                "vagas_totais": row[2],
                "vagas_restantes": row[3],
                "nome_uc": row[4]
            })


        # Retorna os dados como JSON
        print(f"Dados enviados: {dados}")
        return JsonResponse(dados, safe=False)

    except Exception as e:
        print(f"Erro ao executar a consulta: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

def atualizar_turno_view(request):
    if request.method == "POST":
        try:
            # Obter os dados do corpo da requisição JSON
            data = json.loads(request.body)
            turno_id = data.get("turno_id")
            nome_turno = data.get("nome_turno")
            vagas_totais = data.get("vagas_totais")

            # Validação dos dados
            if not all([turno_id, nome_turno, vagas_totais]):
                return JsonResponse({"success": False, "error": "Todos os campos são obrigatórios."}, status=400)

            # Chamar o procedimento armazenado no PostgreSQL
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_turno_update(%s, %s, %s)
                """, [turno_id, nome_turno, vagas_totais])
            
            return JsonResponse({"success": True, "message": "Turno atualizado com sucesso!"})

        except Exception as e:
            print(f"Erro ao atualizar turno: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método inválido"}, status=405)

def obter_detalhes_turno(request, turno_id):
    # Verificar se a solicitação é do tipo GET
    if request.method == 'GET':
        try:
            with connection.cursor() as cursor:
                # Executar a função SQL para buscar os detalhes do turno específico
                cursor.execute("""
                    SELECT * FROM diogo_f_obter_detalhes_turno_especifico(%s)
                """, [turno_id])
                
                # Recuperar o resultado da consulta
                row = cursor.fetchone()
                
                # Se nenhum resultado for encontrado
                if not row:
                    return JsonResponse({'error': 'Turno não encontrado'}, status=404)

                # Preparar os dados para serem enviados em formato JSON
                turno_data = {
                    'id_turno': row[0],
                    'turno_nome': row[1],
                    'vagas_totais': row[2],
                    'vagas_ocupadas': row[3]
                }
                
                # Retornar os dados em formato JSON
                return JsonResponse(turno_data, safe=False)

        except Exception as e:
            # Retornar erro se algo der errado
            print(f"Erro ao obter detalhes do turno: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    # Se não for um método GET, retornamos um erro
    return JsonResponse({'error': 'Método não permitido'}, status=405)

def obter_alunos_turno(request, id_turno):
    """
    Retorna uma lista de alunos inscritos em um turno específico.
    """
    try:
        with connection.cursor() as cursor:
            # Chama a função SQL para obter alunos do turno
            cursor.execute("""
                SELECT * FROM diogo_f_obter_alunos_por_turno(%s)
            """, [id_turno])
            
            rows = cursor.fetchall()
            
        # Formata os dados para JSON
        alunos = [
            {"n_meca": row[0], "p_nome": row[1], "u_nome": row[2]}
            for row in rows
        ]
        
        return JsonResponse({"success": True, "alunos": alunos})
    
    except Exception as e:
        print(f"Erro ao obter alunos do turno: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def remover_alunos_turno(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            alunos = data.get('alunos', [])
            turno_id = data.get('turno_id')

            print(f"Alunos recebidos na VIEWWW: {alunos}, Turno ID: {turno_id}")  # Log para depuração

            if not alunos or not turno_id:
                return JsonResponse({"success": False, "error": "IDs dos alunos ou turno não fornecidos."})

            with connection.cursor() as cursor:
                for aluno in alunos:
                    cursor.execute("""
                        CALL diogo_p_remover_matricula_turno(%s, %s)
                    """, [aluno, turno_id])

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Erro: {e}")  # Log de erro no servidor
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido"})

def adicionar_aluno_turno(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            turno_id = data.get('turno_id')
            aluno = data.get('aluno')

            if not turno_id or not aluno:
                return JsonResponse({'success': False, 'error': 'Dados inválidos.'}, status=400)

            n_meca = aluno.get('n_meca')

            if not n_meca:
                return JsonResponse({'success': False, 'error': 'Dados do aluno incompletos.'}, status=400)

            # Verificar se o aluno pode ser inscrito no turno chamando a função SQL
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT diogo_verificar_se_pode_matricular_turno(%s, %s);
                """, [n_meca, turno_id])
                resultado = cursor.fetchone()

            # Se a função retornar algo diferente de sucesso, interromper o processo
            if resultado and 'Sucesso' not in resultado[0]:
                return JsonResponse({'success': False, 'error': resultado[0]}, status=400)

            # Extrair o ID da matrícula do resultado da função
            try:
                id_matricula = int(resultado[0].split('ID da matrícula: ')[1])
            except (IndexError, ValueError):
                return JsonResponse({'success': False, 'error': 'Erro ao extrair o ID da matrícula.'}, status=500)

            # Chamar o procedimento para adicionar o aluno ao turno
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_matriculas_turno_insert(%s, %s);
                """, [id_matricula, turno_id])

            return JsonResponse({'success': True, 'message': 'Aluno adicionado com sucesso!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método inválido.'}, status=405)

def verificar_eliminar_turno(request):
    if request.method == "POST":
        try:
            # Obter o ID do turno a partir do POST
            turno_id = request.POST.get("turno_id")

            if not turno_id:
                return JsonResponse({"success": False, "error": "ID do turno não fornecido."})

            # Verificar se o turno pode ser eliminado usando a função no PostgreSQL
            with connection.cursor() as cursor:
                cursor.execute("SELECT diogo_verificar_eliminar_turno(%s)", [turno_id])
                result = cursor.fetchone()

                # Validar o resultado da consulta
                if not result or len(result) < 1:
                    return JsonResponse({"success": False, "error": "Erro na verificação ou turno não encontrado."})

                # Extrair a mensagem retornada pela função SQL
                mensagem = result[0]  # Apenas a mensagem retornada pela função

                # Verificar se pode eliminar (com base na mensagem retornada)
                pode_eliminar = "Sucesso" in mensagem

                # Retornar as informações necessárias para o modal
                return JsonResponse({
                    "success": True,
                    "posso_eliminar": pode_eliminar,
                    "mensagem": mensagem
                })

        except Exception as e:
            return JsonResponse({"success": False, "error": f"Erro no servidor: {str(e)}"})

    return JsonResponse({"success": False, "error": "Método inválido."})



def eliminar_turno(request):
    if request.method == "POST":
        try:
            # Obter o ID do turno a partir do POST
            turno_id = request.POST.get("turno_id")
            
            if not turno_id:
                return JsonResponse({"success": False, "error": "ID do turno não fornecido."})

            # Garantir que o ID do turno seja um número inteiro válido
            try:
                turno_id = int(turno_id)
            except ValueError:
                return JsonResponse({"success": False, "error": "ID do turno inválido."})

            # Executar o procedimento armazenado no banco de dados
            with connection.cursor() as cursor:
                cursor.execute("CALL p_turno_delete(%s)", [turno_id])

            # Retornar sucesso
            return JsonResponse({"success": True, "message": f"Turno com ID {turno_id} eliminado com sucesso."})

        except Exception as e:
            # Retornar mensagem de erro detalhada em caso de exceção
            return JsonResponse({"success": False, "error": f"Erro ao eliminar o turno: {str(e)}"})

    return JsonResponse({"success": False, "error": "Método inválido"})


def obter_turnos_sem_horarios(request):
    if request.method == "GET":
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM diogo_obter_turnos_sem_horarios()")
                resultados = cursor.fetchall()
                turnos = [
                    {
                        "id_turno": row[0],
                        "turno_nome": row[1],
                        "id_uc": row[2],
                        "id_semestre": row[3],
                        "id_ano": row[4]
                    }
                    for row in resultados
                ]
            return JsonResponse({"success": True, "turnos": turnos})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método inválido"})

def espacos_disponiveis(request):
    if request.method == "POST":
        try:
            data = request.POST
            dia_semana = data.get("dia_semana")
            hora_inicio = data.get("hora_inicio")
            hora_fim = data.get("hora_fim")

            if not dia_semana or not hora_inicio or not hora_fim:
                return JsonResponse({"success": False, "error": "Parâmetros insuficientes."})

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM diogo_obter_espacos_disponiveis(%s, %s, %s)
                """, [dia_semana, hora_inicio, hora_fim])
                resultados = cursor.fetchall()

            espacos = [
                {"id_espaco": row[0], "numero_sala": row[1]}
                for row in resultados
            ]
            return JsonResponse({"success": True, "espacos": espacos})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método inválido"})

def adicionar_horario(request):
    if request.method == "POST":
        try:
            # Carregar os dados enviados pelo frontend
            data = json.loads(request.body)
            turno_id = data.get("turno_id")
            dia_semana = data.get("dia_semana")
            hora_inicio = data.get("hora_inicio")
            hora_fim = data.get("hora_fim")
            espaco_id = data.get("espaco_id")

            # Validar os dados recebidos
            if not turno_id or not dia_semana or not hora_inicio or not hora_fim or not espaco_id:
                return JsonResponse({"success": False, "error": "Todos os campos são obrigatórios."})

            # Chamar o procedimento armazenado no banco de dados
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_horario_insert(%s, %s, %s, %s, %s);
                """, [turno_id, espaco_id, dia_semana, hora_inicio, hora_fim])

            return JsonResponse({"success": True, "message": "Horário adicionado com sucesso!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método inválido."})


@funcionario_required
def obter_turnos_nomes(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT turno_nome
                FROM turnos
                ORDER BY turno_nome
            """)  # Ajuste conforme sua tabela
            turnos = [row[0] for row in cursor.fetchall()]
        return JsonResponse({"success": True, "turnos": turnos})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@funcionario_required
def pesquisar_horarios_filtrados(request):
    curso_id = request.GET.get('curso_id')
    ano = request.GET.get('ano')
    semestre = request.GET.get('semestre')
    turno = request.GET.get('turno')

    # Validação dos parâmetros
    if not curso_id or not ano or not semestre or not turno:
        return JsonResponse({"success": False, "error": "Parâmetros inválidos."}, status=400)

    try:
        with connection.cursor() as cursor:
            # Chamada da função SQL
            query = """
                SELECT * 
                FROM diogo_obter_horarios_filtrados_pesquisa(%s, %s, %s, %s)
            """
            cursor.execute(query, [ano, semestre, curso_id, turno])
            horarios = cursor.fetchall()

            # Obter os nomes das colunas
            colunas = [desc[0] for desc in cursor.description]

            # Formatar os resultados como uma lista de dicionários
            horarios_formatados = [dict(zip(colunas, horario)) for horario in horarios]

        return JsonResponse({"success": True, "data": horarios_formatados}, safe=False)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def obter_horario_detalhes(request, horario_id):
    try:
        with connection.cursor() as cursor:
            # Chamar a função do banco de dados
            cursor.execute("SELECT * FROM diogo_obter_dados_horario_especifico(%s)", [horario_id])
            result = cursor.fetchone()

            # Verifica se o horário foi encontrado
            if result:
                colunas = [desc[0] for desc in cursor.description]
                horario = dict(zip(colunas, result))
                return JsonResponse({"success": True, "horario": horario})
            else:
                return JsonResponse({"success": False, "error": "Horário não encontrado."}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

def atualizar_horario(request, id_horario):
    if request.method == 'PUT':
        try:
            # Obtém os dados enviados no corpo da requisição
            data = json.loads(request.body)
            dia_semana = data.get('dia_semana')
            hora_inicio = data.get('hora_inicio')
            hora_fim = data.get('hora_fim')

            # Valida os dados
            if not all([dia_semana, hora_inicio, hora_fim]):
                return JsonResponse({'success': False, 'error': 'Parâmetros inválidos ou incompletos.'}, status=400)

            # Log dos parâmetros para depuração
            print(f"Atualizando horário: id_horario={id_horario}, dia_semana={dia_semana}, hora_inicio={hora_inicio}, hora_fim={hora_fim}")

            # Chama o PROCEDIMENTO SQL para verificar e atualizar o horário
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL diogo_verificar_e_atualizar_horario(%s, %s, %s, %s)
                """, [id_horario, dia_semana, hora_inicio, hora_fim])

            return JsonResponse({'success': True, 'message': 'Horário atualizado com sucesso!'})
        except Exception as e:
            print(f"Erro ao atualizar horário: {str(e)}")  # Log para depuração
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)

def remover_horario(request, id_horario):
    if request.method == 'DELETE':
        try:
            # Chama o procedimento no banco de dados
            with connection.cursor() as cursor:
                cursor.execute("CALL p_horario_delete(%s)", [int(id_horario)])


            return JsonResponse({'success': True, 'message': f'Horário com ID {id_horario} removido com sucesso!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)


def obter_id_curso(request, nome_curso):
    if request.method == "GET":
        try:
            with connection.cursor() as cursor:
                # Chamar a função SQL para buscar o ID do curso
                cursor.execute("""
                    SELECT obter_id_curso(%s)
                """, [nome_curso])
                resultado = cursor.fetchone()
            
            # Verificar se o curso foi encontrado
            if resultado:
                return JsonResponse({"success": True, "curso_id": resultado[0]})
            else:
                return JsonResponse({"success": False, "error": "Curso não encontrado."}, status=404)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método inválido."}, status=405)

def pesquisar_horarios(request):
    if request.method == "GET":
        curso_id = request.GET.get('curso_id')  # Obtém o ID do curso
        ano = request.GET.get('ano')           # Obtém o ano
        semestre = request.GET.get('semestre') # Obtém o semestre

        # Valida se todos os parâmetros foram fornecidos
        if not curso_id or not ano or not semestre:
            return JsonResponse({"success": False, "error": "Parâmetros inválidos."}, status=400)

        try:
            # Executa a função do banco de dados
            with connection.cursor() as cursor:
                query = """
                    SELECT * 
                    FROM obter_turnos_com_horarios(%s, %s, %s)
                """
                cursor.execute(query, [curso_id, ano, semestre])
                turnos = cursor.fetchall()

                # Obtém os nomes das colunas da função
                colunas = [desc[0] for desc in cursor.description]

                # Formata os resultados como uma lista de dicionários
                turnos_formatados = [dict(zip(colunas, turno)) for turno in turnos]

            return JsonResponse({"success": True, "data": turnos_formatados}, safe=False)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método inválido."}, status=405)

def obter_horarios_e_ucs(request, turno_id, curso_id, ano, semestre):
    if request.method == "GET":
        try:
            with connection.cursor() as cursor:
                # Chama a função listar_horarios_completo_turno
                cursor.execute("""
                    SELECT * FROM listar_horarios_completo_turno(%s)
                """, [turno_id])
                horarios = cursor.fetchall()
                colunas_horarios = [desc[0] for desc in cursor.description]  # Salva após o primeiro fetch
                
                # Chama a função listar_ucs_por_curso_ano_semestre
                cursor.execute("""
                    SELECT * FROM listar_ucs_por_curso_ano_semestre(%s, %s, %s)
                """, [curso_id, ano, semestre])
                ucs_disponiveis = cursor.fetchall()
                colunas_ucs = [desc[0] for desc in cursor.description]  # Salva após o segundo fetch

                # Formata os resultados como listas de dicionários
                horarios_formatados = [dict(zip(colunas_horarios, horario)) for horario in horarios]
                ucs_formatadas = [dict(zip(colunas_ucs, uc)) for uc in ucs_disponiveis]

            return JsonResponse({
                "success": True,
                "horarios": horarios_formatados,
                "ucs_disponiveis": ucs_formatadas
            }, safe=False)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Método inválido"}, status=405)


@csrf_exempt
def editar_horario(request, id_horario):
    if request.method == 'PUT':
        try:
            # Parse o corpo da requisição
            data = json.loads(request.body)
            
            # Extrair os parâmetros do corpo da requisição
            dia_semana = data.get('dia_semana')
            hora_inicio = data.get('hora_inicio')
            hora_fim = data.get('hora_fim')

            # Log dos dados recebidos
            print(f"Dados recebidos: id_horario={id_horario}, dia_semana={dia_semana}, hora_inicio={hora_inicio}, hora_fim={hora_fim}")

            # Verificar se os parâmetros obrigatórios estão presentes
            if not dia_semana or not hora_inicio or not hora_fim:
                print("Erro: Parâmetros inválidos ou ausentes.")
                return JsonResponse({'success': False, 'error': 'Parâmetros inválidos ou ausentes.'}, status=400)

            # Chamar a função PostgreSQL `diogo_atualizar_horario`
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT diogo_atualizar_horario(%s, %s, %s, %s)",
                    [id_horario, dia_semana, hora_inicio, hora_fim]
                )

            return JsonResponse({'success': True, 'message': 'Horário atualizado com sucesso.'})

        except Exception as e:
            # Log do erro
            print(f"Erro ao atualizar horário: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)



def carregar_professor_horario(request):
    # Verifica se o usuário está logado e é professor
    user_id = request.session.get('user_id')
    
    try:
        # Consulta os horários do professor logado usando a função do banco de dados
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM diogo_f_obter_horarios_completo_professor(%s)
            """, [user_id])
            
            horarios = cursor.fetchall()

        # Converte os resultados para um formato JSON
        horarios_data = [
            {
                'id_turno': horario[0],
                'turno_nome': horario[1],
                'nome_uc': horario[2],
                'nome_semestre': horario[3],
                'nome_ano': horario[4],
                'espaco': horario[5],
                'dia_semana': horario[6],
                'hora_inicio': str(horario[7]),
                'hora_fim': str(horario[8])
            }
            for horario in horarios
        ]

        return JsonResponse(horarios_data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)













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
        cursor.execute("SELECT * FROM f_listar_alunos()") ##call procedure here
        alunos = cursor.fetchall()  


    return render(request, 'pagina_principal/main.html', {
        'default_content': 'alunos_funcionario',
        'alunos': alunos,
        'mensagem': mensagem,
        'status': status,
    })

@funcionario_required
def aluno_delete(request, id_aluno):
    mensagem = None
    status = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("CALL p_aluno_delete(%s);", [id_aluno])

        mensagem = "Aluno removido com sucesso!"
        status = "success"
    except Exception as e:
        mensagem = f"Erro ao remover aluno: {str(e)}"
        status = "error"

    return redirect('alunos_funcionario')  

@funcionario_required
def aluno_editar(request, id_aluno):
    mensagem = None
    status = None

    if request.method == 'POST':
        # Capturar os dados enviados pelo formulário
        p_nome = request.POST.get('p_nome')
        u_nome = request.POST.get('u_nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        localidade = request.POST.get('localidade')

        try:
            # Atualizar os dados usando o procedimento armazenado
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_aluno_update(%s, %s, %s, %s, %s, %s);
                """, [id_aluno, p_nome, u_nome, email, telefone, localidade])

            mensagem = "Aluno atualizado com sucesso!"
            status = "success"
        except Exception as e:
            mensagem = f"Erro ao atualizar aluno: {str(e)}"
            status = "error"

    return redirect('alunos_funcionario')


@funcionario_required
def professores_funcionario(request):
    mensagem = None
    status = None
    professores = []  # Lista para armazenar os professores

    if request.method == 'POST':
        # Obter os dados enviados pelo formulário
        p_nome = request.POST.get('p_nome')
        u_nome = request.POST.get('u_nome')
        email = request.POST.get('email')
        password = request.POST.get('password')
        telefone = request.POST.get('telefone')
        localidade = request.POST.get('localidade')
        
                 # Debug: Verifique os valores capturados
        print("Dados recebidos do formulário:")
        print(f"Nome: {p_nome}, Sobrenome: {u_nome}, Email: {email}, Telefone: {telefone}, Localidade: {localidade}")

        try:
            # Chamar o procedimento armazenado no banco de dados
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_professor_insert(%s, %s, %s, %s, %s, %s)
                """, [
                    p_nome,
                    u_nome,
                    email,
                    password,
                    telefone,
                    localidade
                ])


            # Mensagem de sucesso
            mensagem = "Professor criado com sucesso!"
            status = "success"
        except Exception as e:
            # Mensagem de erro
            mensagem = f"Erro ao criar professor: {str(e)}"
            status = "error"

    # Recuperar lista de professores usando a função f_listar_professores
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM f_listar_professores()")
        professores = cursor.fetchall()

    return render(request, 'pagina_principal/main.html', {
        'default_content': 'professores_funcionario',
        'professores': professores,
        'mensagem': mensagem,
        'status': status,
    })

@funcionario_required
def professores_nao_atribuidos(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM diogo_f_listar_professores_nao_atribuidos();")
        
        colunas = [desc[0] for desc in cursor.description]
        professores = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    return JsonResponse(professores, safe=False)

@funcionario_required
def professores_atribuidos(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM diogo_f_listar_professores_atribuidos();")
        colunas = [desc[0] for desc in cursor.description]
        professores = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    return JsonResponse(professores, safe=False)


@funcionario_required
def atribuir_uc_professor(request, id_professor):
    print("Entrou na view atribuir_uc_professor")  

    if request.method == 'POST':
        print("Método POST detectado")  

        # Captura dos dados do formulário
        id_unidade_curricular = request.POST.get('unidade_curricular')
        id_turno = request.POST.get('turno')
        print(f"Dados recebidos - Professor: {id_professor}, UC: {id_unidade_curricular}, Turno: {id_turno}")  

        # Validação dos campos
        if not (id_professor and id_unidade_curricular and id_turno):
            messages.error(request, "Todos os campos são obrigatórios.")
            print("Campos obrigatórios ausentes!")  
            return redirect(reverse('atribuir_uc_professor', args=[id_professor]))

        try:
            # Chamada da procedure no banco
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_atribuir_uc_professor(%s, %s, %s);
                """, [id_professor, id_unidade_curricular, id_turno])
            print("Procedure executada com sucesso!")  # Log 5

            messages.success(request, "Unidade Curricular atribuída com sucesso ao professor!")
            return redirect(reverse('atribuir_uc_professor', args=[id_professor]))

        except Exception as e:
            print(f"Erro ao atribuir UC: {e}")  # Log 6
            messages.error(request, f"Ocorreu um erro: {e}")
            return redirect(reverse('atribuir_uc_professor', args=[id_professor]))

    print("Entrando na busca de dados para dropdowns")  # Log 7
    with connection.cursor() as cursor:
        # Buscar Unidades Curriculares
        cursor.execute("SELECT ID_UC, Nome FROM Unidades_Curriculares")
        unidades_curriculares = [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]
        # unidades_curriculares = cursor.fetchall()
        print("Unidades Curriculares:", unidades_curriculares)  # Log 8

        # Buscar Turnos
        cursor.execute("SELECT ID_Turno, Turno_Nome FROM Turnos")
        #turnos = [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]
        turnos = cursor.fetchall()
        print("Turnos:", turnos)  # Log 9

        cursor.execute("SELECT * FROM f_listar_professores()")
        professores = cursor.fetchall()

    print("Renderizando template com dados")  # Log 12
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'professores_funcionario',
        'unidades_curriculares': unidades_curriculares,
        'turnos': turnos,
        'professores': professores
    })

def listar_unidades_curriculares(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM diogo_f_listar_unidades_curriculares()")
            unidades = cursor.fetchall()

        unidades_list = [{"id_uc": row[0], "nome": row[1]} for row in unidades]

        return JsonResponse(unidades_list, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def listar_turnos_por_uc(request, id_uc):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM diogo_f_listar_turnos_por_uc(%s)", [id_uc])
            turnos = cursor.fetchall()

        turnos_list = [{"id_turno": row[0], "turno_nome": row[1]} for row in turnos]

        print(f"Turnos para UC {id_uc}: {turnos_list}")  # 🔹 Debug no terminal

        return JsonResponse(turnos_list, safe=False)
    except Exception as e:
        print(f"Erro na view: {e}")
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def registrar_professor_turno(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Recebendo dados no formato JSON
            id_professor = data.get("id_professor")
            unidades_curriculares = data.get("unidades_curriculares", [])  # Lista de UCs
            turnos = data.get("turnos", [])  # Lista de Turnos

            # Verifica se há pelo menos uma UC e um turno correspondente
            if not id_professor or not unidades_curriculares or not turnos:
                return JsonResponse({"success": False, "error": "Dados incompletos"})

            if len(unidades_curriculares) != len(turnos):
                return JsonResponse({"success": False, "error": "Cada UC deve ter um turno correspondente"})

            # Executar a procedure para cada UC-Turno
            with connection.cursor() as cursor:
                for id_uc, id_turno in zip(unidades_curriculares, turnos):
                    cursor.execute(
                        "CALL p_atribuir_uc_professor(%s, %s, %s);",
                        [id_professor, id_uc, id_turno]
                    )

            return JsonResponse({"success": True})
        
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Erro ao processar JSON"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido"})


def remover_atribuicao_uc_professor(request):
    if request.method == "POST":
        id_professor = request.POST.get("id_professor")
        nome_uc = request.POST.get("nome_uc")

        if not id_professor or not nome_uc:
            return JsonResponse({"error": "Parâmetros inválidos"}, status=400)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT diogo_f_remover_atribuicao_uc_professor(%s, %s);", [id_professor, nome_uc])

            return JsonResponse({"success": f"Atribuição da UC '{nome_uc}' removida com sucesso para o professor {id_professor}!"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Método não permitido"}, status=405)




@funcionario_required
def professor_delete(request, id_professor):
    mensagem = None
    status = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("CALL p_professor_delete(%s);", [id_professor])

        mensagem = "Professor removido com sucesso!"
        status = "success"
    except Exception as e:
        mensagem = f"Erro ao remover professor: {str(e)}"
        status = "error"

    return redirect('professores_funcionario')  


@funcionario_required
def professor_editar(request, id_professor):
    mensagem = None
    status = None

    if request.method == 'POST':
        # Capturar os dados enviados pelo formulário
        p_nome = request.POST.get('p_nome')
        u_nome = request.POST.get('u_nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        localidade = request.POST.get('localidade')

        try:
            # Atualizar os dados usando o procedimento armazenado
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_professor_update(%s, %s, %s, %s, %s, %s);
                """, [id_professor, p_nome, u_nome, email, telefone, localidade])

            mensagem = "Professor atualizado com sucesso!"
            status = "success"
        except Exception as e:
            mensagem = f"Erro ao atualizar professor: {str(e)}"
            status = "error"

    return redirect('professores_funcionario')

@aluno_required
def professores_aluno(request):
    # Obtém o ID do aluno logado
    id_aluno = request.session.get('user_id')

    try:
        # Buscar ID do Curso
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ID_Curso 
                FROM Matriculas 
                WHERE ID_Aluno = %s 
                LIMIT 1;
            """, [id_aluno])
            curso_result = cursor.fetchone()

        if not curso_result:
            messages.error(request, 'Curso não encontrado para este aluno.')
            return render(request, 'pagina_principal/main.html', {'default_content': 'professores_aluno'})

        id_curso = curso_result[0]

        # Buscar os Professores usando Função SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * 
                FROM f_professores_curso_aluno(%s, %s);
            """, [id_curso, id_aluno])
            professores = [
                {
                    'nome': row[1],
                    'unidade_curricular': row[2],
                    'email': row[3],
                    'telefone': row[4]
                }
                for row in cursor.fetchall()
            ]

            
    except Exception as e:
        print(f"Erro ao carregar professores: {e}")
        messages.error(request, f"Ocorreu um erro: {str(e)}")
        return render(request, 'pagina_principal/main.html', {'default_content': 'professores_aluno'})

    # Renderizar a página com os professores encontrados
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'professores_aluno',
        'professores': professores,
    })

#Pagamentos
#Listar os pagamentos em falta do aluno logado na aplicação
def pagamentos_em_falta_alunos(request):
    mensagem_pendentes = None
    mensagem_historico = None
    status_pendentes = None
    status_historico = None
    pagamentos_pendentes = []
    historico_pagamentos = []
    pagamentos = []

    try:
        # Verifica se o usuário está logado
        user_id = request.session.get('user_id')
       
        # Buscar os pagamentos pendentes do usuário logado
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM public.f_pagamentos_em_falta_alunos(%s)
            """, [user_id])
            pagamentos_pendentes = [
                {
                    'descricao': pagamento[0],
                    'valor': pagamento[1],
                    'multa': pagamento[4],
                    'data_vencimento': pagamento[2],
                    'estado': pagamento[3]
                }
                for pagamento in cursor.fetchall()
            ]


        for pagamento in pagamentos:
            pagamento['total'] = round(float(pagamento['valor']) + float(pagamento['multa']), 2)

        # Buscar o histórico de pagamentos do usuário logado
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM public.f_pagamentos_historico_pagamentos_alunos(%s)
            """, [user_id])
            historico_pagamentos = [
                {
                    'descricao': pagamento[0],
                    'valor': pagamento[1],
                    'multa': pagamento[4],
                    'data_vencimento': pagamento[2],
                    'estado': pagamento[3]
                }
                for pagamento in cursor.fetchall()
            ]

        mensagem_pendentes = "Pagamentos pendentes carregados com sucesso."
        status_pendentes = "success"
        mensagem_historico = "Histórico de pagamentos carregado com sucesso."
        status_historico = "success"

    except Exception as e:
        # Mensagens de erro
        mensagem_pendentes = f"Erro ao carregar pagamentos pendentes: {str(e)}"
        status_pendentes = "error"
        mensagem_historico = f"Erro ao carregar histórico de pagamentos: {str(e)}"
        status_historico = "error"

    # Renderizar a página com os dados das duas tabs
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'pagamentos_aluno',
        'pagamentos_pendentes': pagamentos_pendentes,
        'historico_pagamentos': historico_pagamentos,
        'mensagem_pendentes': mensagem_pendentes,
        'status_pendentes': status_pendentes,
        'mensagem_historico': mensagem_historico,
        'status_historico': status_historico,
        'pagamentos': pagamentos,
    })


def funcionario_listar_pagamentos(request):
    mensagem_todos_pagamentos = None
    status_todos_pagamentos = None
    todos_pagamentos = []

    try:
        # Chamar a função SQL para listar todos os pagamentos
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM public.f_funcionario_listar_pagamentos();
            """)
            todos_pagamentos = [
                {
                    'id_pagamento': pagamento[0],
                    'nome_aluno': pagamento[1],
                    'descricao': pagamento[2],
                    'valor': pagamento[3],
                    'data_vencimento': pagamento[4],
                    'estado': pagamento[5],
                    'multa': pagamento[6]
                }
                for pagamento in cursor.fetchall()
            ]

        mensagem_todos_pagamentos = "Todos os pagamentos carregados com sucesso."
        status_todos_pagamentos = "success"

    except Exception as e:
        # Mensagem de erro
        mensagem_todos_pagamentos = f"Erro ao carregar os pagamentos: {str(e)}"
        status_todos_pagamentos = "error"

    # Renderizar a página com os dados
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'pagamentos_funcionario',
        'todos_pagamentos': todos_pagamentos,
        'mensagem_todos_pagamentos': mensagem_todos_pagamentos,
        'status_todos_pagamentos': status_todos_pagamentos,
    })

def funcionario_update_pagamentos(request, id_pagamento):

    if request.method == 'POST':
        # Capturar os dados enviados pelo formulário
        descricao = request.POST.get('descricao')
        valor = request.POST.get('valor')
        data_vencimento = request.POST.get('data_vencimento')
        estado = request.POST.get('estado')
        multa = request.POST.get('multa', 0.00)  # Valor padrão para multa

        try:
            # Atualizar os dados usando o procedimento armazenado
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_funcionario_update_pagamentos(%s, %s, %s, %s, %s, %s);
                """, [id_pagamento, descricao, valor, data_vencimento, estado, multa])

            messages.success (request, "Pagamento atualizado com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao atualizar pagamento: {str(e)}")

    # Redirecionar de volta à página de pagamentos com uma mensagem de sucesso ou erro
    return redirect('pagamentos_funcionario')

def funcionario_delete_pagamentos(request, id_pagamento):
    try:
        # Verificar se o registro existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Pagamentos WHERE id_pagamento = %s", [id_pagamento])
            if cursor.fetchone() is None:
                messages.error(request, "Pagamento não encontrado.")
                return redirect('pagamentos_funcionario')

        # Remover o pagamento usando o procedimento armazenado
        with connection.cursor() as cursor:
            cursor.execute("CALL p_funcionario_delete_pagamentos(%s);", [id_pagamento])

        # Adicionar uma mensagem de sucesso
        messages.success(request, "Pagamento removido com sucesso!")
    except Exception as e:
        # Adicionar uma mensagem de erro
        messages.error(request, f"Erro ao remover pagamento: {str(e)}")

    # Redirecionar de volta para a página de pagamentos
    return redirect('pagamentos_funcionario')


#Inserção da matricula do aluno
def matricula_aluno(request):

    user_id = request.session.get('user_id')  # ID do aluno logado
    aluno_data = {}

    try:
        # Buscar os dados do aluno logado
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p_nome, u_nome, email, telefone, localidade
                FROM alunos
                WHERE id_aluno = %s
            """, [user_id])
            aluno = cursor.fetchone()

        if aluno:
            aluno_data = {
                'p_nome': aluno[0],
                'u_nome': aluno[1],
                'email': aluno[2],
                'telefone': aluno[3],
                'localidade': aluno[4],
            }
        else:
            messages.error(request, "Aluno não encontrado.")
            return redirect('dashboard')  # Redireciona caso o aluno não seja encontrado

        if request.method == 'POST':
            # Capturar os dados enviados pelo formulário
            id_curso = request.POST.get('id_curso')
            ano_letivo = request.POST.get('ano_letivo')
            data_inscricao = request.POST.get('ano_inscricao')

            # Inserir matrícula usando o procedimento armazenado
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL p_matricula_insert(%s, %s, %s, %s);
                """, [user_id, id_curso, data_inscricao, ano_letivo])

            messages.success(request, "Matrícula realizada com sucesso!")
            return redirect('matricula_aluno')

    except Exception as e:
        messages.error(request, f"Erro ao carregar os dados do aluno ou realizar a matrícula: {str(e)}")

    # Renderizar o formulário de inscrição com os dados do aluno preenchidos
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'matricula_aluno',
        'aluno_data': aluno_data,
    })


    

@funcionario_required
def avaliacoes_funcionario(request):
    curso = request.GET.get('curso')
    ano = request.GET.get('ano')
    semestre = request.GET.get('semestre')
    epoca = request.GET.get('epoca')
    
    query = "SELECT * FROM f_listar_avaliacoes()"
    conditions = []
    params = []

    if curso:
        conditions.append("curso = %s")
        params.append(curso)
    if ano:
        conditions.append("ano = %s")
        params.append(ano)
    if semestre:
        conditions.append("semestre = %s")
        params.append(semestre)
    if epoca:
        conditions.append("epoca = %s")
        params.append(epoca)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        avaliacoes = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Obter opções para filtros
        cursor.execute("SELECT DISTINCT Nome FROM Cursos")
        cursos = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Nome_Ano FROM Ano")
        anos = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Nome_Semestre FROM Semestre")
        semestres = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Epoca FROM Avaliacoes")
        epocas = [row[0] for row in cursor.fetchall()]

    return render(request, 'pagina_principal/main.html', {
        'default_content': 'avaliacoes_funcionario',
        'avaliacoes': avaliacoes,
        'cursos': cursos,
        'anos': anos,
        'semestres': semestres,
        'epocas': epocas,
        'filtros': {
            'curso': curso,
            'ano': ano,
            'semestre': semestre,
            'epoca': epoca
        }
    })


@funcionario_required
def aprovar_avaliacao(request, id_avaliacao):
    try:
        with connection.cursor() as cursor:
            cursor.execute("CALL p_aprovar_avaliacao(%s)", [id_avaliacao])
        messages.success(request, f"Avaliação {id_avaliacao} processada com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro ao aprovar avaliação: {str(e)}")
    
    return redirect('avaliacoes_funcionario')


@professor_required
def avaliacoes_professor(request):
    id_professor = request.session.get('user_id')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            avaliacoes = data.get('avaliacoes', [])

            with connection.cursor() as cursor:
                for avaliacao in avaliacoes:
                    cursor.execute("""
                        CALL p_avaliacoes_professor_inserir(%s, %s, %s, %s, %s, %s, %s)
                    """, [
                        id_professor,
                        avaliacao['id_aluno'],
                        avaliacao['id_uc'],
                        avaliacao['nome'],
                        avaliacao['data_avaliacao'],
                        avaliacao['epoca'],
                        avaliacao['nota']
                    ])
            return JsonResponse({'success': True, 'message': 'Avaliações registadas com sucesso.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT UC.ID_UC, UC.Nome FROM Unidades_Curriculares UC JOIN Turnos T ON UC.ID_UC = T.ID_UC JOIN Turnos_Professor tp ON T.ID_Turno = tp.ID_Turno WHERE tp.ID_Professor_Turno = %s", (id_professor,) )
        ucs = cursor.fetchall()
        uc_ids = [uc[0] for uc in ucs]  # Armazena o ID de cada UC

        if uc_ids:
            cursor.execute("SELECT A.n_meca, A.P_Nome, UC.nome AS UC FROM Alunos A JOIN Matriculas M ON A.ID_Aluno = M.ID_Aluno JOIN Cursos C ON M.ID_Curso = C.ID_Curso JOIN Unidades_Curriculares UC ON C.ID_Curso = UC.ID_Curso WHERE UC.ID_UC IN %s ORDER BY UC", (tuple(uc_ids),))
            alunos = cursor.fetchall()
            # Query aos Alunos - filtrar por Curso e UCs do prof
        else:
            alunos = []
    
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'avaliacoes_professor',
        'ucs': ucs,
        'alunos': alunos
    })


@aluno_required
def avaliacoes_aluno(request):
    id_aluno = request.session.get('user_id')
    ano = request.GET.get('ano')
    semestre = request.GET.get('semestre')
    epoca = request.GET.get('epoca')
    
    query = """
        SELECT * FROM f_listar_avaliacoes_aluno(%s, %s, %s, %s)
    """
    params = [
        id_aluno,
        ano if ano else None,
        semestre if semestre else None,
        epoca if epoca else None
    ]

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        avaliacoes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Filtros
        cursor.execute("SELECT DISTINCT Nome_Ano FROM Ano")
        anos = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Nome_Semestre FROM Semestre")
        semestres = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Epoca FROM Avaliacoes")
        epocas = [row[0] for row in cursor.fetchall()]
    
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'avaliacoes_aluno',
        'avaliacoes': avaliacoes,
        'anos': anos,
        'semestres': semestres,
        'epocas': epocas,
        'filtros': {
            'ano': ano,
            'semestre': semestre,
            'epoca': epoca
        }
    })

def carregar_horario_aluno(request):
    # Verifica se o usuário está logado e é aluno
    user_id = request.session.get('user_id')

    try:
        # Consulta os horários do aluno usando uma função SQL equivalente
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM diogo_f_obter_horarios_completo_aluno(%s)
            """, [user_id])

            horarios = cursor.fetchall()

        # Converte os resultados para um formato JSON
        horarios_data = [
            {
                'id_turno': horario[0],
                'turno_nome': horario[1],
                'nome_uc': horario[2],
                'nome_semestre': horario[3],
                'nome_ano': horario[4],
                'espaco': horario[5],
                'dia_semana': horario[6],
                'hora_inicio': str(horario[7]),
                'hora_fim': str(horario[8])
            }
            for horario in horarios
        ]

        return JsonResponse(horarios_data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@aluno_required
def dashboard_aluno(request):
    user_id = request.session.get('user_id')  # Obtém o ID do aluno logado

    try:
        with connection.cursor() as cursor:
            # Buscar resumo acadêmico do aluno
            cursor.execute("SELECT * FROM diogo_f_resumo_academico_aluno(%s);", [user_id])
            resultado = cursor.fetchone()

        with connection.cursor() as cursor:
            # Buscar avaliações recentes do aluno
            cursor.execute("SELECT * FROM diogo_f_obter_avaliacoes_recentes_aluno(%s);", [user_id])
            avaliacoes = cursor.fetchall()

        # Definir valores padrão quando o aluno não está matriculado ou não tem dados
        contexto = {
            'curso_nome': resultado[0] if resultado and resultado[0] else "Não Matriculado",
            'unidades_curriculares': resultado[1] if resultado and resultado[1] else "Sem turnos inscritos",
            'propinas_pendentes': resultado[2] if resultado and resultado[2] > 0 else "Sem propinas pendentes",
            'avaliacoes': [
                {
                    'nome_uc': av[0],
                    'nome_metodo': av[1],
                    'data_avaliacao': av[2],
                    'nota': av[3]
                }
                for av in avaliacoes
            ] if avaliacoes else [],
            'default_content': 'dashboard_aluno'  # Define o conteúdo padrão da página
        }

    except Exception as e:
        contexto = {
            'curso_nome': "Erro ao carregar curso",
            'unidades_curriculares': "Erro ao carregar UC",
            'propinas_pendentes': "Erro",
            'avaliacoes': [],
            'default_content': 'dashboard_aluno'
        }

    return render(request, 'pagina_principal/main.html', contexto)


@professor_required
def dashboard_professor(request):
    user_id = request.session.get('user_id')  # Obtém o ID do professor logado

    try:
        with connection.cursor() as cursor:
            # Buscar os dados acadêmicos do professor
            cursor.execute("SELECT * FROM diogo_f_resumo_academico_professor(%s);", [user_id])
            resultado = cursor.fetchone()

        if resultado:
            contexto = {
                'curso_nome': resultado[0] if resultado[0] else "Não leciona cursos",
                'unidades_curriculares': resultado[1] if resultado[1] else "Não leciona unidades curriculares",
                'default_content': 'dashboard_professor'
            }
        else:
            contexto = {
                'curso_nome': "Não leciona cursos",
                'unidades_curriculares': "Não leciona unidades curriculares",
                'default_content': 'dashboard_professor'
            }

    except Exception as e:
        contexto = {
            'curso_nome': "Erro ao carregar curso",
            'unidades_curriculares': "Erro ao carregar UC",
            'default_content': 'dashboard_professor'
        }

    return render(request, 'pagina_principal/main.html', contexto)

@funcionario_required
def dashboard_funcionario(request):
    # Conectar ao PostgreSQL e executar a função
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM diogo_f_resumo_administrativo_funcionario();")
        resultado = cursor.fetchone()

    # Mapear os dados para o contexto
    contexto = {
        'default_content': 'dashboard_funcionario',
        'total_cursos': resultado[0] if resultado else 0,
        'total_turnos': resultado[1] if resultado else 0,
        'total_matriculas': resultado[2] if resultado else 0
    }

    return render(request, 'pagina_principal/main.html', contexto)

@aluno_required
def horarios_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'horarios_aluno'})

@professor_required
def horarios_professor(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'horarios_professor'})

@aluno_required
def pagamentos_aluno(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pagamentos_aluno'})

@funcionario_required
def pagamentos_funcionario(request):
    return render(request, 'pagina_principal/main.html', {'default_content': 'pagamentos_funcionario'})

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

@professor_required
def unidades_curriculares_professor(request):
    """
    Retorna as unidades curriculares associadas aos turnos do professor logado,
    com suporte a filtros de turno, ano e semestre.
    """
    id_professor = request.session.get('user_id')  # Obtém o ID do professor da sessão

    turno = request.GET.get('turno')  # Filtro por turno
    ano = request.GET.get('ano')      # Filtro por ano
    semestre = request.GET.get('semestre')  # Filtro por semestre

    try:
        with connection.cursor() as cursor:
            query = """
                SELECT uc.id_uc, uc.nome AS unidade_curricular, uc.id_ano, uc.id_semestre, uc.ects, t.turno_nome
                FROM public.unidades_curriculares uc
                JOIN public.turnos t ON uc.id_uc = t.id_uc
                JOIN public.turnos_professor tp ON t.id_turno = tp.id_turno
                WHERE tp.id_professor = %s
            """
            params = [id_professor]

            if turno:
                query += " AND t.turno_nome = %s"
                params.append(turno)

            if ano:
                query += " AND uc.id_ano = %s"
                params.append(ano)

            if semestre:
                query += " AND uc.id_semestre = %s"
                params.append(semestre)

            cursor.execute(query, params)
            unidades_curriculares = cursor.fetchall()
            
            colunas = [col[0] for col in cursor.description]
            unidades_formatadas = [dict(zip(colunas, uc)) for uc in unidades_curriculares]

        return render(request, 'pagina_principal/main.html', {
            'default_content': 'unidades_curriculares_professor',
            'unidades_curriculares': unidades_formatadas,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
