from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView,
)
from django.contrib import messages as flash

from .forms import AddresseeForm, MessageForm, NewsletterForm
from .models import Addressee, Message, Newsletter, Attempt
from .services import send_newsletter, get_user_stats
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
User = get_user_model()

# ==========================================
# 1. Вспомогательные функции и миксины
# ==========================================

def is_manager(user):
    return user.is_authenticated and (
        user.is_superuser or
        user.groups.filter(name='Менеджеры').exists() or 
        user.groups.filter(name='Админы').exists()
    )

class ManagerVisibleQuerysetMixin:
    """Менеджер видит все объекты, обычный пользователь — только свои."""
    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Изменять/удалять может только владелец (менеджер — тоже только своё)."""
    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)

    def test_func(self):
        return True  


# ==========================================
# 2. Главная страница
# ==========================================


class IndexView(TemplateView):          
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        user = self.request.user

       
        newsletters = Newsletter.objects.all()
        addressees = Addressee.objects.all()
        
    
        if user.is_authenticated and not is_manager(user):
            newsletters = newsletters.filter(owner=user)
            addressees = addressees.filter(owner=user)

        ctx['total_newsletters'] = newsletters.count()
        ctx['active_newsletters'] = newsletters.filter(
            first_sent_at__lte=now, 
            end_at__gte=now,
            status=Newsletter.STATUS_STARTED,
        ).count()
        ctx['unique_recipients'] = addressees.count()
        return ctx


# ==========================================
# 3. Получатели (Addressee)
# ==========================================

class AddresseeListView(LoginRequiredMixin, ManagerVisibleQuerysetMixin, ListView):
    model = Addressee
    template_name = 'addressee_list.html'
    context_object_name = 'addressees'


class AddresseeCreateView(LoginRequiredMixin, CreateView):
    model = Addressee
    form_class = AddresseeForm
    template_name = 'addressee_form.html'
    success_url = reverse_lazy('main:addressee_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        flash.success(self.request, 'Получатель добавлен.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Добавить получателя'
        return ctx


class AddresseeUpdateView(OwnerRequiredMixin, UpdateView):
    model = Addressee
    form_class = AddresseeForm
    template_name = 'addressee_form.html'
    success_url = reverse_lazy('main:addressee_list')

    def form_valid(self, form):
        flash.success(self.request, 'Получатель обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать получателя'
        return ctx


class AddresseeDeleteView(OwnerRequiredMixin, DeleteView):
    model = Addressee
    template_name = 'addressee_confirm_delete.html'
    success_url = reverse_lazy('main:addressee_list')

    def form_valid(self, form):
        flash.success(self.request, 'Получатель удалён.')
        return super().form_valid(form)


# ==========================================
# 4. Сообщения (Message)
# ==========================================

class MessageListView(LoginRequiredMixin, ManagerVisibleQuerysetMixin, ListView):
    model = Message
    template_name = 'message_list.html'
    context_object_name = 'messages'


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_form.html'
    success_url = reverse_lazy('main:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        flash.success(self.request, 'Сообщение добавлено.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Добавить сообщение'
        return ctx


class MessageUpdateView(OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_form.html'
    success_url = reverse_lazy('main:message_list')

    def form_valid(self, form):
        flash.success(self.request, 'Сообщение обновлено.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать сообщение'
        return ctx


class MessageDeleteView(OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = 'message_confirm_delete.html'
    success_url = reverse_lazy('main:message_list')

    def form_valid(self, form):
        flash.success(self.request, 'Сообщение удалено.')
        return super().form_valid(form)


# ==========================================
# 5. Рассылки (Newsletter)
# ==========================================

class NewsletterListView(LoginRequiredMixin, ManagerVisibleQuerysetMixin, ListView):
    model = Newsletter
    template_name = 'newsletter_list.html'
    context_object_name = 'newsletters'

    def get_queryset(self):
        qs = super().get_queryset().select_related('message')
        if self.request.GET.get('filter') == 'active':
            now = timezone.now()
            qs = qs.filter(
                first_sent_at__lte=now,
                end_at__gte=now,
                status=Newsletter.STATUS_STARTED,
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for n in ctx['newsletters']:
            n.update_status()
        ctx['filter_param'] = self.request.GET.get('filter')
        return ctx


class NewsletterDetailView(LoginRequiredMixin, ManagerVisibleQuerysetMixin, DetailView):
    model = Newsletter
    template_name = 'newsletter_detail.html'
    context_object_name = 'newsletter'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['attempts'] = self.object.attempts.select_related('recipient').all()
        ctx['can_edit'] = self.object.owner_id == self.request.user.id
        return ctx


class NewsletterCreateView(LoginRequiredMixin, CreateView):
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletter_form.html'
    success_url = reverse_lazy('main:newsletter_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        flash.success(self.request, 'Рассылка создана.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Создать рассылку'
        return ctx


class NewsletterUpdateView(OwnerRequiredMixin, UpdateView):
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletter_form.html'
    success_url = reverse_lazy('main:newsletter_list')

    def form_valid(self, form):
        flash.success(self.request, 'Рассылка обновлена.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать рассылку'
        return ctx


class NewsletterDeleteView(OwnerRequiredMixin, DeleteView):
    model = Newsletter
    template_name = 'newsletter_confirm_delete.html'
    success_url = reverse_lazy('main:newsletter_list')

    def form_valid(self, form):
        flash.success(self.request, 'Рассылка удалена.')
        return super().form_valid(form)


class NewsletterSendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        newsletter = get_object_or_404(Newsletter, pk=pk, owner=request.user)
        attempts = send_newsletter(newsletter)

        if not attempts:
            flash.error(request, 'Отправка не выполнена: нет получателей или рассылка завершена.')
        else:
            success = sum(1 for a in attempts if a.status == Attempt.STATUS_SUCCESS)
            flash.success(request, f'Отправка завершена: успешно {success} из {len(attempts)}.')
        return redirect('main:newsletter_detail', pk=pk)

    def get(self, request, pk):
        return redirect('main:newsletter_detail', pk=pk)


# ==========================================
# 6. Статистика
# ==========================================
@method_decorator(cache_page(60), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class StatsView(LoginRequiredMixin, TemplateView):
    template_name = 'stats.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
    
        qs = Newsletter.objects.all() if is_manager(user) else Newsletter.objects.filter(owner=user)
        
        mailings = (
            qs.annotate(
                total=Count('attempts'),
                successful=Count('attempts', filter=Q(attempts__status=Attempt.STATUS_SUCCESS)),
                failed=Count('attempts', filter=Q(attempts__status=Attempt.STATUS_FAILED)),
            )
            .order_by('-pk')
        )
        ctx['summary'] = get_user_stats(user)
        ctx['mailings'] = mailings
        return ctx


# ==========================================
# 7. Действия менеджеров (Права)
# ==========================================

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список пользователей. Доступен ТОЛЬКО менеджерам."""
    model = User
    template_name = 'user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return is_manager(self.request.user)

    def get_queryset(self):
        # Исключаем суперюзеров и самого себя
        return User.objects.exclude(is_superuser=True).exclude(pk=self.request.user.pk)


