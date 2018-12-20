from datetime import date, datetime
from django.contrib import admin, messages

# Register your models here.
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect

from core.forms import ParameterForBaseForm, BaseUserCreationForm, BaseUserChangeForm, ParametersUserForm
from core.models import ParameterForBase, UsuarioBase, ParametersUser
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class ParametroAdmin(admin.ModelAdmin):
    list_display = ('nomeProjeto', 'tituloProjeto', 'descricaoProjeto')
    form = ParameterForBaseForm

    def changelist_view(self, request, extra_context=None):
        obj = ParameterForBase.objects.first()
        if obj:
            return HttpResponseRedirect("%s/" % obj.pk)
        return super(ParametroAdmin, self).changelist_view(request, extra_context)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return not ParameterForBase.objects.all().exists()


class ParametersUserAdmin(admin.ModelAdmin):
    form = ParametersUserForm
    list_display = ('id', 'mim_tamanho', 'max_tamanho', 'dias_expirar', 'qtde_numero',
                    'qtde_caracter', 'bloquear_sequencia_caracter', 'usuario_matricula', 'combinar_numero_caracter')
    list_editable = ('mim_tamanho', 'max_tamanho', 'qtde_numero',
                     'qtde_caracter', 'dias_expirar', 'bloquear_sequencia_caracter', 'usuario_matricula',
                     'combinar_numero_caracter')

    fieldsets = [
        (u'Configurações Basica', {'fields': (('mim_tamanho', 'max_tamanho',),
                                              ('dias_expirar', 'bloquear_usuario'),
                                              ('qtde_verificar_similares', 'senha_padrao'),
                                              ('bloquear_sequencia_caracter', 'busca_dados_matricula'),
                                              ('usuario_matricula', 'editar_dados_perfil',),
                                              )}),
        (u'Numeros e Caracteres', {'fields': (('combinar_numero_caracter',
                                               'qtde_numero', 'qtde_caracter'),
                                              )}),
        (u'Maiuscula e Minuscula', {'fields': (('combinar_maiuscula_minuscula',
                                                'qtde_maiuscula', 'qtde_minuscula'),
                                               )}),
    ]


    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect("%s/" % ParametersUser.objects.first().id)


class UsuarioInline(admin.StackedInline):
    model = UsuarioBase
    max_num = 1
    extra = 1
    can_delete = False
    # readonly_fields = ['matricula','servidor','cod_setor','setor','cod_cargo','cargo','cod_funcao','funcao',
    #                    'cod_vinculo','vinculo','secretaria','cod_unidade_gestora','data_admissao','data_desligamento',
    #                    'localizacao','ativo','exonerado','mes_referencia','ano_referencia','data_atualizacao', 'prodata',
    #                    ]

    def get_readonly_fields(self, request, obj=None):
        try:
            if not obj.usuario is None and obj.usuario.prodata:
                self.readonly_fields = ['matricula', 'servidor', 'cod_setor', 'setor', 'cod_cargo', 'cargo', 'cod_funcao',
                                   'funcao',
                                   'cod_vinculo', 'vinculo', 'secretaria', 'cod_unidade_gestora', 'data_admissao',
                                   'data_desligamento',
                                   'localizacao', 'ativo', 'exonerado', 'mes_referencia', 'ano_referencia',
                                   'data_atualizacao', 'prodata',
                                   ]
            else:
                self.readonly_fields = ['prodata',]
        except:
            self.readonly_fields = ['prodata', ]

        return self.readonly_fields


class UserDjangoAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_grupos', 'is_staff', 'is_active')

    readonly_fields = ("last_login", 'date_joined')
    actions = ['resetar_senha', 'ativar_usuario', 'inativar_usuario', ]
    change_form_template = 'admin/auth/user/change_form.html'

    add_form = BaseUserCreationForm
    form = BaseUserChangeForm

    def get_grupos(self, obj):
        return "\n".join([p.name for p in obj.groups.all()])
    get_grupos.short_description = 'Grupos'

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)

        form = super(UserDjangoAdmin, self).get_form(request, obj, **defaults)
        form.user = request.user

        return form

    def resetar_senha(self, request, queryset):
        for obj in queryset:
            obj.set_password(ParametersUser.objects.first().senha_padrao)
            obj.save()
        self.message_user(request, u'Senhas resetadas com sucesso', level=messages.INFO)

    resetar_senha.short_description = "Resetar Senha"

    def ativar_usuario(self, request, queryset):
        for obj in queryset:
            obj.set_password(ParametersUser.objects.first().senha_padrao)
            obj.is_active = True
            obj.last_login = datetime.today()
            obj.save()
        self.message_user(request, u'Usuarios ativo com sucesso.', level=messages.INFO)

    ativar_usuario.short_description = "Ativar Usuários"

    def inativar_usuario(self, request, queryset):
        for obj in queryset:
            obj.is_active = False
            obj.save()
        self.message_user(request, u'Usuarios inativo com sucesso.', level=messages.INFO)

    inativar_usuario.short_description = "Inativar Usuários"

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            self.inlines= []
        else:
            self.inlines = [UsuarioInline]

        return super(UserDjangoAdmin, self).get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        try:

            if change:
                if obj.is_superuser and not request.user.is_superuser:
                    self.message_user(request, u'Você não tem permissão para salvar um Usuario como SUPER USER.',
                                      level=messages.ERROR)
                    return HttpResponseRedirect('../' + str(obj.id) + '/')
                obj.save()
            else:
                if obj and hasattr(obj,'usuariobase') and obj.usuariobase:
                    usuario_perfil = obj.usuariobase
                else:
                    usuario_perfil = UsuarioBase()
                usuario_perfil.user = obj
                usuario_perfil.preencher_dados_via_integracao()
                obj.save()
                usuario_perfil.user = obj
                usuario_perfil.save()
        except Exception as e:
            pass


admin.site.unregister(User)
admin.site.register(User, UserDjangoAdmin)

admin.site.register(ParameterForBase, ParametroAdmin)
admin.site.register(ParametersUser, ParametersUserAdmin)
