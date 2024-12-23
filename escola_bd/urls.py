from django.contrib import admin
from django.urls import path
from app_escola import views  # Importa as views do app
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  
    path('login/', views.login_view, name='login'),
    #path('pagina_principal/', views.pagina_principal, name='pagina_principal'),
    path('loading/', views.loading_page, name='loading_page'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    #opções da nav bar
 
    path('aluno/dashboard/', views.dashboard_aluno, name='dashboard_aluno'),
    path('professor/dashboard/', views.dashboard_professor, name='dashboard_professor'),
    path('funcionario/dashboard/', views.dashboard_funcionario, name='dashboard_funcionario'),
    path('obter_cursos/', views.obter_cursos, name='obter_cursos'),
    path('criar_turno/', views.criar_turno, name='criar_turno'),
    path('buscar_dados/', views.buscar_turnos, name='buscar_turnos'),
    path('atualizar_turno/', views.atualizar_turno_view, name='atualizar_turno'),
    path('obter_detalhes_turno/<int:turno_id>/', views.obter_detalhes_turno, name='obter_detalhes_turno'),
    path('verificar_eliminar_turno/', views.verificar_eliminar_turno, name='verificar_eliminar_turno'),
    path('eliminar_turno/', views.eliminar_turno, name='eliminar_turno'),
    path('pesquisar_horarios/', views.pesquisar_horarios, name='pesquisar_horarios'),
    path('obter_horarios_e_ucs/<int:turno_id>/<int:curso_id>/<str:ano>/<str:semestre>/', views.obter_horarios_e_ucs,name='obter_horarios_e_ucs'),
    path('obter_id_curso/<str:nome_curso>/', views.obter_id_curso, name='obter_id_curso'),

    path('aluno/horarios/', views.horarios_aluno, name='horarios_aluno'),
    path('professor/horarios/', views.horarios_professor, name='horarios_professor'),

    path('aluno/professores/', views.professores_aluno, name='professores_aluno'),
    path('funcionario/professores/', views.professores_funcionario, name='professores_funcionario'),
    path('funcionarios/professores/remover/<int:id_professor>/', views.professor_delete, name='professor_delete'),
    path('funcionario/professores/editar/<int:id_professor>/', views.professor_editar, name='professor_editar'),
    path('funcionario/professores/atribuirUC/<int:id_professor>/', views.atribuir_uc_professor, name='atribuir_uc_professor'),

    path('aluno/avaliacoes/', views.avaliacoes_aluno, name='avaliacoes_aluno'),
    path('professor/avaliacoes/', views.avaliacoes_professor, name='avaliacoes_professor'),
    path('funcionario/avaliacoes/', views.avaliacoes_funcionario, name='avaliacoes_funcionario'),
    path('avaliacoes/aprovar/<int:id_avaliacao>/', views.aprovar_avaliacao, name='aprovar_avaliacao'),
    #path('avaliacoes/inserir/', views.inserir_avaliacoes_professor, name='inserir_avaliacoes_professor'),


    path('aluno/pagamentos/', views.pagamentos_aluno, name='pagamentos_aluno'),
    path('funcionario/pagamentos/', views.pagamentos_funcionario, name='pagamentos_funcionario'),

    path('aluno/matricula/', views.matricula_aluno, name='matricula_aluno'),
    path('funcionario/matricula/', views.matricula_funcionario, name='matricula_funcionario'),

    path('professor/unidades_curriculares/', views.unidades_curriculares_professor, name='unidades_curriculares_professor'),
    path('funcionario/unidades_curriculares/', views.unidades_curriculares_funcionario, name='unidades_curriculares_funcionario'),
    path('funcionario/obter_horarios/<int:id_turno>/', views.obter_horarios_turno, name='obter_horarios_turno'),

    path('funcionarios/alunos/', views.alunos_funcionario, name='alunos_funcionario'),
    path('funcionarios/delete/<int:id_aluno>/', views.aluno_delete, name='aluno_delete'),
    path('funcionarios/editar/<int:id_aluno>/', views.aluno_editar, name='aluno_editar'),


    path('aluno/gestao_escola/', views.gestao_escola_aluno, name='gestao_escola_aluno'),
    path('professor/gestao_escola/', views.gestao_escola_professor, name='gestao_escola_professor'),
    path('funcionario/gestao_escola/', views.gestao_escola_funcionario, name='gestao_escola_funcionario'),

]
