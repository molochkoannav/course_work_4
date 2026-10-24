from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as flash
from django.utils.timezone import now

from .models import Addressee, Message, Newsletter, Attempt
from .forms import AddresseeForm, MessageForm, NewsletterForm
from .services import send_newsletter
from django.utils import timezone

# ---------- Главная страница ----------
def index(request):
    now = timezone.now()  
    context = {
        'total_newsletters': Newsletter.objects.count(),
        'active_newsletters': Newsletter.objects.filter(
            first_sent_at__lte=now,       
            end_at__gte=now,     
            status=Newsletter.STATUS_STARTED,
        ).count(),
        'unique_recipients': Addressee.objects.count(),
    }
    return render(request, 'index.html', context)


# ---------- Получатели ----------
def addressee_list(request):
    addressees = Addressee.objects.all()
    return render(request, 'addressee_list.html', {'addressees': addressees})


def addressee_create(request):
    form = AddresseeForm(request.POST or None)
    if form.is_valid():
        form.save()
        flash.success(request, 'Получатель добавлен.')
        return redirect('main:addressee_list')
    return render(request, 'addressee_form.html',
                  {'form': form, 'title': 'Добавить получателя'})


def addressee_update(request, pk):
    obj = get_object_or_404(Addressee, pk=pk)
    form = AddresseeForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        flash.success(request, 'Получатель обновлён.')
        return redirect('main:addressee_list')
    return render(request, 'addressee_form.html',
                  {'form': form, 'title': 'Редактировать получателя'})


def addressee_delete(request, pk):
    obj = get_object_or_404(Addressee, pk=pk)
    if request.method == 'POST':
        obj.delete()
        flash.success(request, 'Получатель удалён.')
        return redirect('main:addressee_list')
    return render(request, 'addressee_confirm_delete.html', {'object': obj})


# ---------- Сообщения ----------
def message_list(request):
    messages_qs = Message.objects.all()
    return render(request, 'message_list.html', {'messages': messages_qs})


def message_create(request):
    form = MessageForm(request.POST or None)
    if form.is_valid():
        form.save()
        flash.success(request, 'Сообщение добавлено.')
        return redirect('main:message_list')
    return render(request, 'message_form.html',
                  {'form': form, 'title': 'Добавить сообщение'})


def message_update(request, pk):
    obj = get_object_or_404(Message, pk=pk)
    form = MessageForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        flash.success(request, 'Сообщение обновлено.')
        return redirect('main:message_list')
    return render(request, 'message_form.html',
                  {'form': form, 'title': 'Редактировать сообщение'})


def message_delete(request, pk):
    obj = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        obj.delete()
        flash.success(request, 'Сообщение удалено.')
        return redirect('main:message_list')
    return render(request, 'message_confirm_delete.html', {'object': obj})


# ---------- Рассылки ----------
def newsletter_list(request):
    newsletters = Newsletter.objects.select_related('message').all()

    filter_param = request.GET.get('filter')
    if filter_param == 'active':
        now = timezone.now()
        newsletters = newsletters.filter(
            first_sent_at__lte=now,
            end_at__gte=now,
            status=Newsletter.STATUS_STARTED,
        )

    # статусы по времени
    for n in newsletters:
        n.update_status()
    return render(request, 'newsletter_list.html', {
        'newsletters': newsletters,
        'filter_param': filter_param,  
    })


def newsletter_detail(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    newsletter.update_status()
    attempts = newsletter.attempts.select_related('recipient').all()
    return render(request, 'newsletter_detail.html', {'newsletter': newsletter, 'attempts': attempts})


def newsletter_create(request):
    form = NewsletterForm(request.POST or None)
    if form.is_valid():
        form.save()
        flash.success(request, 'Рассылка создана.')
        return redirect('main:newsletter_list')
    return render(request, 'newsletter_form.html',
                  {'form': form, 'title': 'Создать рассылку'})


def newsletter_update(request, pk):
    obj = get_object_or_404(Newsletter, pk=pk)
    form = NewsletterForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        flash.success(request, 'Рассылка обновлена.')
        return redirect('main:newsletter_list')
    return render(request, 'newsletter_form.html',
                  {'form': form, 'title': 'Редактировать рассылку'})


def newsletter_delete(request, pk):
    obj = get_object_or_404(Newsletter, pk=pk)
    if request.method == 'POST':
        obj.delete()
        flash.success(request, 'Рассылка удалена.')
        return redirect('main:newsletter_list')
    return render(request, 'newsletter_confirm_delete.html', {'object': obj})


def newsletter_send(request, pk):
    """Ручной запуск отправки через интерфейс."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    attempts = send_newsletter(newsletter)

    if not attempts:
        flash.error(request, 'Отправка не выполнена: нет получателей или рассылка завершена.')
    else:
        success = sum(1 for a in attempts if a.status == Attempt.STATUS_SUCCESS)
        flash.success(request,
                      f'Отправка завершена: успешно {success} из {len(attempts)}.')

    return redirect('main:newsletter_detail', pk=pk)
