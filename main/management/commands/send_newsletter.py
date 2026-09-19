from django.core.management.base import BaseCommand, CommandError

from main.models import Newsletter, Attempt
from main.services import send_newsletter


class Command(BaseCommand):
    help = 'Отправляет рассылку по её ID'

    def add_arguments(self, parser):
        parser.add_argument('newsletter_id', type=int, help='ID рассылки')

    def handle(self, *args, **options):
        nid = options['newsletter_id']
        try:
            newsletter = Newsletter.objects.get(pk=nid)
        except Newsletter.DoesNotExist:
            raise CommandError(f'Рассылка с ID={nid} не найдена.')

        attempts = send_newsletter(newsletter)

        if not attempts:
            self.stdout.write(self.style.WARNING(
                'Отправка не выполнена: нет получателей или рассылка завершена.'
            ))
            return

        success = sum(1 for a in attempts if a.status == Attempt.STATUS_SUCCESS)
        self.stdout.write(self.style.SUCCESS(
            f'Рассылка #{nid}: успешно {success} из {len(attempts)}.'
        ))