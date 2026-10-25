from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/',    views.UserLoginView.as_view(),  name='login'),
    path('logout/',   views.UserLogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.RegisterView.as_view(),   name='register'),
    path('profile/',  views.ProfileView.as_view(),    name='profile'),
    path('password_change/',auth_views.PasswordChangeView.as_view(template_name='password_change.html',success_url=reverse_lazy('users:profile')),name='password_change'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/users/password_reset/done/'
         ), 
         name='password_reset'),
    
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/users/reset/done/'
         ), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