class BlockUserView(PermissionRequiredMixin, View):
    """Блокировка пользователя (требует спец. права)."""
    permission_required = 'main.can_block_users'
    raise_exception = True  

    def post(self, request, user_id):
        user_to_block = get_object_or_404(User, pk=user_id)
        
        if user_to_block == request.user:
            flash.error(request, "Вы не можете заблокировать самого себя.")
            return redirect('main:user_list')
            
        if user_to_block.is_superuser:
            flash.error(request, "Нельзя заблокировать суперпользователя.")
            return redirect('main:user_list')

        user_to_block.is_active = not user_to_block.is_active
        user_to_block.save()

        action = "разблокирован" if user_to_block.is_active else "заблокирован"
        flash.success(request, f'Пользователь {user_to_block.username} {action}.')
        
        return redirect('main:user_list')


class DisableNewsletterView(PermissionRequiredMixin, View):
    """Принудительное отключение рассылки (требует спец. права)."""
    permission_required = 'main.can_disable_newsletters'
    raise_exception = True

    def post(self, request, pk):
        newsletter = get_object_or_404(Newsletter, pk=pk)
        
        if newsletter.status != Newsletter.STATUS_FINISHED:
            newsletter.status = Newsletter.STATUS_FINISHED
            newsletter.save(update_fields=['status'])
            flash.success(request, f'Рассылка #{newsletter.pk} принудительно отключена.')
        else:
            flash.info(request, f'Рассылка #{newsletter.pk} уже отключена.')
            
        return redirect(request.META.get('HTTP_REFERER', 'main:newsletter_list'))