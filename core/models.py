from datetime import datetime

from django.contrib.admin.utils import NestedObjects, quote
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRel, GenericRelation
from django.db import models, transaction
from django.db.models import (AutoField, ManyToManyField,
                              ManyToOneRel, ManyToManyRel,
                              OneToOneRel, BooleanField,
                              FileField, ImageField, OneToOneField)
from django.db.models.signals import post_save
from django.dispatch import receiver

from .settings import use_default_manager

from rest_framework.pagination import PageNumberPagination
import requests


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
    apenas desativados, atribuindo ao campo deleted = True e
    enabled = True
    """

    def get_queryset(self):
        """Sobrescrevendo a queryset para filtrar os 
        registros que foram marcados como deleted
        """
        queryset = super(BaseManager, self).get_queryset()

        if ((hasattr(self.model,'_meta') and hasattr(self.model._meta,'ordering') and self.model._meta.ordering ) or
                ((hasattr(self.model,'Meta') and hasattr(self.model.Meta,'ordering') and self.model.Meta.ordering))):
            queryset = queryset.order_by(*(self.model._meta.ordering or self.model.Meta.ordering))

        return queryset.filter(deleted=False)

class BaseMetod(models.Model):
    """Classe Base para ser herdada pelas demais
    para herdar os métodos

    objects_all [Manager auxiliar para retornar todos os registro
                 mesmo que o use_default_manager esteja como True]
    """

    # Verificação se deve ser usado o manager padrão ou o customizado
    if use_default_manager is False:
        objects = BaseManager()
    else:
        objects = models.Manager()

    # Manager auxiliar para retornar todos os registro indepentende
    # da configuraçao do use_default_manager
    objects_all = models.Manager()

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
                if hasattr(field, "auto_now_add") or hasattr(field, "now_add"):
                    continue

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
                                                    (field.related_name or '{}_set'.format(field.name))
                                                )))
                    elif type(field) is GenericRelation:
                        if self.__getattribute__(field.name).exists():
                            many_fields.append((field.related_model._meta.verbose_name_plural or field.name,
                                self.__getattribute__(field.name).all()
                            ))
                    elif type(field) is OneToOneRel or type(field) is OneToOneField:
                        object_list.append((field.related_model._meta.verbose_name or field.name,
                                            self.__getattribute__(field.name)))
                    elif type(field) is BooleanField:
                        object_list.append(
                            ((field.verbose_name if hasattr(field, 'verbose_name') else None) or field.name,
                             "Sim" if self.__getattribute__(field.name) else "Nâo"))
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
                                (field.verbose_name if hasattr(field, 'verbose_name') else None) or field.name,
                                getattr(self, 'get_{}_display'.format(field.name))()
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
                url = reverse('%s:%s-update'% (
                                  opts.app_label,
                                  opts.model_name),
                              None, (quote(obj.pk),))


            except NoReverseMatch:
                # Change url doesn't exist -- don't display link to edit
                return no_edit_link

            p = '%s.%s' % (opts.app_label, get_permission_codename('delete', opts))
            if not user.has_perm(p):
                perms_needed.add(opts.verbose_name.title())
            # Display a link to the admin page.
            return format_html('{}: <a href="{}">{}</a>',
                               str(opts.verbose_name).title(),
                               url,
                               obj)

        to_delete = collector.nested(format_callback)

        protected = [format_callback(obj) for obj in collector.protected]
        model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}

        return perms_needed, protected

    def delete(self, using='default', keep_parents=False):
        """Sobrescrevendo o método para marcar os campos
        deleted como True e enabled como False. Assim o
        item não é excluído do banco de dados.
        """
        # Verificando se deve ser utilizado o manager costumizado
        if use_default_manager is False:

            # Iniciando uma transação para garantir a integridade dos dados
            with transaction.atomic():

                # Recuperando as listas com os campos do objeto
                object_list, many_fields = self.get_all_related_fields()

                # Percorrendo todos os campos que possuem relacionamento com o objeto
                for obj, values in many_fields:
                    if values.all():
                        values.all().update(deleted=True, enabled=False)
                # Atualizando o registro
                self.deleted = True
                self.enabled = False
                self.save(update_fields=['deleted', 'enabled'])
        else:
            super().delete()

    class Meta:
        """ Configure abstract class """
        abstract = True
        ordering = ['pk']

    def get_exclude_hidden_fields(self):
        return ['enabled', 'deleted']

    def get_meta(self):
        return self._meta

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
    enabled = models.BooleanField('Ativo', default=True)
    deleted = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

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
    iconeProjeto = models.TextField(blank=True, null=True, default='')
    login_redirect_url = models.CharField(max_length=250, blank=True, null=True, default= '/core/')
    login_url = models.CharField(max_length=250, blank=True, null=True, default='/core/login/')
    logout_redirect_url = models.CharField(max_length=250, blank=True, null=True, default='/core/login/')
    url_integracao = models.CharField(max_length=500, blank=True, null=True, default='')

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


user_model = get_user_model()

class UsuarioBase(models.Model):
    """
    Classe para gerenciar os usuários do sistema.
    Quando um usuário for cadastrado ou tentar logar no sistema será realizada uma consulta
    na API do sistema integração para validar os dados do usuário trazendo todos os valores
    abaixo descritos.

    O Username tem que ser a matrícula sem formatação do usuário Exemplo:
    Se a matrícula for 99.999-9 o valor inserido tem que ser 999999
    """

    user = models.OneToOneField(user_model, on_delete=models.CASCADE)
    matricula = models.BigIntegerField(u'Matricula', blank=True, null=True, db_index=True)
    servidor = models.CharField(u'servidor', max_length=500, blank=True, null=True, db_index=True)
    cod_setor = models.CharField(u'cod_setor', max_length=50, blank=True, null=True, db_index=True)
    setor = models.CharField(u'setor', max_length=500, blank=True, null=True, db_index=True)
    cod_cargo = models.BigIntegerField(u'cod_cargo', blank=True, null=True, db_index=True)
    cargo = models.CharField(u'cargo', max_length=500, blank=True, null=True, db_index=True)
    cod_funcao = models.BigIntegerField(u'cod_funcao', blank=True, null=True, db_index=True)
    funcao = models.CharField(u'funcao', max_length=500, blank=True, null=True, db_index=True)
    cod_vinculo = models.BigIntegerField(u'cod_vinculo', blank=True, null=True, db_index=True)
    vinculo = models.CharField(u'vinculo', max_length=500, blank=True, null=True, db_index=True)
    secretaria = models.CharField(u'Secretaria', max_length=500, blank=True, null=True, db_index=True)
    cod_unidade_gestora = models.CharField(verbose_name=u'Código da Unidade Gestora', max_length=11, blank=True,
                                           null=True, db_index=True) #secretaria
    data_admissao = models.DateField(u'data_admissao', blank=True, null=True)
    data_desligamento = models.DateField(u'data_desligamento', blank=True, null=True)
    localizacao = models.CharField(u'localizacao', max_length=500, blank=True, null=True, db_index=True)
    ativo = models.BooleanField(u'ativo ?', default=False)
    exonerado = models.BooleanField(u'exonerado ?', default=False)
    mes_referencia = models.PositiveIntegerField(u'Mês Referência', default=0)
    ano_referencia = models.PositiveIntegerField(u'Ano Referência', default=0)
    data_atualizacao = models.DateTimeField(auto_now=True)

    prodata = models.BooleanField(blank=True, default=False) #se pegou da prodata automaticamente

    def preencher_dados_via_integracao(self):
        try:
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            parameter_for_base = ParameterForBase.objects.first()
            response = None
            if hasattr(parameter_for_base, 'url_integracao') and parameter_for_base.url_integracao:
                response = requests.get(parameter_for_base.url_integracao,
                                    params={'matricula': self.matricula or self.user.username,
                                            'ano_referencia': ano_atual, 'mes_referencia': mes_atual}).json()

            if response and 'count' in response and response['count'] <= 0:
                if mes_atual != 1:
                    mes_atual -= 1
                else:
                    mes_atual = 12
                    ano_atual -= 1
                response = requests.get(parameter_for_base.url_integracao,
                                        params={'matricula': self.matricula or self.user.username, 'ano_referencia': ano_atual,
                                                'mes_referencia': mes_atual}).json()
            if response and 'results' in response and len(response['results']) > 0:
                response = response['results'][0]

                if hasattr(self,'user') and self.user:
                    nome = response['servidor'].split(' ')[0]
                    sobre_nome = ' '.join(response['servidor'].split(' ')[1:])
                    self.user.first_name = nome.strip()[:30]
                    self.user.last_name = sobre_nome.strip()[:150]

                self.matricula = response['matricula']
                self.servidor = response['servidor']
                self.cod_setor = response['cod_setor']
                self.setor = response['setor']
                self.cod_cargo = response['cod_cargo']
                self.cargo = response['cargo']
                self.cod_funcao = response['cod_funcao']
                self.funcao = response['funcao']
                self.cod_vinculo = response['cod_vinculo']
                self.vinculo = response['vinculo']
                self.secretaria = response['secretaria']
                self.cod_unidade_gestora = response['cod_secretaria']
                self.data_admissao = response['data_admissao']
                self.data_desligamento = response['data_desligamento']
                self.localizacao = response['localizacao']
                self.ativo = response['ativo']
                # self.exonerado = response['results']
                self.mes_referencia = response['mes_referencia']
                self.ano_referencia = response['ano_referencia']
                self.data_atualizacao = response['data_atualizacao']
                self.prodata = True
            else:
                self.prodata = False
        except Exception as e:
            pass

    def __str__(self):
        return '%s - %s' % (self.matricula, self.servidor)


class ParametersUser(Base):
    mim_tamanho = models.IntegerField(verbose_name=u"Quantidade mínima de caracteres",
                                      help_text="Tamanho mínimo da senha", default=8)
    max_tamanho = models.IntegerField(verbose_name=u"Quantidade máxima de caracteres",
                                      help_text="Tamanho máximo da senha",  default=30)
    dias_expirar = models.IntegerField(verbose_name=u'Quantidade de dias para exigir a troca de senha', default=30)
    qtde_verificar_similares = models.IntegerField(verbose_name=u"Quantidade de senhas similares a serem bloqueadas",
                                                   default=3)
    combinar_numero_caracter = models.BooleanField(verbose_name=u"Combinar Letras e Numeros", default=True)
    qtde_numero = models.IntegerField(verbose_name=u"Quantidade mínima de números", default=4)
    qtde_caracter = models.IntegerField(verbose_name=u"Quantidade mínima de letras", default=2, )
    bloquear_usuario = models.IntegerField(verbose_name=u"Quantidade de dias para bloquear o usuario", default=30,
                                           help_text=u"Qtde de dias para bloquear usuario sem acesso. Use 0 para desabilitar.")
    busca_dados_matricula = models.BooleanField(verbose_name=u'Buscar dados do usuário pela Matricula', default=False,
                                          help_text=u"Busca dados do usuario na base de dados de Colaboradores")
    bloquear_sequencia_caracter = models.BooleanField(verbose_name=u'Bloquear sequências de caracteres',
                                                      help_text="Bloqueia sequência de caracteres no campo de senha",
                                                      default=True)
    usuario_matricula = models.BooleanField(verbose_name=u"Obrigar Matricula no campo Usuario", default=False)
    combinar_maiuscula_minuscula = models.BooleanField(verbose_name=u"Combinar letras maiúsculas e minúsculas",
                                                       default=False)
    qtde_maiuscula = models.IntegerField(verbose_name=u"Quantidade mínima de maiúsculas", default=0)
    qtde_minuscula = models.IntegerField(verbose_name=u"Quantidade mínima de minúsculas", default=0)
    senha_padrao = models.CharField(verbose_name=u"Senha padrão para reset", max_length=125, default=u'agtec@123456',
                                    help_text=u"Senha padrão que sera criada quando resetar senha do usuario")
    editar_dados_perfil = models.BooleanField(verbose_name=u'Editar dados do Perfil no cadastro de Usuário ',
                                              default=False,
                                              help_text=u"Editar dados do perfil manualmente senão encontrar dados do usuario pelo Matricula")

    def __unicode__(self):
        return u'%s' % self.id

    class Meta:
        verbose_name = u'Parâmetro do Usuário'
        verbose_name_plural = u"Parâmetros dos Usuários"
        permissions = (
            ("can_reset_password", u"Pode resetar a senha"),
        )

    def bloquear_sequencias(self):
        PASSWORD_COMMON_SEQUENCES = [
            u"0123456789",
            u"`1234567890-=",
            u"9876543210",
            u"`0987654321-=",
            u"~!@#$%^&*()_+",
            u"abcdefghijklmnopqrstuvwxyz",
            u"quertyuiop[]\\asdfghjkl;\'zxcvbnm,./",
            u'quertyuiop{}|asdfghjkl;"zxcvbnm<>?',
            u"quertyuiopasdfghjklzxcvbnm",
            u"1qaz2wsx3edc4rfv5tgb6yhn7ujm8ik,9ol.0p;/-['=]\\",
            u"qazwsxedcrfvtgbyhnujmikolp"
        ]
        return PASSWORD_COMMON_SEQUENCES if self.bloquear_sequencia_caracter else None

    def complexidade_senha(self):
        PASSWORD_COMPLEXITY = {  # You can ommit any or all of these for no limit for that particular set
                                 "UPPER": self.qtde_maiuscula if self.combinar_maiuscula_minuscula else 0,  # Uppercase
                                 "LOWER": self.qtde_minuscula if self.combinar_maiuscula_minuscula else 0,  # Lowercase
                                 "DIGITS": self.qtde_numero if self.combinar_numero_caracter else 0,  # Digits
                                 "PUNCTUATION": 0,  # Punctuation (string.punctuation)
                                 "NON ASCII": self.qtde_caracter if self.combinar_numero_caracter else 0,
                                 # Non Ascii (ord() >= 128)
                                 "WORDS": 1  # Words (substrings seperates by a whitespace)
        }
        return PASSWORD_COMPLEXITY if self.combinar_numero_caracter else None


class HistoricoSenha(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_password_history')
    password = models.CharField(max_length=128)

    def get_password(self):
        return self.password

    def get_last_password(self, user):
        try:
            return HistoricoSenha.objects.filter(user=user).order_by('-id').first()
        except:
            return None

    def primeiro_acesso(self, user):
        if HistoricoSenha.objects.filter(user=user).count() <= 1:
            return True
        return False

    def verificar_senha_experiou(self, user):
        ultima_senha = self.get_last_password(user)
        dias = datetime.now().toordinal() - ultima_senha.created_on.toordinal()
        if dias > ParametersUser.objects.get().dias_expirar:
            return True
        return False


@receiver(post_save, sender=user_model, dispatch_uid='core.HistoricoSenha.post_save')
def historico_senha_pos_save(sender, instance, created, **kwargs):
    try:
        param = ParametersUser.objects.first()
        historico = HistoricoSenha.objects.filter(user=instance)
        if historico.count() < param.qtde_verificar_similares:
            if not historico.filter(password=instance.password).exists():
                HistoricoSenha.objects.create(user=instance, password=instance.password)
        else:
            if not historico.filter(password=instance.password).exists():
                historico = HistoricoSenha.objects.filter(user=instance).order_by('id').first()
                historico.delete()
                HistoricoSenha.objects.create(user=instance, password=instance.password)
    except:
        pass
