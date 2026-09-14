from django.contrib import admin
from django.utils.html import format_html
from .models import Addressee, Message, Newsletter, Attempt


@admin.register(Addressee)
class AddresseeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'comment_short')
    search_fields = ('name', 'email', 'comment')
    ordering = ('name',)
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'email')
        }),
        ('Дополнительно', {
            'fields': ('comment',),
            'classes': ('wide',),
        }),
    )

    @admin.display(description='Комментарий')
    def comment_short(self, obj):
        if not obj.comment:
            return '—'
        return obj.comment[:60] + '…' if len(obj.comment) > 60 else obj.comment


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'body_short')
    search_fields = ('subject', 'body')
    ordering = ('id',)
    list_per_page = 25

    @admin.display(description='Тело письма')
    def body_short(self, obj):
        if not obj.body:
            return '—'
        return obj.body[:60] + '…' if len(obj.body) > 60 else obj.body


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'message',
        'status',
        'first_sent_at',
        'end_at',
        'recipients_count',
    )
    search_fields = ('status', 'message__subject')
    ordering = ('-first_sent_at',)
    list_per_page = 25
    list_filter = ('status',)
    date_hierarchy = 'first_sent_at'
    filter_horizontal = ('recipients',)  
    readonly_fields = ('status',)          

    fieldsets = (
        ('Основное', {
            'fields': ('message', 'recipients')
        }),
        ('Расписание', {
            'fields': ('first_sent_at', 'end_at')
        }),
        ('Статус', {
            'fields': ('status',),
        }),
    )

    @admin.display(description='Получателей')
    def recipients_count(self, obj):
        return obj.recipients.count()


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'newsletter_link',
        'recipient',
        'attempted_at',
        'status',
        'server_response_short',
    )
    search_fields = (
        'status',
        'newsletter__message__subject',
        'recipient__email',
        'server_response',
    )
    ordering = ('-attempted_at',)
    list_per_page = 25
    list_filter = ('status', 'attempted_at')
    date_hierarchy = 'attempted_at'
    readonly_fields = ('attempted_at',)

    @admin.display(description='Рассылка', ordering='newsletter__id')
    def newsletter_link(self, obj):
        return format_html(
            '<a href="/admin/main/newsletter/{}/change/">Рассылка #{}</a>',
            obj.newsletter_id,
            obj.newsletter_id,
        )

    @admin.display(description='Ответ сервера')
    def server_response_short(self, obj):
        if not obj.server_response:
            return '—'
        return obj.server_response[:60] + '…' if len(obj.server_response) > 60 else obj.server_response