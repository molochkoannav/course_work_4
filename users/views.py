from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from .forms import LoginForm, RegisterForm, ProfileEditForm


# ============================================================
# Вход
# ============================================================

class UserLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('users:profile')


# ============================================================
# Выход
# ============================================================

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')


# ============================================================
# Профиль (обрабатывает GET и POST)
# ============================================================

class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'
    login_url = reverse_lazy('users:login')

    def get(self, request, *args, **kwargs):
        form = ProfileEditForm(instance=request.user)
        return render(request, self.template_name, {
            'form': form,
            'title': 'Личный кабинет',
        })

    def post(self, request, *args, **kwargs):
        form = ProfileEditForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('users:profile')
        # если форма невалидна — рендерим ту же страницу с ошибками
        return render(request, self.template_name, {
            'form': form,
            'title': 'Личный кабинет',
        })


# ============================================================
# Регистрация
# ============================================================

class RegisterView(View):
    template_name = 'users/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:profile')
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:profile')

        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('users:profile')

        messages.error(request, 'Исправьте ошибки в форме')
        return render(request, self.template_name, {'form': form})
