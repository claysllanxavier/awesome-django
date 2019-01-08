from datetime import date, datetime
from django.contrib import admin, messages

# Register your models here.
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect

from core.forms import ParameterForBaseForm
from core.models import ParameterForBase
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



admin.site.register(ParameterForBase, ParametroAdmin)