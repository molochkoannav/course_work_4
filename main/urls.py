from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),

    # Получатели
    path('addressees/', views.addressee_list, name='addressee_list'),
    path('addressees/create/', views.addressee_create, name='addressee_create'),
    path('addressees/<int:pk>/update/', views.addressee_update, name='addressee_update'),
    path('addressees/<int:pk>/delete/', views.addressee_delete, name='addressee_delete'),

    # Сообщения
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/', views.message_create, name='message_create'),
    path('messages/<int:pk>/update/', views.message_update, name='message_update'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    # Рассылки
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views.newsletter_create, name='newsletter_create'),
    path('newsletters/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),
    path('newsletters/<int:pk>/update/', views.newsletter_update, name='newsletter_update'),
    path('newsletters/<int:pk>/delete/', views.newsletter_delete, name='newsletter_delete'),
    path('newsletters/<int:pk>/send/', views.newsletter_send, name='newsletter_send'),

    # Статистика 
    path('stats/', views.stats_view, name='stats'),
]