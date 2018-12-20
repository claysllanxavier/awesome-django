import itertools
from django import template

from django.template.defaultfilters import stringfilter

register = template.Library()


@register.simple_tag(takes_context=True)
def get_ip(context):
    """Template tag to get user IP"""
    request = context['request']
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# pegar um atributo de um dicionario
# motivo: No template não acessa var que começa com _
@register.filter(name='get')
def get(d, k):
    return d.get(k, None)


# Retorna os fields manytomany
@register.filter(name='get_many_to_many')
def get_many_to_many(obj, object_list):
    manytomany_name = []
    manytomany = []
    for field in obj._meta.many_to_many:
        manytomany_name.append(field._m2m_reverse_name_cache)

    for item in object_list:
        try:
            if item[1].target_field_name in manytomany_name:
                manytomany.append(item[1])
        except Exception:
            pass

    return manytomany


@register.filter(name='include_empty_form')
def include_empty_form(formset):
    """
    Certifique-se de que o "formulário vazio" esteja incluído ao exibir um formset (geralmente tabela com linhas de entrada)

    Essa templatetag é usada para acrescentar o enpy_form na lista de formset, para poder ter os campos bases que vão ser add.
    """
    for form in formset:
        yield form
    if hasattr(formset, 'empty_form'):
        yield formset.empty_form


@register.filter()
def has_add_permission(model=None, request=None):
    """
    Verifica se o usuario tem a permissão de adicionar, no model passado

    ex: {if model|has_add_permission:request %}
    """
    if model and hasattr(model, 'has_add_permission') and request:
        return model.has_add_permission(request=request)
    else:
        return False


@register.filter()
def has_change_permission(model=None, request=None):
    """
    Verifica se o usuario tem a permissão de alterar, no model passado

    ex: {if model|has_change_permission:request %}
    """
    if model and hasattr(model, 'has_change_permission') and request:
        return model.has_change_permission(request=request)
    else:
        return False


@register.filter()
def has_delete_permission(model=None, request=None):
    """
    Verifica se o usuario tem a permissão de deletar, no model passado

    ex: {if model|has_delete_permission:request %}
    """
    if model and hasattr(model, 'has_delete_permission') and request:
        return model.has_delete_permission(request=request)
    else:
        return False


@register.filter(name='has_perm')
def has_perm(user, permissao):
    return user.has_perm(permissao)


@register.filter
@stringfilter
def split(string, sep):
    """Return the string split by sep.

    Example usage: {{ value|split:"/" }}
    """
    return string.split(sep)

@register.filter
def in_list(value, the_list):
    """Return the True or False

    Example usage: {{ value|in:list }}
    """
    if the_list is None or len(the_list) <=0:
        return False
    if isinstance(the_list,str):
        the_list = the_list.split(',')
    else:
        the_list = list(the_list)
    return value in the_list

@register.filter
def contains_in_list(value, the_list):
    """ Return the True or False caso contenha o elemnto na lista ou parte dele
    parecido com o in_list, porem ele pega elemnto por elemnto da lista e olha se a string contem o value

    Example usage: {{ value|in:list }}

    """
    if the_list is None or len(the_list) <=0:
        return False
    if isinstance(the_list,str):
        the_list = the_list.split(',')
    else:
        the_list = list(the_list)

    for elemento in the_list:
        if value in elemento:
            return True
    return value in the_list


class SetVarNode(template.Node):

    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        current = context
        # inverte a lista para acelerar o processo
        for dic_context in list(reversed(context.dicts)):
            if self.var_name in dic_context:
                current = dic_context
        current[self.var_name] = value
        return ""

@register.tag(name='set')
def set_var(parser, token):
    """
    {% set some_var = '123' %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% set <var_name> = <var_value> %}")

    return SetVarNode(parts[1], parts[3])
