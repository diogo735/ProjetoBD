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

    path('aluno/horarios/', views.horarios_aluno, name='horarios_aluno'),
    path('professor/horarios/', views.horarios_professor, name='horarios_professor'),

    path('aluno/professores/', views.professores_aluno, name='professores_aluno'),
    path('funcionario/professores/', views.professores_funcionario, name='professores_funcionario'),
    
    path('aluno/avaliacoes/', views.avaliacoes_aluno, name='avaliacoes_aluno'),
    path('professor/avaliacoes/', views.avaliacoes_professor, name='avaliacoes_professor'),
    path('funcionario/avaliacoes/', views.avaliacoes_funcionario, name='avaliacoes_funcionario'),

    path('aluno/pagamentos/', views.pagamentos_aluno, name='pagamentos_aluno'),
    path('funcionario/pagamentos/', views.pagamentos_funcionario, name='pagamentos_funcionario'),

    path('aluno/matricula/', views.matricula_aluno, name='matricula_aluno'),
    path('funcionario/matricula/', views.matricula_funcionario, name='matricula_funcionario'),

    path('professor/unidades_curriculares/', views.unidades_curriculares_professor, name='unidades_curriculares_professor'),
    path('funcionario/unidades_curriculares/', views.unidades_curriculares_funcionario, name='unidades_curriculares_funcionario'),

    path('funcionarios/alunos/', views.alunos_funcionario, name='alunos_funcionario'),
    
    path('aluno/gestao_escola/', views.gestao_escola_aluno, name='gestao_escola_aluno'),
    path('professor/gestao_escola/', views.gestao_escola_professor, name='gestao_escola_professor'),
    path('funcionario/gestao_escola/', views.gestao_escola_funcionario, name='gestao_escola_funcionario'),

]
