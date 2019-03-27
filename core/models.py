from datetime import datetime

import requests
from django.contrib.admin.utils import NestedObjects, quote
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import (GenericForeignKey, GenericRel,
                                                GenericRelation)
from django.db import models, transaction
from django.db.models import (AutoField, BooleanField, FileField, ImageField,
                              ManyToManyField, ManyToManyRel, ManyToOneRel,
                              OneToOneField, OneToOneRel, DateField)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
import datetime

models.options.DEFAULT_NAMES += ('fk_fields_modal',)


class PaginacaoCustomizada(PageNumberPagination):
    """Classe para configurar a paginação da API
        O padrão da paginação são 10 itens, caso queira
        alterar o valor basta passar na URL o parametro
        page_size = X
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100000


class BaseManager(models.Manager):
    """Sobrescrevendo o Manager padrão. Nesse Manager 
    os registros não são apagados do banco de dados
    apenas desativados, atribuindo ao campo deleted a data de deleção
    """
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super(BaseManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        """Sobrescrevendo a queryset para filtrar os 
        registros que foram marcados como deleted
        """
        queryset = super(BaseManager, self).get_queryset()

        if ((hasattr(self.model, '_meta') and hasattr(self.model._meta, 'ordering') and self.model._meta.ordering) or
                ((hasattr(self.model, 'Meta') and hasattr(self.model.Meta, 'ordering') and self.model.Meta.ordering))):
            queryset = queryset.order_by(
                *(self.model._meta.ordering or self.model.Meta.ordering))
        if self.alive_only:
            return queryset.filter(deleted_on=None)
        return queryset.exclude(deleted_on=None)


class BaseMetod(models.Model):
    """Classe Base para ser herdada pelas demais
    para herdar os métodos

    objects_all [Manager auxiliar para retornar todos os registro
                 mesmo que o use_default_manager esteja como True]
    """

    objects = BaseManager()
    # Manager auxiliar para retornar os objetos deletados
    objects_deads = BaseManager(alive_only=False)

    def get_all_related_fields(self, view=None, include_many_to_many=True):
        """Método para retornar todos os campos que fazem referência ao
        registro que está sendo manipulado

        Returns:
            [Listas] -- [São retornadas duas listas a primeira com
                         os campos 'comuns' e a segunda lista os campos que
                         possuem relacionamento ManyToMany ou ForeignKey]
        """

        try:
            # Lista para retornar os campos que não são de relacionamento
            object_list = []

            # Lista para retornar os campos com relacionamento
            many_fields = []

            for field in self._meta.get_fields(include_parents=True):
                # Verificando se existe o atributo exclude no atributo que está sendo analisado

                if view and hasattr(view, 'exclude') and field.name in view.exclude:
                    continue
                if view and hasattr(view, 'form_class') and hasattr(view.form_class._meta, 'exclude') and field.name in view.form_class._meta.exclude:
                    continue
                if field.name in self.get_exclude_hidden_fields():
                    continue
                # Desconsiderando o campo do tipo AutoField da análise
                if isinstance(field, AutoField):
                    continue
                # Desconsiderando os campos com atributos auto_now_add ou now_add da análise
                # if hasattr(field, "auto_now_add") or hasattr(field, "now_add"):
                #     continue

                try:
                    # Verificando o tipo do relacionamento entre os campos
                    if type(field) is ManyToManyField and include_many_to_many:
                        if self.__getattribute__(field.name).exists():
                            many_fields.append((
                                field.verbose_name or field.name,
                                self.__getattribute__(field.name).all() or None
                            ))
                    elif (((type(field) is ManyToOneRel or type(field) is ManyToManyRel)) or
                          type(field) is GenericRel or type(field) is GenericForeignKey):
                        if self.__getattribute__((field.related_name or '{}_set'.format(field.name))).exists():
                            many_fields.append((field.related_model._meta.verbose_name_plural or field.name,
                                                self.__getattribute__(
                                                    (field.related_name or '{}_set'.format(
                                                        field.name))
                                                )))
                    elif type(field) is GenericRelation:
                        if self.__getattribute__(field.name).exists():
                            many_fields.append((field.related_model._meta.verbose_name_plural or field.name,
                                                self.__getattribute__(
                                                    field.name).all()
                                                ))
                    elif type(field) is OneToOneRel or type(field) is OneToOneField:
                        object_list.append((field.related_model._meta.verbose_name or field.name,
                                            self.__getattribute__(field.name)))
                    elif type(field) is BooleanField:
                        object_list.append(
                            ((field.verbose_name if hasattr(field, 'verbose_name') else None) or field.name,
                             "Sim" if self.__getattribute__(field.name) else None))
                    elif type(field) is DateField:
                        object_list.append(
                            ((field.verbose_name if hasattr(field, 'verbose_name') else None) or field.name,
                            self.__getattribute__(field.name).strftime("%d/%m/%Y")
                            if self.__getattribute__(field.name) else "Nâo"))
                    elif type(field) is ImageField or type(field) is FileField:
                        tag = ''
                        if self.__getattribute__(field.name).name:
                            if type(field) is ImageField:
                                tag = '<img width="100px" src="{url}" alt="{nome}" />'
                            elif type(field) is FileField:
                                tag = '<a  href="{url}" > <i class="fas fa-file"></i> {nome}</a>'
                            if tag:
                                tag = tag.format(url=self.__getattribute__(field.name).url,
                                                 nome=self.__getattribute__(field.name).name.split('.')[0])

                        object_list.append(
                            ((field.verbose_name if hasattr(field, 'verbose_name') else None) or field.name,
                             tag))
                    elif hasattr(field, 'choices') and hasattr(self, 'get_{}_display'.format(field.name)):
                        object_list.append(
                            (
                                (field.verbose_name if hasattr(
                                    field, 'verbose_name') else None) or field.name,
                                getattr(
                                    self, 'get_{}_display'.format(field.name))()
                            )
                        )
                    else:
                        object_list.append(
                            ((field.verbose_name if hasattr(field, 'verbose_name') else None) or field.name,
                             self.__getattribute__(field.name)))
                except Exception:
                    pass

        finally:
            # Retornando as listas
            return object_list, many_fields

    def get_deleted_objects(self, objs, user, using='default'):
        """
        Find all objects related to ``objs`` that should also be deleted. ``objs``
        must be a homogeneous iterable of objects (e.g. a QuerySet).

        Return a nested list of strings suitable for display in the
        template with the ``unordered_list`` filter.

        Encontre todos os objetos relacionados a ``objs`` que também devem ser deletados. ``objs``
                  deve ser um iterável homogêneo de objetos (por exemplo, um QuerySet).

                  Retornar uma lista aninhada de sequências adequadas para exibição no
                  template com o filtro `` unordered_list``.
        """
        collector = NestedObjects(using=using)
        collector.collect(objs)
        perms_needed = set()

        def format_callback(obj):
            opts = obj._meta

            no_edit_link = '%s: %s' % (str(opts.verbose_name).title(), obj)

            try:
                url = reverse('%s:%s-update' % (
                    opts.app_label,
                    opts.model_name),
                    None, (quote(obj.pk),))

            except NoReverseMatch:
                # Change url doesn't exist -- don't display link to edit
                return no_edit_link

            p = '%s.%s' % (
                opts.app_label, get_permission_codename('delete', opts))
            if not user.has_perm(p):
                perms_needed.add(opts.verbose_name.title())
            # Display a link to the admin page.
            return format_html('{}: <a href="{}">{}</a>',
                               str(opts.verbose_name).title(),
                               url,
                               obj)

        to_delete = collector.nested(format_callback)

        protected = [format_callback(obj) for obj in collector.protected]
        model_count = {model._meta.verbose_name_plural: len(
            objs) for model, objs in collector.model_objs.items()}

        return perms_needed, protected

    def delete(self, using='default', keep_parents=False):
        """Sobrescrevendo o método para marcar os campos
        deleted com a data da deleção. Assim o
        item não é excluído do banco de dados.
        """

        # Iniciando uma transação para garantir a integridade dos dados
        with transaction.atomic():

            # Recuperando as listas com os campos do objeto
            object_list, many_fields = self.get_all_related_fields()

            # Percorrendo todos os campos que possuem relacionamento do objeto
            for obj, values in many_fields:
                if values.all():
                    values.all().update(deleted_on=timezone.now())
            # Atualizando o registro
            self.deleted_on = timezone.now()
            self.save(update_fields=['deleted_on'])

    def hard_delete(self):
        super().delete()

    class Meta:
        """ Configure abstract class """
        abstract = True
        ordering = ['pk']

    def get_exclude_hidden_fields(self):
        return ['deleted_on', 'created_on', 'updated_on']

    def get_meta(self):
        return self._meta

    def has_view_permission(self, request):
        """
        Returns True if the given request has permission to view an object.
        Can be overridden by the user in subclasses.
        """
        opts = self._meta
        codename = get_permission_codename('view', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        Can be overridden by the user in subclasses.
        """
        opts = self._meta
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self._meta
        codename = get_permission_codename('change', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self._meta
        codename = get_permission_codename('delete', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))


