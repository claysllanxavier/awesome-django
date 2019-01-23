# -*-coding:utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ManyToManyRel
from django.forms import CharField, PasswordInput
from django.core.validators import EMPTY_VALUES
from django.forms import ValidationError
from django.forms.utils import flatatt
from django.template.defaultfilters import linebreaksbr
from django.utils import six
from django.utils.encoding import force_text, smart_text
from django.utils.html import format_html, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from django.utils.translation import ugettext_lazy as _
import re
from django import forms


class ReadonlyField(object):
    def __init__(self, form, field):
        from django.contrib.admin.utils import label_for_field, help_text_for_field
        # Make self.field look a little bit like a field. This means that
        # {{ field.name }} must be a useful class name to identify the field.
        # For convenience, store other field-related data here too.
        if callable(field):
            class_name = field.__name__ if field.__name__ != '<lambda>' else ''
        else:
            class_name = field

        if form._meta.labels and class_name in form._meta.labels:
            label = form._meta.labels[class_name]
        else:
            label = label_for_field(field, form._meta.model)

        if form._meta.help_texts and class_name in form._meta.help_texts:
            help_text = form._meta.help_texts[class_name]
        else:
            help_text = help_text_for_field(class_name, form._meta.model)

        self.field = {
            'name': class_name,
            'label': label,
            'help_text': help_text,
            'field': field,
        }
        self.form = form
        self.is_checkbox = False
        self.is_readonly = True
        self.is_hidden = False

    def label_tag(self):
        attrs = {}
        label = self.field['label']
        return format_html('<label{}>{}:</label>',
                           flatatt(attrs),
                           capfirst(force_text(label)))

    def contents(self):
        from django.contrib.admin.templatetags.admin_list import _boolean_icon
        from django.contrib.admin.utils import lookup_field, display_for_field

        field, obj = self.field['field'], self.form.instance
        try:
            f, attr, value = lookup_field(field, obj)
        except (AttributeError, ValueError, ObjectDoesNotExist):
            result_repr = ''
        else:
            if f is None:
                boolean = getattr(attr, "boolean", False)
                if boolean:
                    result_repr = _boolean_icon(value)
                else:
                    result_repr = smart_text(value)
                    if getattr(attr, "allow_tags", False):
                        result_repr = mark_safe(result_repr)
                    else:
                        result_repr = linebreaksbr(result_repr)
            else:
                if isinstance(getattr(f, 'rel', None), ManyToManyRel) and value is not None:
                    result_repr = ", ".join(map(six.text_type, value.all()))
                else:
                    result_repr = display_for_field(value, f,'(None)')
                result_repr = linebreaksbr(result_repr)
        return conditional_escape(result_repr)

    def __str__(self, *args, **kwargs):
        """ Return str(self). """
        return format_html('%s' % self.contents())