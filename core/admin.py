from datetime import date, datetime
from django.contrib import admin, messages

# Register your models here.
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect

from core.forms import ParameterForBaseForm, ParametersUserForm
from core.models import ParameterForBase, ParametersUser
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class ParametroAdmin(admin.ModelAdmin):
    list_display = ('nomeProjeto', 'tituloProjeto', 'descricaoProjeto')
    form = ParameterForBaseForm

    def changelist_view(self, request, extra_context=None):
        obj = ParameterForBase.objects.first()
        if obj:
            return HttpResponseRedirect("%s/" % obj.pk)
        return super(ParametroAdmin, self).changelist_view(
            request, extra_context
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return not ParameterForBase.objects.all().exists()


class ParametersUserAdmin(admin.ModelAdmin):
    form = ParametersUserForm

    fieldsets = [
        (u'Configurações Basica', {'fields': (('senha_padrao'),
                                              )}),
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect("%s/" % ParametersUser.objects.first().id)


class UserCoreAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name',
        'last_name', 'get_grupos', 'is_staff',
        'is_active'
    )

    readonly_fields = ("last_login", 'date_joined')
    actions = ['resetar_senha', 'ativar_usuario', 'inativar_usuario', ]

    def get_grupos(self, obj):
        return "\n".join([p.name for p in obj.groups.all()])
    get_grupos.short_description = 'Grupos'

    def resetar_senha(self, request, queryset):
        for obj in queryset:
            obj.set_password(ParametersUser.objects.first().senha_padrao)
            obj.save()
        self.message_user(
            request, u'Senhas resetadas com sucesso', level=messages.INFO)

    resetar_senha.short_description = "Resetar Senha"

    def ativar_usuario(self, request, queryset):
        for obj in queryset:
            obj.set_password(ParametersUser.objects.first().senha_padrao)
            obj.is_active = True
            obj.last_login = datetime.today()
            obj.save()
        self.message_user(
            request, u'Usuarios ativo com sucesso.', level=messages.INFO)

    ativar_usuario.short_description = "Ativar Usuários"

    def inativar_usuario(self, request, queryset):
        for obj in queryset:
            obj.is_active = False
            obj.save()
        self.message_user(
            request, u'Usuarios inativo com sucesso.', level=messages.INFO)

    inativar_usuario.short_description = "Inativar Usuários"

    def save_model(self, request, obj, form, change):
        try:

            if change:
                if obj.is_superuser and not request.user.is_superuser:
                    self.message_user(
                        request,
                        u'Você não tem permissão para salvar um \
                            Usuario como SUPER USER.',
                        level=messages.ERROR
                    )
                    return HttpResponseRedirect('../' + str(obj.id) + '/')

                if (
                    '_resetar_senha_user' in request.POST
                    and request.user.is_superuser
                ):
                    obj.set_password(
                        ParametersUser.objects.first().senha_padrao)
                    self.message_user(
                        request,
                        u'Senha resetada com sucesso',
                        level=messages.INFO
                    )
                elif '_ativar_user' in request.POST:
                    obj.set_password("senha@123")
                    obj.is_active = True
                    obj.last_login = date.today()
                    self.message_user(
                        request,
                        u'Usuario ativado com sucesso',
                        level=messages.INFO
                    )
                elif '_inativar_user' in request.POST:
                    obj.is_active = False
                    self.message_user(
                        request,
                        u'Usuario inativado com sucesso',
                        level=messages.INFO
                    )
                obj.save()
            else:
                obj.save()
        except Exception as e:
            pass


admin.site.unregister(User)
admin.site.register(User, UserCoreAdmin)

admin.site.register(ParameterForBase, ParametroAdmin)
admin.site.register(ParametersUser, ParametersUserAdmin)