class Base(BaseMetod):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    deleted_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        """ Configure abstract class """
        abstract = True
        ordering = ['pk']

    def __str__(self):
        return '%s' % self.updated_on


class ParameterForBase(Base):
    nomeProjeto = models.TextField(blank=True, null=True, default='')
    tituloProjeto = models.TextField(blank=True, null=True, default='')
    descricaoProjeto = models.TextField(blank=True, null=True, default='')
    iconeProjeto = models.ImageField(upload_to='images/', blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        parametro = ParameterForBase.objects.first()
        if parametro:
            self.id = parametro.id
            self.pk = parametro.pk
        super(ParameterForBase, self).save()

    class Meta:
        verbose_name = u'Parametro para o Core'
        verbose_name_plural = u'Parametros para o Core'

    def __str__(self):
        return "{}".format(self.nomeProjeto or self.id)


class ParametersUser(Base):
    senha_padrao = models.CharField(verbose_name=u"Senha padrão para reset", max_length=30, default=u'password@123456',
                                    help_text=u"Senha padrão que sera criada quando resetar senha do usuario")

    def __unicode__(self):
        return u'%s' % self.id

    class Meta:
        verbose_name = u'Parâmetro do Usuário'
        verbose_name_plural = u"Parâmetros dos Usuários"
        permissions = (
            ("can_reset_password", u"Pode resetar a senha"),
        )


class NotificationBase(models.Model):
    """
    Model responsavel para o sistema de notificações
    """
    CHOICES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Danger')
    )
    remetente = models.ForeignKey(User, verbose_name=u"Remetente", blank=True, null=True,
                                  related_name='notificationbase_remetente', on_delete=models.CASCADE)
    remetente_string = models.CharField(u"Remetente Descrição", max_length=60, null=True, blank=True)
    destinatario = models.ForeignKey(User, verbose_name=u"Destinatário",
                                     related_name='notificationbase_destinatario', on_delete=models.CASCADE)
    titulo = models.CharField(u"Título", max_length=30, null=True, blank=True)
    mensagem = models.TextField(u"Mensagem")
    url = models.CharField(u"View name URL", max_length=60)
    parametro = models.CharField(u"Parametro URL", max_length=20, null=True, blank=True)
    parametro_get = models.CharField(u"Parametro GET", max_length=60, null=True, blank=True)
    visualizado = models.BooleanField(u"Visualizado", default=False, db_index=True)
    data_envio = models.DateTimeField(u"Data de envio", auto_now_add=True)
    tipo = models.CharField(u"Tipo", choices=CHOICES, max_length=10, default=CHOICES[0][0])

    def __str__(self):
        return u"Notificação nº%s - %s" % (self.id, self.data_envio.strftime("%d/%m/%Y %H:%M:%S"))

    def data_envio_f(self):
        return self.data_envio.strftime("%d/%m/%Y %H:%M:%S")

    def get_url(self):
        url = self.url
        try:
            if url and self.parametro:
                try:
                    return reverse(url, args=self.parametro)
                except Exception:
                    return reverse(url, kwargs={'pk':self.parametro})
            elif url:
                return reverse(url)
        except Exception:
            pass
        return '#'

    class Meta:
        verbose_name = "notificação"
        verbose_name_plural = "notificações"
        ordering = ['-data_envio']
