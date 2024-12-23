import json
from django.shortcuts import get_object_or_404, render, redirect
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

from django.shortcuts import render

from django.shortcuts import render
from datetime import datetime

@funcionario_required
def unidades_curriculares_funcionario(request):
    # Definindo cursos, anos, semestres e turnos
    cursos = ['Engenharia Informática', 'Engenharia Multimedia', 'Engenharia Turismo']
    anos = ['1º Ano', '2º Ano', '3º Ano']
    semestres = ['1º Semestre', '2º Semestre']
    turnos_horario = ['Manhã', 'Tarde']
    
    # Obter o mês atual
    mes_atual = datetime.now().month
    
    # Determinar semestre atual
    if 9 <= mes_atual >= 2:  # Setembro a Fevereiro
        semestre_atual = '1º Semestre'
    else:  # Março a Agosto
        semestre_atual = '2º Semestre'
    
    turnos = []
    turno_id = 1  # Iniciamos um contador para IDs únicos
    
    for curso in cursos:
        for ano in anos:
            for semestre in semestres:
                if semestre == semestre_atual:  # Filtrar pelo semestre atual
                    for turno in turnos_horario:
                        turnos.append({
                            'curso_nome': curso,
                            'turno_nome': turno,
                            'ano': ano,
                            'semestre': semestre,
                            'vagas_disponiveis': 25,
                            'id_turno': turno_id,
                        })
                        turno_id += 1  # Incrementa o ID para cada turno
    
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

def atualizar_turno_view(request):
    if request.method == "POST":
        turno_id = request.POST.get("turno_id")
        nome_turno = request.POST.get("nome_turno")
        vagas_totais = request.POST.get("vagas_totais")
        ano = request.POST.get("ano")
        semestre = request.POST.get("semestre")
        estado = request.POST.get("estado")

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT atualizar_turno(%s, %s, %s, %s, %s, %s::SMALLINT)
                    """,
                    [turno_id, nome_turno, vagas_totais, ano, semestre, estado]
                )
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido"})

def obter_detalhes_turno(request, turno_id):
    # Verificar se a solicitação é do tipo GET
    if request.method == 'GET':
        try:
            with connection.cursor() as cursor:
                # Executar a consulta para buscar os detalhes do turno específico
                cursor.execute("""
                    SELECT id_turno, turno_nome, vagas_totais,vagas_disponiveis, ano, semestre, estado 
                    FROM turno 
                    WHERE id_turno = %s
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
                    'vagas_disponiveis': row[3],
                    'ano': row[4],
                    'semestre': row[5],
                    'estado': row[6]  # Assumindo que seja um valor booleano ou inteiro (1 ou 0)
                }
                
                # Retornar os dados em formato JSON
                return JsonResponse(turno_data, safe=False)

        except Exception as e:
            # Retornar erro se algo der errado
            print(f"Erro ao obter detalhes do turno: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    # Se não for um método GET, retornamos um erro
    return JsonResponse({'error': 'Método não permitido'}, status=405)

def verificar_eliminar_turno(request):
    if request.method == "POST":
        try:
            turno_id = request.POST.get("turno_id")
            
            # Verificar se o turno pode ser eliminado usando a função no PostgreSQL
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM verificacao_eliminar_turno(%s)", [turno_id])
                result = cursor.fetchone()
                if not result:
                    return JsonResponse({"success": False, "error": "Turno não encontrado ou erro na verificação."})

                # Extrair os valores retornados pela função
                posso_eliminar = result[0]  # O valor booleano
                turno_nome = result[1]      # O nome do turno
                horarios_associados = result[2]  # Quantidade de horários associados

                # Responder com os dados obtidos
                return JsonResponse({
                    "success": True,
                    "turno_nome": turno_nome,
                    "posso_eliminar": posso_eliminar,
                    "horarios_associados": horarios_associados
                })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido"})

def eliminar_turno(request):
    if request.method == "POST":
        try:
            turno_id = request.POST.get("turno_id")
            
            if not turno_id:
                return JsonResponse({"success": False, "error": "ID do turno não fornecido."})

            # Executar o procedimento armazenado no banco de dados
            with connection.cursor() as cursor:
                cursor.execute("CALL p_turno_delete(%s)", [turno_id])

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método inválido"})

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
    id_aluno = request.user.id  # Ajuste conforme seu modelo
    
    # Buscar o ID do Curso pela Matrícula
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ID_Curso 
            FROM Matriculas 
            WHERE ID_Aluno = %s 
            LIMIT 1;
        """, [id_aluno])
        
        row = cursor.fetchone()
        if row:
            id_curso = row[0]
        else:
            id_curso = None

    if not id_curso:
        return render(request, 'pagina_principal/main.html', {
            'default_content': 'professores_aluno',
            'error': 'Curso não encontrado para este aluno.'
        })

    # Buscar os Professores usando a Função SQL
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * 
            FROM fn_professores_curso_aluno(%s, %s);
        """, [id_curso, id_aluno])

        # Obtém os resultados
        professores = [
            {
                'nome': row[1],
                'unidade_curricular': row[2],
                'email': row[3],
                'telefone': row[4]
            } 
            for row in cursor.fetchall()
        ]

    # Renderiza os dados na view
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'professores_aluno',
        'professores': professores
    })

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