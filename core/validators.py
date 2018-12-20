
from __future__ import division
import string
from core.models import ParametersUser, HistoricoSenha
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db import connection



def get_parametros():
    if 'core_parametersuser' in connection.introspection.table_names():
        if not ParametersUser.objects.exists():
            ParametersUser.objects.create()
        return ParametersUser.objects.first()
    return ParametersUser()

class LengthValidator(object):
    message = _(u"A senha (%s)")
    code = "length"

    def __init__(self, min_length=None, max_length=None):
        self.min_length = min_length
        self.max_length = max_length

    def __call__(self, value):
        if get_parametros() and hasattr(get_parametros(),'mim_tamanho') and get_parametros().mim_tamanho:
            self.min_length = get_parametros().mim_tamanho or self.min_length
        if get_parametros() and hasattr(get_parametros(),'max_tamanho') and get_parametros().max_tamanho:
            self.max_length = get_parametros().max_tamanho or self.max_length

        if self.min_length and len(value) < self.min_length:
            raise ValidationError(
                self.message % _(u"Deve conter %s caracteres ou mais") % self.min_length,
                code=self.code)
        elif self.max_length and len(value) > self.max_length:
            raise ValidationError(
                self.message % _(u"Deve conter %s caracteres ou menos") % self.max_length,
                code=self.code)

class ComplexityValidator(object):
    message = _(u"A senha deve ser mais complexa (%s)")
    code = "complexity"

    def __init__(self, complexities):
        self.complexities = complexities

    def __call__(self, value):
        # faz uma validação para não ir objetos nulos
        if self.complexities is None or not get_parametros() or not hasattr( get_parametros(),'complexidade_senha') \
                or not get_parametros().complexidade_senha():
            return
        # coloca em tempo real os parametros vindo do banco, antes sem essa linha só pegava novos valores quando reiniciava a aplicação
        self.complexities = get_parametros().complexidade_senha() or self.complexities

        vect_uppercase, vect_lowercase, vect_digits, vect_non_ascii, vect_punctuation = [], [], [], [], []

        for character in value:
            if character.isdigit():
                vect_digits.append(character)
            else:
                vect_non_ascii.append(character)

            if character.isupper():
                vect_uppercase.append(character)
            elif character.islower():
                vect_lowercase.append(character)
            elif character in string.punctuation:
                vect_punctuation.append(character)

        words = set(value.split())

        if len(vect_uppercase) < self.complexities.get("UPPER", 0):
            raise ValidationError(
                self.message % _(u"Deve conter %(UPPER)s caracteres ou mais em maiúsculas \n") % self.complexities,
                code=self.code)
        elif len(vect_lowercase) < self.complexities.get("LOWER", 0):
            raise ValidationError(
                self.message % _(u"Deve conter %(LOWER)s ou mais caracteres minúsculos \n") % self.complexities,
                code=self.code)
        elif len(vect_digits) < self.complexities.get("DIGITS", 0):
            raise ValidationError(
                self.message % _(u"Deve conter %(DIGITS)s ou mais números \n") % self.complexities,
                code=self.code)
        elif len(vect_punctuation) < self.complexities.get("PUNCTUATION", 0):
            raise ValidationError(
                self.message % _(u"Deve conter %(PUNCTUATION)s ou mais caractere com pontuação \n") % self.complexities,
                code=self.code)
        elif len(vect_non_ascii) < self.complexities.get("NON ASCII", 0):
            raise ValidationError(
                self.message % _(u"Deve conter %(NON ASCII)s ou mais letras. \n") % self.complexities,
                code=self.code)
        elif len(words) < self.complexities.get("WORDS", 0):
            raise ValidationError(
                self.message % _(u"Deve conter %(WORDS)s palavras ou mais exclusivas \n") % self.complexities,
                code=self.code)


class BaseSimilarityValidator(object):
    message = _(u"Muito semelhante ao [%(haystacks)s] \n")
    code = "similarity"

    def __init__(self, haystacks=None):
        self.haystacks = haystacks if haystacks else []

    def fuzzy_substring(self, needle, haystack):
        needle, haystack = needle.lower(), haystack.lower()
        m, n = len(needle), len(haystack)

        if m == 1:
            if not needle in haystack:
                return -1
        if not n:
            return m

        row1 = [0] * (n+1)
        for i in range(0,m):
            row2 = [i+1]
            for j in range(0,n):
                cost = ( needle[i] != haystack[j] )
                row2.append(min(row1[j+1]+1, row2[j]+1, row1[j]+cost))
            row1 = row2
        return min(row1)

    def __call__(self, value):
        # faz uma validação para não ir objetos nulos
        # coloca em tempo real, caso tenha os parametros vindo do banco, antes sem essa linha só pegava novos valores quando reiniciava a aplicação
        if get_parametros() and hasattr(get_parametros(),'bloquear_sequencias') and get_parametros().bloquear_sequencias():
            self.haystacks = get_parametros().bloquear_sequencias() or self.haystacks

        for haystack in self.haystacks:
            distance = self.fuzzy_substring(value, haystack)
            longest = max(len(value), len(haystack))
            similarity = (longest - distance) / longest
            if similarity >= 0.92:
                raise ValidationError(
                    self.message % {"haystacks": ", ".join(self.haystacks)},
                    code=self.code)

class DictionaryValidator(BaseSimilarityValidator):
    message = _(u"Com base em uma palavra do dicionário. \n")
    code = "dictionary_word"

    def __init__(self, words=None, dictionary=None):
        haystacks = []
        if dictionary:
            with open(dictionary) as dictionary:
                haystacks.extend(
                    [x.strip() for x in dictionary.readlines()]
                )
        if words:
            haystacks.extend(words)
        super(DictionaryValidator, self).__init__(haystacks=haystacks)


class CommonSequenceValidator(BaseSimilarityValidator):
    message = _(u"Não é permitido seqüência comum de caracteres. \n")
    code = "common_sequence"


class PasswordUsedValidator(object):
    message = _(u"Não é possivel utilizar esse Senha, pois a mesma já foi utilizada nas ultimas %s alterações")
    code = "password_used"
    user = None

    def __init__(self, qtde_similares=None):
        self.qtde_similares = qtde_similares

    def __call__(self, value):
        if not self.qtde_similares is None or not get_parametros() or not hasattr( get_parametros(),'qtde_verificar_similares') \
                or not get_parametros().qtde_verificar_similares:
            return None
        self.qtde_similares = get_parametros().qtde_verificar_similares or self.qtde_similares

        if self.qtde_similares > 0 or get_parametros().senha_padrao == value:
            for historico in HistoricoSenha.objects.filter(user=self.user):
                if check_password(value,historico.password):
                    raise ValidationError(
                        self.message % self.qtde_similares,
                        code=self.code)


validate_length = LengthValidator(get_parametros().mim_tamanho, get_parametros().max_tamanho)
complexity = ComplexityValidator(get_parametros().complexidade_senha())
dictionary_words = DictionaryValidator(dictionary=None)
common_sequences = CommonSequenceValidator(get_parametros().bloquear_sequencias())
password_used = PasswordUsedValidator(get_parametros().qtde_verificar_similares)
