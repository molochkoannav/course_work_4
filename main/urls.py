from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    # Получатели
    path('addressees/', views.AddresseeListView.as_view(), name='addressee_list'),
    path('addressees/create/', views.AddresseeCreateView.as_view(), name='addressee_create'),
    path('addressees/<int:pk>/edit/', views.AddresseeUpdateView.as_view(), name='addressee_update'),
    path('addressees/<int:pk>/delete/', views.AddresseeDeleteView.as_view(), name='addressee_delete'),

    # Сообщения
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/edit/', views.MessageUpdateView.as_view(), name='message_update'),
    path('messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Рассылки
    path('newsletters/', views.NewsletterListView.as_view(), name='newsletter_list'),
    path('newsletters/create/', views.NewsletterCreateView.as_view(), name='newsletter_create'),
    path('newsletters/<int:pk>/', views.NewsletterDetailView.as_view(), name='newsletter_detail'),
    path('newsletters/<int:pk>/edit/', views.NewsletterUpdateView.as_view(), name='newsletter_update'),
    path('newsletters/<int:pk>/delete/', views.NewsletterDeleteView.as_view(), name='newsletter_delete'),
    path('newsletters/<int:pk>/send/', views.NewsletterSendView.as_view(), name='newsletter_send'),


    path('stats/', views.StatsView.as_view(), name='stats'),

    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/block/', views.BlockUserView.as_view(), name='user_block'),
    path('newsletters/<int:pk>/disable/', views.DisableNewsletterView.as_view(), name='newsletter_disable'),
]