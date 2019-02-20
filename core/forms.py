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

import django
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       ReadOnlyPasswordHashField,
                                       UserChangeForm, UserCreationForm)
from django.contrib.auth.models import User
from django.forms.fields import ChoiceField, DateField, DateTimeField
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from core.models import Base, ParameterForBase, ParametersUser


class BaseForm(forms.ModelForm):
    """Form para ser usado no classe based views"""
    # Sobrescrevendo o Init para aplicar as regras CSS

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.readonly_fields = kwargs.pop('readonly_fields', None)
        super(BaseForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            class_attrs = ""
            if hasattr(self.fields[field], 'widget') and \
                    hasattr(self.fields[field].widget, 'attrs') and\
                    'class' in self.fields[field].widget.attrs:
                class_attrs = self.fields[field].widget.attrs['class']

            # Verificando se o campo é do tipo DateTime
            if isinstance(self.fields[field], DateTimeField) is True:
                class_attrs = "{} {}".format(class_attrs, 'datetimefield')
            # Verificando se o campo é do do Date
            elif isinstance(self.fields[field], DateField) is True:
                class_attrs = "{} {}".format(class_attrs, 'datefield')
            # Verificando se o campo é do tipo ChoiceField
            elif isinstance(self.fields[field], ChoiceField) is True:
                class_attrs = "{} {}".format(class_attrs, 'select')

            # Atualizando os atributos do campo para adicionar as classes
            # conforme as regras anteriores
            self.fields[field].widget.attrs.update({
                'class': class_attrs
            })

    def __iter__(self):
        for field in self.fields:
            if self.readonly_fields and field in self.readonly_fields:
                self[field].field.widget.attrs['readonly'] = True
                yield self[field]
            else:
                yield self[field]

    class Meta:
        model = Base
        exclude = ['enabled', 'deleted']


class ParameterForBaseForm(BaseForm):
    class Meta:
        model = ParameterForBase
        fields = '__all__'


class BasePasswordResetForm(PasswordResetForm):
    """
    formulario de envio de email para recuperação de senha
    """

    def clean_email(self):

        cleaned_data = self.cleaned_data.get('email')
        user = get_user_model().objects.filter(email=cleaned_data).first()

        if cleaned_data and not user:
            raise forms.ValidationError("O email informado, não foi encontrado! \
                                        Talvez você não tenha cadastrado"
                                        " seu email no perfil. Por favor, \
                                        entre em contado com o administrador \
                                        do sistema.")
        if not user.is_active:
            raise forms.ValidationError(
                "A conta relacionada a este e-mail está inativa. "
                "Por favor, entre em contato com o administrador do sistema")

        return cleaned_data


class ParametersUserForm(BaseForm):
    class Meta:
        model = ParametersUser
        fields = '__all__'
