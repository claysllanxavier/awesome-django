from django.contrib.auth.views import (
    PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView,
)
from django.urls import path, reverse_lazy

from core.forms import BasePasswordChangeForm, BasePasswordResetForm
from core.models import ParameterForBase
from core.views import IndexTemplateView, BaseLoginView, BaseLogoutView, BasePasswordResetCompleteView

app_name = 'core'
urlpatterns = [
    path('', IndexTemplateView.as_view(), name='index'),
    path('login/', BaseLoginView.as_view(), name='login'),
    path('logout/', BaseLogoutView.as_view(), name='logout'),

    path('password/change/', PasswordChangeView.as_view(
        template_name='outside_template/registration/password_change_form.html',
        success_url=reverse_lazy('core:password_change_done'),
        form_class=BasePasswordChangeForm,
        extra_context={'parameter': ParameterForBase.objects.first}), name='password_change'),

    path('password_change/done/', PasswordChangeDoneView.as_view(
        template_name='outside_template/registration/password_change_done.html',
        extra_context={'parameter': ParameterForBase.objects.first}), name='password_change_done'),

    path('password_reset/', PasswordResetView.as_view(
        template_name='outside_template/registration/password_reset_form.html',
        success_url=reverse_lazy('core:password_reset_done'),
        form_class=BasePasswordResetForm,
        extra_context={'parameter': ParameterForBase.objects.first},
        email_template_name='outside_template/registration/password_reset_email.html'), name="password_reset"),

    path('password_reset/done/', PasswordResetDoneView.as_view(
        template_name='outside_template/registration/password_reset_done.html',
        extra_context={'parameter': ParameterForBase.objects.first}), name="password_reset_done"),

    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='outside_template/registration/password_reset_confirm.html',
        success_url=reverse_lazy('core:password_reset_complete'),
        extra_context={'parameter': ParameterForBase.objects.first} ), name="password_reset_confirm"),

    path('reset/done/', BasePasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
