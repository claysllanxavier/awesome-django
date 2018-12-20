"""Arquivo Forms para retornar os campos com os atributos do Bootstrap

<class 'django.forms.fields.BooleanField'>
<class 'django.forms.models.ModelChoiceField'>
<class 'django.forms.fields.CharField'>
<class 'django.forms.fields.EmailField'>
<class 'django.forms.fields.URLField'>
<class 'django.forms.fields.TypedChoiceField'>
<class 'django.forms.fields.DecimalField'>
<class 'django.forms.fields.FloatField'>
<class 'django.forms.fields.IntegerField'>
<class 'django.forms.fields.IntegerField'>
<class 'django.forms.fields.CharField'>
<class 'django.forms.fields.BooleanField'>
<class 'django.forms.fields.DateField'>
<class 'django.forms.fields.DateTimeField'>

"""
from datetime import datetime
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, ReadOnlyPasswordHashField, UserChangeForm, PasswordChangeForm, \
    PasswordResetForm
from django.contrib.auth.models import User
from django.forms.fields import DateField, DateTimeField
from django.utils.translation import gettext, gettext_lazy as _

from core.fields import MatriculaField, PasswordField
from core.models import ParameterForBase, UsuarioBase, HistoricoSenha, ParametersUser
from core.validators import get_parametros
from core.models import Base
import django


