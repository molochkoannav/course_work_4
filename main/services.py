from django.core.mail import send_mail
from django.conf import settings
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

    # Рассылку нельзя отправить, если она завершена
    if newsletter.status == Newsletter.STATUS_FINISHED:
        logger.info('Рассылка #%s завершена, отправка пропущена.', newsletter.pk)
        return attempts

    recipients = list(newsletter.recipients.all())
    if not recipients:
        logger.info('Рассылка #%s: нет получателей.', newsletter.pk)
        return attempts

    subject = newsletter.message.subject
    body = newsletter.message.body
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    any_success = False

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
        attempts.append(attempt)

    # Фиксируем первую отправку
    if any_success and newsletter.first_sent_at is None:
        newsletter.first_sent_at = timezone.now()
        newsletter.save(update_fields=['first_sent_at'])
    newsletter.update_status()   
    return attempts