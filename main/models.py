from django.db import models
from django.utils import timezone
from django.conf import settings

class Addressee(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='addressees', 
        verbose_name='Владелец', 
        null=True, blank=True
    )
    email = models.EmailField(verbose_name='Email')
    name = models.CharField(max_length=500, verbose_name='Ф.И.О.')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    def __str__(self):
        return f'{self.name} ({self.email})'

    class Meta:
        
        unique_together = [('owner', 'email')]
        verbose_name = 'Получатель рассылки'
        verbose_name_plural = 'Получатели рассылки'
        ordering = ['name']


class Message(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='messages', 
        verbose_name='Владелец', 
        null=True, blank=True
    )
    subject = models.CharField(max_length=500, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'


class Newsletter(models.Model):
    STATUS_CREATED = 'Создана'
    STATUS_STARTED = 'Запущена'
    STATUS_FINISHED = 'Завершена'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_FINISHED, 'Завершена'),
    ]
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='newsletters', 
        verbose_name='Владелец', 
        null=True, blank=True
    )
    first_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата и время первой отправки')
    end_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата и время окончания отправки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name='Статус')
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='mailings', verbose_name='Сообщение')
    recipients = models.ManyToManyField('Addressee', related_name='mailings', verbose_name='Получатели')

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-first_sent_at']
        permissions = [
            ("can_block_users", "Может блокировать пользователей"),
            ("can_disable_newsletters", "Может отключать рассылки"),
        ]

    def __str__(self):
        return f'Рассылка #{self.pk} ({self.status})'

    def update_status(self):
        """Пересчитать статус на основе факта отправки и текущего времени."""
        now = timezone.now()
        
        if self.end_at is not None and now >= self.end_at:
            new_status = self.STATUS_FINISHED
        elif self.first_sent_at is not None:
            new_status = self.STATUS_STARTED
        else:
            new_status = self.STATUS_CREATED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])


class Attempt(models.Model):
    STATUS_SUCCESS = 'Успешно'
    STATUS_FAILED = 'Не успешно'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE, related_name='attempts', verbose_name='Рассылка')
    recipient = models.ForeignKey(Addressee, on_delete=models.CASCADE, related_name='attempts', verbose_name='Получатель')
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус')
    server_response = models.TextField(blank=True, verbose_name='Ответ почтового сервера')

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['newsletter', '-attempted_at']),
        ]

    def __str__(self):
        return f'Попытка #{self.pk} → {self.recipient.email} ({self.status})'