from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.db.models.aggregates import Count
from django.utils import timezone
import logging
from .models import Newsletter, Attempt

logger = logging.getLogger(__name__)

def send_newsletter(newsletter: Newsletter) -> list[Attempt]:
    """
    Отправляет рассылку каждому получателю.
    На каждого получателя создаётся отдельная Attempt.
    Возвращает список созданных попыток.
    """
    attempts = []
    newsletter.update_status()

    # Если статус не "Запущена" — выходим
    if newsletter.status != Newsletter.STATUS_STARTED:
        logger.info('Рассылка #%s в статусе "%s", отправка запрещена.', newsletter.pk, newsletter.status)
        return attempts

    # Получаем список получателей
    recipients = list(newsletter.recipients.all())
    if not recipients:
        logger.info('Рассылка #%s: нет получателей.', newsletter.pk)
        return attempts

    subject = newsletter.message.subject
    body = newsletter.message.body
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    any_success = False

    # Отправляем каждому
    for recipient in recipients:
        try:
            sent = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempt = Attempt.objects.create(
                newsletter=newsletter,
                recipient=recipient,
                status=Attempt.STATUS_SUCCESS,
                server_response=f'OK. Отправлено писем: {sent}',
            )
            any_success = True
        except Exception as exc:
            logger.exception(
                'Ошибка отправки рассылки #%s на %s',
                newsletter.pk,
                recipient.email,
            )
            attempt = Attempt.objects.create(
                newsletter=newsletter,
                recipient=recipient,
                status=Attempt.STATUS_FAILED,
                server_response=str(exc),
            )
        print(">>> ПОПЫТКА:", recipient.email, "статус:", attempt.status)
        attempts.append(attempt)

    # Фиксируем первую успешную отправку
    if any_success and newsletter.first_sent_at is None:
        newsletter.first_sent_at = timezone.now()
        newsletter.save(update_fields=['first_sent_at'])

    # Обновляем статус и ВСЕГДА возвращаем список attempts
    newsletter.update_status()
    return attempts


def get_user_stats(user):
    """Успешные/неуспешные попытки и число отправленных сообщений."""
    qs = Attempt.objects.filter(newsletter__owner=user)

    data = qs.aggregate(
        total_attempts=Count('id'),
        successful=Count('id', filter=Q(status=Attempt.STATUS_SUCCESS)),
        failed=Count('id', filter=Q(status=Attempt.STATUS_FAILED)),
    )
    total = data['total_attempts'] or 0
    data['success_rate'] = round(data['successful'] / total * 100, 2) if total else 0
    return data