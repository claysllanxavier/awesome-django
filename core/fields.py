# -*-coding:utf-8 -*-
from django.contrib.auth.password_validation import validate_password
from django.forms import CharField, PasswordInput
from django.core.validators import EMPTY_VALUES
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
import re
from django import forms


class CpfCnpjField(CharField):
    """
    This field validate a CPF number or a CPF string. A CPF number is
    compounded by XXX.XXX.XXX-VD. The two last digits are check digits. If it fails it tries to validate a CNPJ number or a CNPJ string. A CNPJ is compounded by XX.XXX.XXX/XXXX-XX.

    More information:
    http://en.wikipedia.org/wiki/Cadastro_de_Pessoas_Físicas
    """
    default_error_messages = {
        'invalid': _(u"CPF ou CNPJ inválido."),
        'digits_only': _(u"Este campo requer somente números."),
        'max_digits': _(u"Este campo requer no máximo 11 dígitos."),
        'invalid_cpf': _(u"CPF inválido."),
        'invalid_cnpj': _(u"CNPJ inválido."),
    }

    def __init__(self, max_length=None, min_length=None, cpfcnpj_required=True, *args, **kwargs):
        self.cpfcnpj_required = cpfcnpj_required
        self.max_length = max_length
        self.min_length = min_length
        super().__init__(**kwargs)

    def validate_CPF(self, value):
        """
        Value can be either a string in the format XXX.XXX.XXX-XX or an
        11-digit number.
        """
        if value in EMPTY_VALUES:
            return u''
        if not value.isdigit():
            value = re.sub("[-/\.]", "", value)
        orig_value = value[:]
        try:
            int(value)
        except ValueError:
            raise ValidationError(self.error_messages['digits_only'], code='digits_only')
        if len(value) != 11:
            raise ValidationError(self.error_messages['max_digits'], code='max_digits')
        orig_dv = value[-2:]

        new_1dv = sum([i * int(value[idx]) for idx, i in enumerate(range(10, 1, -1))])
        new_1dv = DV_maker(new_1dv % 11)
        value = value[:-2] + str(new_1dv) + value[-1]
        new_2dv = sum([i * int(value[idx]) for idx, i in enumerate(range(11, 1, -1))])
        new_2dv = DV_maker(new_2dv % 11)
        value = value[:-1] + str(new_2dv)

        if value[-2:] != orig_dv:
            raise ValidationError(self.error_messages['invalid_cpf'], code='invalid_cpf')
        return orig_value

    def validate_CNPJ(self, value, erro_cpf):
        ## Try to Validate CNPJ
        """
        Value can be either a string in the format XX.XXX.XXX/XXXX-XX or a
        group of 14 characters.
        """
        if erro_cpf != 'max_digits':
            raise ValidationError(self.error_messages[erro_cpf], code=erro_cpf)

        if value in EMPTY_VALUES:
            return u''
        if not value.isdigit():
            value = re.sub("[-/\.]", "", value)
        orig_value = value[:]
        try:
            int(value)
        except ValueError:
            raise ValidationError(self.error_messages['digits_only'], code='digits_only')
        if len(value) != 14:
            raise ValidationError(self.error_messages['max_digits'], code='max_digits')
        orig_dv = value[-2:]

        new_1dv = sum([i * int(value[idx]) for idx, i in enumerate(range(5, 1, -1) + range(9, 1, -1))])
        new_1dv = DV_maker(new_1dv % 11)
        value = value[:-2] + str(new_1dv) + value[-1]
        new_2dv = sum([i * int(value[idx]) for idx, i in enumerate(range(6, 1, -1) + range(9, 1, -1))])
        new_2dv = DV_maker(new_2dv % 11)
        value = value[:-1] + str(new_2dv)
        if value[-2:] != orig_dv:
            raise ValidationError(self.error_messages['invalid_cnpj'], code='invalid_cnpj')

        return orig_value

    def clean(self, value):

        value = super(CpfCnpjField, self).clean(value)
        if self.cpfcnpj_required or value.isdigit():
            try:
                orig_value = self.validate_CPF(value)
            except ValidationError as err:
                orig_value = self.validate_CNPJ(value, err.code)

            return re.sub("[-/\.]", "", orig_value)
        return value