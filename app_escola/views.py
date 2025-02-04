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


# Inserção da matricula do aluno
def matricula_aluno(request):
    user_id = request.session.get('user_id')  # ID do aluno logado na aplicação
    aluno_data = {}
    detalhes_matricula = None
    ucs_matricula = []

    try:
        # Vai obter os dados do aluno que está logado
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
            return redirect('dashboard')

        # Captura os dados do formulário
        if request.method == 'POST':
            id_curso = request.POST.get('id_curso')
            ano_letivo = request.POST.get('ano_letivo')
            data_inscricao = request.POST.get('ano_inscricao')
            ucs_selecionadas = request.POST.getlist('ucs[]')  # Lista dos IDs das UCs selecionados

            # Captura os dados dos turnos
            turnos_selecionados = []
            for uc_id in ucs_selecionadas:
                turno_id = request.POST.get(f"turno_{uc_id}")
                if turno_id:
                    turnos_selecionados.append((int(uc_id), int(turno_id)))

            # Inserção da matricula
            with connection.cursor() as cursor:
                print("Executando CALL p_matricula_insert com:", user_id, id_curso, data_inscricao, ano_letivo)
                cursor.execute("""
                    CALL p_matricula_insert(%s, %s, %s, %s);
                """, [user_id, id_curso, data_inscricao, ano_letivo])

                # Vai buscar o ID da matrícula criada
                cursor.execute("SELECT currval('matriculas_id_matricula_seq');")
                id_matricula = cursor.fetchone()[0]

            if not id_matricula:
                messages.error(request, "Erro ao criar a matrícula.")
                return redirect('matricula_aluno')

            # Inserção dos turnos na tabela matriculas_turnos
            if turnos_selecionados:
                with connection.cursor() as cursor:
                    for uc_id, turno_id in turnos_selecionados:
                        print(f"Inserindo turno {turno_id} para a matrícula {id_matricula}")
                        cursor.execute("""
                            CALL p_matriculas_turno_insert(%s, %s);
                        """, [id_matricula, turno_id])
                    connection.commit() 

            messages.success(request, "Matrícula realizada com sucesso!")
            return redirect('matricula_aluno')

        # Dados da matricula atual do aluno logado na aplicação
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM vw_alunos_detalhes_matricula WHERE id_aluno = %s", [user_id])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        if rows:
            matricula = [dict(zip(columns, row)) for row in rows]

            # Dados gerais da matricula
            detalhes_matricula = {
                'curso': matricula[0]['curso'],
                'ano_letivo': matricula[0]['ano_letivo'],
                'data_matricula': matricula[0]['data_matricula']
            }

            # Criação das lista dos turnos e UCs que o aluno inscreveu-se
            for item in matricula:
                ucs_matricula.append({
                    'unidade_curricular': item['unidade_curricular'],
                    'turno': item['turno']
                })

    except Exception as e:
        messages.error(request, f"Erro ao carregar os dados: {str(e)}")

    return render(request, 'pagina_principal/main.html', {
        'default_content': 'matricula_aluno',
        'aluno_data': aluno_data,
        'detalhes_matricula': detalhes_matricula,
        'ucs_matricula': ucs_matricula,
        'mensagem_matricula': "Matrícula carregada com sucesso." if detalhes_matricula else "Nenhuma matrícula encontrada.",
        'status_matriculas': "sucesso" if detalhes_matricula else "erro",
    })


# Fetch do cursos
def get_cursos(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_curso, nome
                FROM cursos
            """)
            cursos = cursor.fetchall()
        return JsonResponse([{'id': curso[0], 'nome': curso[1]} for curso in cursos], safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
# Fetch das UCs de cada curso
def get_ucs(request, curso_id, ano_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_uc, nome, id_semestre
                FROM unidades_curriculares
                WHERE id_curso = %s AND id_ano = %s
                ORDER BY id_semestre, nome
            """, [curso_id, ano_id])
            ucs = cursor.fetchall()

        return JsonResponse([
            {'id_uc': uc[0], 'nome': uc[1], 'id_semestre': uc[2]} for uc in ucs
        ], safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
#Fetch turnos
def get_turnos(request, uc_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_turno, turno_nome, vagas_totais
                FROM turnos
                WHERE id_uc = %s
                ORDER BY turno_nome
            """, [uc_id])
            turnos = cursor.fetchall()

        return JsonResponse([
            {'id_turno': turno[0], 'turno_nome': turno[1], 'vagas_totais': turno[2]} for turno in turnos
        ], safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
# Listar todas as matriculas através do funcionário
def listar_matriculas(request):
    mensagem_todas_matriculas = None
    status_todas_matriculas = None
    todas_matriculas = []

    try:
        # Chamar a função SQL para listar todas as matrículas
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM public.f_funcionario_listar_matriculas();
            """)
            todas_matriculas = [
                {
                    'id_matricula': matricula[0],
                    'nome_aluno': matricula[1],
                    'nome_curso': matricula[2],
                    'data_matricula': matricula[3],
                    'ano_letivo': matricula[4]
                }
                for matricula in cursor.fetchall()
            ]

        mensagem_todas_matriculas = "Todas as matrículas foram carregadas com sucesso."
        status_todas_matriculas = "success"

    except Exception as e:
        # Mensagem de erro
        mensagem_todas_matriculas = f"Erro ao carregar as matrículas: {str(e)}"
        status_todas_matriculas = "error"

    # Renderizar a página com os dados das matrículas
    return render(request, 'pagina_principal/main.html', {
        'default_content': 'matricula_funcionario',
        'todas_matriculas': todas_matriculas,
        'mensagem_todas_matriculas': mensagem_todas_matriculas,
        'status_todas_matriculas': status_todas_matriculas,
    })

# Carregar os detalhes da matricula ao pressionar o botão Ver Detalhes
def matricula_detalhes(request, id_matricula):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM public.f_funcionario_listar_matricula_detalhes(%s)", [id_matricula])
        rows = cursor.fetchall()

    dados = {
        'id_matricula': rows[0][0],
        'nome_aluno': rows[0][1],
        'nome_curso': rows[0][2],
        'ano_letivo': rows[0][3],
        'data_matricula': rows[0][4],
        'ucs': [{'unidade_curricular': row[5], 'turno': row[6]} for row in rows]
    }

    return JsonResponse(dados)

# Eliminação da matricula pelo funcionario 
def funcionario_delete_matricula(request, id_matricula):
    try:
        # Verificar se a matrícula existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Matriculas WHERE id_matricula = %s", [id_matricula])
            if cursor.fetchone() is None:
                messages.error(request, "Matrícula não encontrada.")
                return redirect('funcionario_matriculas')

        # Remover a matrícula utilizando o procedimento armazenado
        with connection.cursor() as cursor:
            cursor.execute("CALL p_funcionario_delete_matricula(%s);", [id_matricula])

        # Mensagem de sucesso
        messages.success(request, "Matrícula removida com sucesso!")
    except Exception as e:
        # Adicionar uma mensagem de erro
        messages.error(request, f"Erro ao remover matrícula: {str(e)}")

    # Redirecionar de volta para a página de matrículas
    return redirect('matricula_funcionario')


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