class BaseForm(forms.ModelForm):
    """Form para ser usado no classe based views"""
    # Sobrescrevendo o Init para aplicar as regras CSS
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(BaseForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            class_attrs = ""
            if hasattr(self.fields[field],'widget') and \
                    hasattr(self.fields[field].widget, 'attrs') and\
                    'class' in self.fields[field].widget.attrs:
                class_attrs = self.fields[field].widget.attrs['class']

            class_attrs =  "{} {}".format(class_attrs, 'form-control')
            # Verificando se o campo está configurado como obrigatório
            # Foi retirado os campos do tipo checkbox, pois da problema de validação obrigando que marque todos
            if self.fields[field].required and (
                    not hasattr(self.fields[field].widget, 'input_type') or (
                    hasattr(self.fields[field].widget, 'input_type')
                    and self.fields[field].widget.input_type != 'checkbox')):
                class_attrs = "{} {}".format(class_attrs, 'obrigatorio')

            # Verificando se o campo é checkbox tanto para choices quanto para BooleanField
            if hasattr(self.fields[field].widget, 'input_type') and (
                    self.fields[field].widget.input_type == 'checkbox' or
                    self.fields[field].widget.input_type == 'radio'):

                if self.fields[field].widget.input_type == 'radio':
                    class_attrs = "{} {}".format(class_attrs, 'custom-control-input')
                else:
                    class_attrs = "{} {}".format(class_attrs, 'form-check-input')

                class_attrs = class_attrs.replace('form-control', '')

            # Verificando se o campo é do tipo DateTime
            elif isinstance(self.fields[field], DateTimeField) is True:
                class_attrs = "{} {}".format(class_attrs, 'datetimefield')
            # Verificando se o campo é do do Date
            elif isinstance(self.fields[field], DateField) is True:
                class_attrs = "{} {}".format(class_attrs, 'datefield')

            # está usando o padrão por questão de dificudade de colocar no bootstrap4
            # if isinstance(self.fields[field], FileField) is True:
                # self.fields[field].widget.template_name = 'outside_template/forms/widgets/clearable_file_input.html'
                # class_attrs = "{} {}".format(class_attrs, 'custom-file-input')
            # if isinstance(self.fields[field], ImageField) is True:
                # self.fields[field].widget.template_name = 'outside_template/forms/widgets/clearable_file_input.html'
                # class_attrs = "{} {}".format(class_attrs, 'custom-file-input')

            # Atualizando os atributos do campo para adicionar as classes
            # conforme as regras anteriores
            self.fields[field].widget.attrs.update({
                'class': class_attrs
            })

    class Meta:
        model = Base
        exclude = ['enabled', 'deleted']


class ParameterForBaseForm(BaseForm):
    class Meta:
        model = ParameterForBase
        fields = '__all__'


class ParametersUserForm(BaseForm):
    class Meta:
        model = ParametersUser
        fields = '__all__'


    def clean(self):
        cleaned_data = super(ParametersUserForm, self).clean()
        combinar_numero_caracter = self.cleaned_data.get("combinar_numero_caracter", False)
        if combinar_numero_caracter:
            qtde_numero = self.cleaned_data.get("qtde_numero", 0)
            qtde_caracter = self.cleaned_data.get("qtde_caracter", 0)
            max_tamanho = self.cleaned_data.get("max_tamanho", 0)

            if qtde_numero + qtde_caracter > max_tamanho:
                raise forms.ValidationError("A soma de 'Quantidade mínima de números' com a "
                                        "'Quantidade mínima de caracteres' exede o valor 'Quantidade máxima de caracteres'!",
                    code='max_tamanho')

        return cleaned_data


    def clean_mim_tamanho(self):
        """
         Definindo uma validação para não colocar menos do que o valor que o Django definiu
        """
        mim_tamanho = self.cleaned_data.get("mim_tamanho",0)
        if mim_tamanho < 8:
            raise forms.ValidationError('O valor minimo não pode ser menor do que 8. '
                                                            '(Valor minimo do Django para senhas)',
                code='mim_tamanho')
        return mim_tamanho


class BaseUserCreationForm(UserCreationForm):
    password1 = PasswordField(label="Password", required=False)
    password2 = PasswordField(label="Password confirmation", required=False)

    class Meta:
        fields = '__all__'
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super(BaseUserCreationForm, self).__init__(*args, **kwargs)
        if get_parametros().busca_dados_matricula or get_parametros().usuario_matricula:
            if get_parametros().usuario_matricula:
                self.fields['username'] = MatriculaField(label=u"Matricula",
                                                       help_text="Requeridos. 30 numeros ou menos.",
                                                       error_messages={'invalid': "Este valor pode conter apenas números."})
            else:
                self.fields['username'] = MatriculaField( label=u"Matricula", required=False,
                                                       help_text="Requeridos. 30 numeros ou menos.",
                                                       error_messages={'invalid': "Este valor pode conter apenas números."})
        else:
            self.fields['username'] = MatriculaField(max_length=30, label='Matricula',
                                                       help_text="Requeridos. 30 numeros ou menos.",
                                                       error_messages={'invalid': "Este valor pode conter apenas números."})
        self.fields['password1'].widget = forms.HiddenInput()
        self.fields['password2'].widget = forms.HiddenInput()

    def clean_username(self):
        """
        Foi necessário estender esta classe, pois quando é alterado o AUTH_USER_MODEL
        é necessário alterar o objeto que está sendo utilizado para a verificação.
        A mesma possui a mesma lógica da função original, apenas alterado a maneira como é obtido o user model.
        """
        username = self.cleaned_data["username"]
        if django.VERSION[0] == 1 and django.VERSION[1] <= 7:  # version 1.7-
            user = get_user_model()
            try:
                user._default_manager.get(username=username)
            except user.DoesNotExist:
                return username
            raise forms.ValidationError(
                self.error_messages['duplicate_username'],
                code='duplicate_username',
            )
        return username

    def clean(self):
        cleaned_data = super(BaseUserCreationForm, self).clean()
        if hasattr(self, 'request'):
            username = self.cleaned_data.get("username", self.request.POST.get('username'))
        elif hasattr(self, 'data') and 'username' in self.data:
            username = self.cleaned_data.get("username", self.data['username'])
        else:
            username = self.cleaned_data.get("username", None)
        self.cleaned_data['password1'] = get_parametros().senha_padrao
        self.cleaned_data['password2'] = get_parametros().senha_padrao
        try:
            usuario = UsuarioBase()
            usuario.matricula = username
            usuario.preencher_dados_via_integracao()
        except Exception as e:
            raise forms.ValidationError(
                u"Ocorreu um erro ao consultar os dados do usuário. Aguarde alguns instantes e tente "
                u"novamente. Caso o erro persista, entre em contato com o administrador do sistema.")
        if get_parametros().busca_dados_matricula and not usuario and not get_parametros().editar_dados_perfil:
            raise forms.ValidationError(
                u"Não foi encontrado nenhum colaborador cadastrado com essa Matricula ou o mesmo não possui matrícula ativa! Somente servidores com matrícula ativa podem ser cadastrados.")
        if get_parametros().busca_dados_matricula and usuario and not usuario.ativo:
            raise forms.ValidationError(u"O cadastro do calaborador %s não está ATIVO! Por favor, entre em contato com Administrador." % usuario.servidor)

        return cleaned_data



class BaseUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField()
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super(BaseUserChangeForm, self).__init__(*args, **kwargs)

        if get_parametros().busca_dados_matricula or get_parametros().usuario_matricula:
            if get_parametros().usuario_matricula:
                self.fields['username'] = MatriculaField(label=u"Matricula",
                                                          help_text="Requeridos no maximo 30 numeros ou menos.",
                                                          error_messages={'invalid': "Este valor pode conter apenas números."})
            else:
                self.fields['username'] = MatriculaField(label=u"Matricula", required=False,
                                                          help_text="Requeridos no maximo 30 numeros ou menos.",
                                                          error_messages={'invalid': "Este valor pode conter apenas números."})
        else:
            self.fields['username'] = forms.CharField(max_length=30, label='Matricula',
                                                       help_text="Requeridos no maximo 30 caracteres.")


    class Meta:
        widgets = {'is_active': forms.HiddenInput()}

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.exclude(id=self.instance.id).filter(email=email).exists():
            raise forms.ValidationError(_("Já tem usuario com este email"), code='invalid')

        return email


    def clean(self):
        cleaned_data = super(BaseUserChangeForm, self).clean()
        if hasattr(self, 'request'):
            username = self.cleaned_data.get("username", self.request.POST.get('username'))
        elif hasattr(self, 'data') and 'username' in self.data:
            username = self.cleaned_data.get("username", self.data['username'])
        else:
            username = self.cleaned_data.get("username", None)

        try:
            usuario = UsuarioBase()
            usuario.matricula = username
            usuario.preencher_dados_via_integracao()
        except Exception as e:
            raise forms.ValidationError(_("Ocorreu um erro ao consultar os dados do usuário. Aguarde alguns instantes e tente"
                                         "  novamente. Caso o erro persista, entre em contato com o administrador do sistema."))

        if get_parametros().busca_dados_matricula and not usuario and not get_parametros().editar_dados_perfil:
            raise forms.ValidationError(
                "Não foi encontrado nenhum colaborador cadastrado com essa Matricula ou o mesmo não possui matrícula ativa! Somente servidores com matrícula ativa podem ser cadastrados.")
        if get_parametros().busca_dados_matricula and usuario and not usuario.ativo:
            raise forms.ValidationError("O cadastro do calaborador %s não está ATIVO! Por favor, entre em contato com Administrador." % usuario.servidor)
        return cleaned_data



class BasePasswordChangeForm(PasswordChangeForm):
    new_password2 = PasswordField(label=_("New password confirmation"), min_length=6)

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.new_password1 = PasswordField(label=_("New password"), user=self.user, min_length=6)

    def save(self, commit=True):
        historico = HistoricoSenha()
        if historico.primeiro_acesso(self.user) and self.user.is_active and not self.user.is_superuser:
            self.user.last_login = datetime.now()
        super(BasePasswordChangeForm, self).save(commit=commit)
        return self.user



class BasePasswordResetForm(PasswordResetForm):
    """
    formulario de envio de email para recuperação de senha
    """
    def clean_email(self):

        cleaned_data = self.cleaned_data.get('email')
        user = get_user_model().objects.filter(email=cleaned_data).first()

        if cleaned_data and not user:
            raise forms.ValidationError("O email informado, não foi encontrado! Talvez você não tenha cadastrado"
                                        " seu email no perfil. Por favor, entre em contado com o administrador do sistema." )

        if user and user.last_login:
            dias_sem_logar = (datetime.now() - user.last_login.replace(tzinfo=None)).days
        elif user:
            dias_sem_logar = (datetime.now() - user.date_joined.replace(tzinfo=None)).days
        else:
            dias_sem_logar = None

        if dias_sem_logar >= get_parametros().bloquear_usuario and not user.is_active \
                and not user.is_superuser and get_parametros().bloquear_usuario > 0:
            raise forms.ValidationError(
                "A conta relacionada a este e-mail está inativa, pois esse usuario não acessa o sistema a mais de %s dias. "
                "Por favor, entre em contato com o administrador do sistema" % get_parametros().bloquear_usuario)
        if not user.is_active:
            raise forms.ValidationError(
                "A conta relacionada a este e-mail está inativa. "
                "Por favor, entre em contato com o administrador do sistema")

        return cleaned_data
