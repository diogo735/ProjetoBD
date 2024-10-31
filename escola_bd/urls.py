from django.contrib import admin
from django.urls import path
from app_escola import views  # Importa as views do app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Rota para a view home
    path('login/', views.login_view, name='login'),
    path('pagina_principal/', views.pagina_principal, name='pagina_principal'),
]
