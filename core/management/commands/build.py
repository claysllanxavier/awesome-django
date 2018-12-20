"""Manager para mapear os models da app automatizando 
a criação dos templates customizados, das views, da APIRest e dos Forms.
"""

import fileinput
import os
import time
from optparse import make_option

# Pacote responsável por pegar a instância do models baseado no nome
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
# Importando os tipos de fields do Django
from django.db.models.fields import (BLANK_CHOICE_DASH, NOT_PROVIDED,
                                     AutoField, BigAutoField, BigIntegerField,
                                     BinaryField, BooleanField, CharField,
                                     CommaSeparatedIntegerField, DateField,
                                     DateTimeField, DecimalField,
                                     DurationField, EmailField, Empty, Field,
                                     FieldDoesNotExist, FilePathField,
                                     FloatField, GenericIPAddressField,
                                     IntegerField, IPAddressField,
                                     NullBooleanField, PositiveIntegerField,
                                     PositiveSmallIntegerField, SlugField,
                                     SmallIntegerField, TextField, TimeField,
                                     URLField, UUIDField)
from django.urls import resolve, reverse
from django.utils.text import capfirst


class Command(BaseCommand):
    help = "Manager para automatizar a geração dos códigos"

    #Path do diretório onde a app core está instalada
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    def add_arguments(self, parser):
        """Método inicial para informar quais parâmetros serão aceitos
        """

        parser.add_argument('App', type=str)
        # O argumento Model conta com um argumento a mais porque ele é opcional
        # caso o desenvolvedor queria gerar os arquivos para toda a app
        parser.add_argument('Model', type=str, nargs='?')

        # Parâmetro opcionais
        parser.add_argument(
            '--templates',
            action = 'store_true',
            dest = 'templates',
            help = 'Criar apenas os Templates'
        )
        parser.add_argument(
            '--api',
            action = 'store_true',
            dest = 'api',
            help = 'Criar apenas a API'
        )
        parser.add_argument(
            '--urls',
            action = 'store_true',
            dest = 'url',
            help = 'Criar apenas as Urls'
        )
        parser.add_argument(
            '--forms',
            action = 'store_true',
            dest = 'forms',
            help = 'Criar apenas o Form'
        )
        parser.add_argument(
            '--views',
            action = 'store_true',
            dest = 'views',
            help = 'Criar apenas as Views (CRUD)'
        )
        parser.add_argument(
            '--parserhtml',
            action = 'store_true',
            dest = 'renderhtml',
            help = 'Renderirzar os fields do models para HTML'
        )

    """
    #################################################################
    Área dos método internos
    #################################################################    
    """

    def _contain_number(self, text):
        try:
            return any(character.isdigit() for character in text)
        except:
            return False

    def _get_size(self, path):
        """Método para verificar o tamanho de um determinado arquivo.
        
        Arguments:
            path {str} -- Caminho absoluto para o arquivo
        
        Returns:
            Tamanho do arquivo
        """

        try:
            return os.path.getsize(path)
        except Exception as e:
            self._message(e)
            return False
    
    def _check_dir(self, path):
        """Método para verificar se o diretório existe
        
        Arguments:
            path {str} -- Caminho do diretório
        
        Returns:
            Boolean -- Verdadeiro se existir o diretório e Falso se não.
        """

        try:
            return os.path.isdir(path)
        except Exception as e:
            self._message(e)
            return False

    def _check_file(self, path):
        """Método para verificar se o arquivo existe
        
        Arguments:
            path {str} -- Caminho para o arquivo
        
        Returns:
            Boolean -- Verdadeiro se existir o arquivo e False se não.
        """

        try:
            return os.path.isfile(path)
        except Exception as e:
            self._message(e)
            return False
    
    def _message(self, message):
        """Método para retornar mensagems ao prompt(Terminal)
        
        Arguments:
            message {str} -- Mensagem a ser exibida
        """

        self.stdout.write(self.style.SUCCESS(message))

    def _check_content(self, path, text_check):
        """Método para verificar se determinado texto existe 
        dentro de determinado arquivo
        
        Arguments:
            path {str} -- Caminho absoluto para o arquivo a ser analisado
            text_check {str} -- Texto a ser pesquisado dentro do arquivo informado
        
        Returns:
            Boolean -- Verdadeiro se o conteúdo for encontrado e False se não.
        """

        try:
            if self._check_file(path):
                with open(path) as arquivo:
                    content = arquivo.read()
                    return text_check in content
            self._message("Arquivo não encontrado para análise.")
        except Exception as e:
            self._message(e)
            return False

    def _get_snippet(self, path):
        """Método para recuperar o texto a ser utilizado na
        configuração do novo elemento
        
        Arguments:
            path {str} -- Caminho absoluto para o arquivo
        
        Returns:
            str -- Texto a ser utilizado para interpolar os dados do models
        """

        try:
            if self._check_file(path):
                with open(path) as arquivo:
                    return arquivo.read()
            self._message("Arquivo não encontrado para captura.")
        except Exception as e:
            self._message(e)
            return None

    def _get_model(self):
        """ Método para pegar a instancia 
        do models

        Returns:
            Instancia do Models or None
        """
        try:
            return apps.get_model(self.app, self.model)
        except:
            return None
    
    """
    #################################################################
    Área dos templates
    #################################################################    
    """

    def _manage_detail_template(self):
        """Método para criar o template de Detail do model.
        """

        try:
            self._message("Trabalhando na configuração do template de Detalhamento.")
            path = os.path.join(self.path_template_dir, "{}_detail.html".format(self.model_lower))
            # Verificando se já existe o template
            if self._check_file(path):
                self._message("O model informado já possui o template de Detalhamento")
                return
            # Pegando o conteúdo do snippet para criar o template
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/detailtemplate.txt"))
            # Interpolando o conteúdo
            content = content.replace("$title$", self.model)
            content = content.replace("$model_name$", self.model_lower)
            content = content.replace("$app_name$", self.app_lower)
            with open(path, 'w') as template:
                template.write(content)
        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O TEMPLATE de Detalhamento sofreu alguma alteração.")
            self._message(error)
    
    def _manage_list_template(self):
        """Método para criar o template de List do model.
        """
        try:
            self._message("Trabalhando na configuração do template de Edição.")
            path = os.path.join(self.path_template_dir, "{}_list.html".format(self.model_lower))
            # Verificando se já existe o template
            if self._check_file(path):
                self._message("O model informado já possui o template de Listagem")
                return
            # Pegando o conteúdo do snippet para criar o template
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/listtemplate.txt"))
            # Interpolando o conteúdo
            content = content.replace("$title$", self.model)
            content = content.replace("$label_count_item$", self.model)
            content = content.replace("$model_name$", self.model_lower)
            content = content.replace("$app_name$", self.app_lower)
            with open(path, 'w') as template:
                template.write(content)

        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O TEMPLATE de Edição sofreu alguma alteração.")
            self._message(error)
    
    def _manage_update_template(self):
        """Método para criar o template de Update do model.
        """

        try:
            self._message("Trabalhando na configuração do template de Edição.")
            path = os.path.join(self.path_template_dir, "{}_update.html".format(self.model_lower))
            # Verificando se já existe o template
            if self._check_file(path):
                self._message("O model informado já possui o template de Edição")
                return
            # Pegando o conteúdo do snippet para criar o template
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/updatetemplate.txt"))
            # Interpolando o conteúdo
            content = content.replace("$title$", self.model)
            content = content.replace("$app_name$", self.app_lower)
            content = content.replace("$model_name$", self.model_lower)

            with open(path, 'w') as template:
                template.write(content)

        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O TEMPLATE de Edição sofreu alguma alteração.")
            self._message(error)
    
    def _manage_create_template(self):
        """Método para criar o template de Create do model.
        """

        try:
            self._message("Trabalhando na configuração do template de Criação.")
            path = os.path.join(self.path_template_dir, "{}_create.html".format(self.model_lower))
            # Verificando se já existe o template
            if self._check_file(path):
                self._message("O model informado já possui o template de Criação")
                return
            # Pegando o conteúdo do snippet para criar o template
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/createtemplate.txt"))
            # Interpolando o conteúdo
            content = content.replace("$title$", self.model)
            with open(path, 'w') as template:
                template.write(content)

        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O TEMPLATE de Criação sofreu alguma alteração.")
            self._message(error)

    def _manage_delete_template(self):
        """Método para criar o template de Delete do model.
        """

        try:
            self._message("Trabalhando na configuração do template de Deleção.")
            path = os.path.join(self.path_template_dir, "{}_delete.html".format(self.model_lower))
            # Verificando se já existe o template
            if self._check_file(path):
                self._message("O model informado já possui o template de Deleção.")
                return
            # Pegando o conteúdo do snippet para criar o template
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/deletetemplate.txt"))
            # Interpolando o conteúdo
            content = content.replace("$app_name$", self.app_lower)
            content = content.replace("$model_name$", self.model_lower)
            with open(path, 'w') as template:
                template.write(content)

        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O TEMPLATE de Deleção sofreu alguma alteração.")
            self._message(error)
    
    def _manage_templates(self):
        """Método pai para controlar a criação do templates
        """

        try:
            self._message("Trabalhando na configuração dos templates.")
            if self._check_dir(self.path_template_dir) is False:
                self._message("Criando o diretório dos Templates")
                os.makedirs(self.path_template_dir)
            # Chamando método de criação do template de detalhe.
            self._manage_detail_template()
            # Chamando método de criação do template de listagem.
            self._manage_list_template()
            # Chamando método de criação do template de criação.
            self._manage_create_template()
            # Chamando método de criação do template de deleção.
            self._manage_delete_template()
            # Chamando método de criação do template de atualização.
            self._manage_update_template()
        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O DIRETÓRIO DE TEMPLATES sofreu alguma alteração.")
            self._message(error)

    """
    #################################################################
    Área da API DRF
    #################################################################    
    """

    def _manage_api_url(self):
        """Método para configuração das URLS da API
        """

        try:
            self._message("Trabalhando na configuração das Urls API do model {}".format(self.model))
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/api_router.txt"))
            content_urls = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/api_router_urls.txt"))
            # Interpolando o conteúdo
            content = content.replace("$ModelName$", self.model)
            content = content.replace("$app_name$", self.app_lower)
            content = content.replace("$model_name$", self.model_lower)
            content_urls = content_urls.replace("$ModelName$", self.model)
            # Verificando se o arquivo urls.py existe
            if self._check_file(self.path_urls) is False:
                # Criando o arquivo com o conteúdo da interpolação
                with open(self.path_urls, 'w') as arquivo:
                    arquivo.write(content_urls + content)
                return
                
            if self._check_content(self.path_urls, " {}ViewAPI".format(self.model)):
                # Já existe configuração de URL para a APP saindo da função
                self._message("O model informado já possui urls da API configuradas.")
                return

            # Verificando se já existe o router = routers.DefaultRouter()
            if self._check_content(self.path_urls, "router = routers.DefaultRouter()"):
                content = content.replace("router = routers.DefaultRouter()", "")
                imports = 'router = routers.DefaultRouter()'
                with fileinput.FileInput(self.path_urls, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, imports + content), end='')
            else:
                #Verifica se há o app_name
                if self._check_content(self.path_urls, "app_name = \'{}\'".format(self.app)):
                    # Atualizando arquivo com o novo conteúdo
                    app_name_url = "app_name = \'{}\'".format(self.app_lower)
                    with fileinput.FileInput(self.path_urls, inplace=True) as arquivo:
                        for line in arquivo:
                            print(line.replace(
                                app_name_url, app_name_url+ '\n' + content), end='')
        
            # Verificando se já existe a configuração dos routers para evitar redundância.
            if self._check_content(self.path_urls, "from rest_framework import routers"):
                content_urls = content_urls.replace("from rest_framework import routers", "")

            # Verificando se já existe a lib include no arquivo, para evitar importação
            # redundante.
            if self._check_content(self.path_urls, "from django.urls import path, include"):
                content_urls = content_urls.replace("from django.urls import path, include", "")
                imports = 'from django.urls import path, include'
                with fileinput.FileInput(self.path_urls, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, content_urls + '\n' + imports), end='')
            else:
                with open(self.path_urls, 'a') as arquivo:
                    arquivo.write(content_urls)
        except Exception as error:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O ARQUIVO urls.py sofreu algumar alteração.")
            self._message(error)

    def _manage_api_view(self):
        """Método para configuração das Views da API
        """
        try:
            self._message("Trabalhando na configuração das Views da API do model {} ".format(self.model))
            content = self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/api_view.txt"))
            content_urls = self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/api_urls.txt"))
            # Interpolando os dados
            content = content.replace("$ModelName$", self.model)
            content_urls = content_urls.replace("$ModelName$", self.model)
            # Verificando se o arquivo views.py existe
            if self._check_file(self.path_views) is False:
                # Criando o arquivo com o conteúdo da interpolação
                with open(self.path_views, 'w') as arquivo:
                    arquivo.write(content_urls + content)
                return

            # Verificando se já tem a configuração do model
            if self._check_content(self.path_views, " {}ViewAPI".format(self.model)):
                self._message("O model informado já possui views da API configurado.")
                return

            # Verificando se já foi importado o model
            if self._check_content(self.path_views, self.model):
                content_urls = content_urls.replace("from .models import {}".format(self.model), "")
            
            # Verificando se tem a importação do rest_framework
            if self._check_content(self.path_views, "from rest_framework.viewsets import ModelViewSet"):
                content_urls = content_urls.replace("from rest_framework.viewsets import ModelViewSet", "")
                content_urls = content_urls.replace("from rest_framework import status", "")
                content_urls = content_urls.replace("from rest_framework.response import Response", "")
                content_urls = content_urls.replace("from rest_framework.decorators import action", "")

            # Verificando se já tem os imports do core
            if self._check_content(self.path_views, "from core.views"):
                content_urls = content_urls.replace(
                    "from core.views import BaseListView, BaseDeleteView, BaseDetailView, BaseUpdateView, BaseCreateView", "")
                imports = 'from core.views import BaseListView, BaseDeleteView, BaseDetailView, BaseUpdateView, BaseCreateView'
                with fileinput.FileInput(self.path_views, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, content_urls + imports), end='')
            else:
                with open(self.path_views, 'a') as views:
                    views.write("\n")
                    views.write(content_urls)
          
            # Atualizando o conteúdo do arquivo.
            with open(self.path_views, 'a') as api_views:
                api_views.write("\n")
                api_views.write(content)
        except:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O ARQUIVO models.py sofreu alguma alteração")

    def _manage_serializer(self):
        """Método para configurar o serializer do model informado.
        """
        try:
            self._message("Trabalhando na configuração do Serializer do model {}".format(self.model))
            content = self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/serializer.txt"))
            content_urls = self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/serializer_urls.txt"))
            # Interpolando os dados
            content = content.replace("$ModelName$", self.model)
            content_urls = content_urls.replace("$ModelName$", self.model)
            # Verificando se o arquivo serializers.py existe
            if self._check_file(self.path_serializer) is False:
                # Criando o arquivo com o conteúdo da interpolação
                with open(self.path_serializer, 'w') as arquivo:
                    arquivo.write(content_urls + '\n\n' + content)
                return
            
            # Verificando se já existe configuração no serializers para o Models informado
            if self._check_content(self.path_serializer, "class {}Serializer".format(self.model)):
                self._message("O model informado já possui serializer configurado.")
                return
            
            # Verificando se tem a importação do ModelSerializer
            if self._check_content(self.path_serializer, "from rest_framework.serializers import ModelSerializer"):
                content_urls = content_urls.replace("from rest_framework.serializers import ModelSerializer", "")
                imports = 'from rest_framework.serializers import ModelSerializer'
                with fileinput.FileInput(self.path_serializer, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, content_urls + imports), end='')
            else:
                with open(self.path_serializer, 'a') as views:
                    views.write(content_urls)
            # Atualizando o conteúdo do arquivo.
            with open(self.path_serializer, 'a') as urls:
                urls.write("\n")
                urls.write(content)
        except:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O ARQUIVO serializer.py sofreu alguma alteração")

    """
    #################################################################
    Área dos Forms
    #################################################################    
    """

    def _manage_form(self):
        """Método para configurar o Form do model informado.
        """

        try:
            self._message("Trabalhando na configuração do Form do model {}".format(self.model))
            content = self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/form.txt"))
            # Recuperando o conteúdo do snippet das urls do form
            content_urls =  self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/form_urls.txt"))
            # Interpolando os dados
            content = content.replace("$ModelClass$", self.model)
            content_urls = content_urls.replace("$ModelClass$", self.model)

            # Verificando se o arquivo forms.py existe
            if self._check_file(self.path_form) is False:
                # Criando o arquivo com o conteúdo da interpolação
                with open(self.path_form, 'w') as arquivo:
                    arquivo.write(content_urls + '\n' + content)
                return

            # Verificando se já existe configuração no forms para o Models informado
            if self._check_content(self.path_form, "class {}Form".format(self.model)):
                self._message("O model informado já possui form configurado.")
                return
            
            # Verificando se tem a importação do BaseForm
            if self._check_content(self.path_form, "from core.forms import BaseForm"):
                content_urls = content_urls.replace("from core.forms import BaseForm", "")
                imports = 'from core.forms import BaseForm'
                with fileinput.FileInput(self.path_form, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, content_urls + imports), end='')
            else:
                with open(self.path_form, 'a') as views:
                    views.write(content_urls)
            # Atualizando o conteúdo do arquivo.
            with open(self.path_form, 'a') as form:
                form.write("\n")
                form.write(content)
        except:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O ARQUIVO forms.py sofreu alguma alteração")
    
    """
    #################################################################
    Área das Views
    #################################################################    
    """

    def _manage_views(self):
        """Método para configurar as Views para o model informado.
        """

        try:
            self._message("Trabalhando na configuração das Views do model {}".format(self.model))
            # Recuperando o conteúdo do snippet da view
            content = self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/crud_views.txt"))
            # Recuperando o conteúdo do snippet das urls da view
            content_urls =  self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/crud_urls.txt"))
            # Interpolando os dados
            content = content.replace("$ModelClass$", self.model)
            content = content.replace("$app_name$", self.app_lower)
            content = content.replace("$model_name$", self.model_lower)
            content_urls = content_urls.replace("$ModelClass$", self.model)

            # Verificando se o arquivo views.py já existe
            if self._check_file(self.path_views) is False:
                # Caso o arquivo não exista ele a já adiciona o código inicial
                with open(self.path_views, 'w') as arquivo:
                    arquivo.write(content_urls + '\n' + content)
                return

            # Verificando se já existe configuração da views para o Models informado
            if self._check_content(self.path_views, "class {}ListView".format(self.model)):
                self._message("O model informado já possui as views configuradas.")
                return

            # Verificando se já tem os imports do core
            if self._check_content(self.path_views, "from core.views"):
                content_urls = content_urls.replace(
                    "from core.views import BaseListView, BaseDeleteView, BaseDetailView, BaseUpdateView, BaseCreateView", "")
                imports = 'from core.views import BaseListView, BaseDeleteView, BaseDetailView, BaseUpdateView, BaseCreateView'
                with fileinput.FileInput(self.path_views, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, content_urls + imports), end='')
            else:
                with open(self.path_views, 'a') as views:
                    views.write(content_urls)

            # Atualizadno o conteúdo do arquivo.
            with open(self.path_views, 'a') as views:
                views.write("\n")
                views.write(content)

        except:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O ARQUIVO views.py sofreu alguma alteração")

    """
    #################################################################
    Área das URLS
    #################################################################    
    """
    def _manage_url(self):
        """Método para configurar as URLS do model informado.
        """
        try:
            self._message("Trabalhando na configuração das Urls do model {}".format(self.model))
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/url.txt"))
            # Recuperando o conteúdo do snippet das urls da view
            content_urls =  self._get_snippet(os.path.join(
                self.path_core, "management/commands/snippets/url_imports.txt"))
            # Interpolando os dados
            content = content.replace("$app_name$", self.app_lower)
            content = content.replace("$model_name$", self.model_lower)
            content = content.replace("$ModelClass$", self.model)
            content_urls = content_urls.replace("$ModelClass$", self.model)
            # Verificando se o arquivo de urls já existe
            if self._check_file(self.path_urls) is False:
                # Criando o arquivo com o conteúdo da interpolação
                with open(self.path_urls, 'w') as arquivo:
                    arquivo.write(content_urls + '\n' + content)
                return
            
            if self._check_content(self.path_urls, " {}ListView".format(self.model)):
                # Já existe configuração de URL para a APP saindo da função
                self._message("O model informado já possui urls configuradas.")
                return
            
            # Verificando se já existe a configuração do index template para evitar redundância.
            if self._check_content(self.path_urls, "from core.views import IndexTemplateView"):
                content_urls = content_urls.replace("from core.views import IndexTemplateView", "")
            
            if self._check_content(self.path_urls, "from django.urls import path, include"):
                content_urls = content_urls.replace("from django.urls import path, include", "")
                imports = 'from django.urls import path, include'
                with fileinput.FileInput(self.path_urls, inplace=True) as arquivo:
                    for line in arquivo:
                        print(line.replace(
                            imports, content_urls + imports), end='')
            else:
                with open(self.path_urls, 'a') as arquivo:
                    arquivo.write(content_urls)
            
            if self._check_content(self.path_urls, "urlpatterns = ["):
                # Verificando se no arquivo já existe uma configuração da URL
                content = content.replace("urlpatterns = [", "urlpatterns += [")
                # retira 4 espaços e o \n para não ficar com quebra de linha dentro das urls
                content = content.replace("path('api/', include(router.urls)),\n    ",'')
                content = content.replace("path('', IndexTemplateView.as_view(extra_context={'app_name':app_name}), name='index-app'),\n    ",'')

            # Verificando se o arquivo já possui o app_name configurado
            if self._check_content(self.path_urls, "app_name = \'{}\'".format(self.app)):
                # Removendo a duplicidade do app_name
                content = content.replace("app_name = \'{}\'".format(self.app), "")
            
            # Atualizando o conteúdo do arquivo.
            with open(self.path_urls, 'a') as urls:
                urls.write(content)
        except:
            self._message("OCORREU UM ERRO, VERIFIQUE SE O ARQUIVO urls.py sofreu alguma alteração")
    
    """
    #################################################################
    Área do parser do HTML
    #################################################################    
    """
    def _render_modal_foreign_key(self, model, app, model_lower, field_name):
        """
        Método para renderizar o Model respectivo a foreign key do model em questão
        A possibilidade de adicionar um novo campo para a foreign key no próprio formulário
        """

        try:
            content = self._get_snippet(
                os.path.join(self.path_core, "management/commands/snippets/modal_form.txt"))
            # Interpolando o conteúdo
            content = content.replace("$ModelName$", model)
            content = content.replace("$app_name$", app)
            content = content.replace("$model_name$", model_lower)
            content = content.replace("$field_name$", field_name)
            return content
        except Exception as error:
            self._message(error)
            
    def _render_input(self, field):
        try:
            types = [
                'AutoField', 'BLANK_CHOICE_DASH', 'BigAutoField', 
                'BigIntegerField', 'BinaryField', 'BooleanField', 
                'CharField', 'CommaSeparatedIntegerField',
                'DateField', 'DateTimeField', 'DecimalField', 
                'DurationField', 'EmailField', 'Empty', 'FileField',
                'Field', 'FieldDoesNotExist', 'FilePathField',
                'FloatField', 'GenericIPAddressField', 
                'IPAddressField', 'IntegerField', 'FieldFile',
                'NOT_PROVIDED', 'NullBooleanField', 'ImageField',
                'PositiveIntegerField', 'PositiveSmallIntegerField', 
                'SlugField', 'SmallIntegerField', 'TextField', 
                'TimeField', 'URLField', 'UUIDField', 'ForeignKey', 'OneToOneField'
            ]
            iten = {}
            iten["app"], iten["model"], iten["name"] = str(field).split('.')
            iten["tipo"] = (str(
                str(type(field)).split('.')[-1:])
                .replace("[\"", "").replace("\'>\"]", ""))
            # Verificando se o tipo de campos está nos tipos conhecidos
            if iten["tipo"] in types:
                # Criando a DIV para os campos de Checkbox
                if iten["tipo"] == 'BooleanField':
                    tag_result = "<div class='form-check col-md-6'>"
                # Criando a DIV form-group
                else:
                    tag_result = "<div class='form-group col-md-6'>"
                required = 'required'
                # Verificando se o campo aceita branco ou nulo para
                # retirar o parâmetro required da tag HTML
                if ((getattr(field, 'blank', None) is True) or
                    (getattr(field, 'null', None) is True) ):
                    #TODO Verificar como tratar os casos onde
                    # o campo é blank=False
                    required = ''
                # Verificando se ele foi setado para readonly
                readonly = getattr(field, 'readonly', '')
                # Criando o Label do campo
                label = "{{{{ form.{}.label_tag }}}}".format(iten['name'])
                # Criando o HELP Text caso exista
                helptext = getattr(field, 'help_text', '')
                """ 
                #####################################################
                Tratando os tipos de campos
                #####################################################
                """
                #Tratando o campo do tipo ForeignKey
                # Adiciona o botão de adicionar um novo
                # Abre o modal para adicionar
                if  (iten.get("tipo") in ('ForeignKey', 'OneToOneField')):
                    tag_result += label
                    tag_result += '\n<div class="input-group">'
                    tag_result += "{{{{ form.{} }}}}\n".format(iten['name'])
                    tag_result += '{{% if form.{}.field.queryset.model|has_add_permission:request %}}<button type="button" class="btn btn-outline-secondary" data-toggle="modal" data-target="#form{}Modal">+</button>{{% endif %}}'\
                                    .format(iten['name'], field.related_model._meta.object_name)
                    tag_result += '</div>'
                    #Cria o modal da foreign
                    self.html_modals += self._render_modal_foreign_key(field.related_model._meta.object_name, iten['app'], field.related_model._meta.model_name, iten['name'])
                elif iten["tipo"] == 'BooleanField':
                     tag_result += "{{{{ form.{} }}}}\n{}".format(iten['name'], label)
                else:
                    tag_result += "{}\n{{{{ form.{} }}}}".format(label, iten['name'])
                """
                #####################################################
                Configurando os atributos do campo
                #####################################################
                """
                # Configurando para os campos do tipo readonly serem plain text
                if readonly is not '':
                    tag_result = tag_result.replace(
                        "class='", "class='form-control-plaintext ")
                # Adicionando a classe obrigatorio aos campos required
                if required is not '':
                    tag_result += '\n<div class="invalid-feedback">Campo Obrigatorio.</div>'
                # Adicionando o HelpText no campo
                if helptext is not '':
                    tag_result += "\n<small class='form-text text-muted'>{}</small>\n".format(helptext)
                tag_result += "{{% if form.{0}.errors  %}}{{{{ form.{0}.errors  }}}}{{% endif %}}".format(iten['name'])
                tag_result += "</div>"
                return tag_result
            else:
                print('Campo {} desconhecido'.format(field))

        except Exception as error:
            print(error)
    """
    #################################################################
    Área dos templates HTML
    #################################################################    
    """
    def _manage_render_html(self):
        """Método para renderizar os campos do models 
        para tags HTML
        """
        self._message("Trabalhando na configuração do parserhtml do model {}".format(self.model))
        try:
            # Rercuperando uma instancia do models informado
            model = self._get_model()
            if model == None:
                self._message("Favor declarar a app no settings.")
                return
            self._manage_templates()
            html_tag = ""
            self.html_modals = ""
            # Percorrendo os campos/atributos do models
            for field in iter(model._meta.fields):
                if str(field).split('.')[2] not in ('updated_on', 'created_on', 'deleted', 'enabled', 'id'):
                    html_tag += self._render_input(field)
            if html_tag is not '':
                # Pegando os templates do Model informado
                for temp in  ['create', 'update']:
                    list_template = os.path.join(
                        self.path_template_dir, "{}_{}.html".format(
                            self.model_lower, temp))
                    # Adiciona os forms no arquivo
                    with fileinput.FileInput(list_template, inplace=True) as arquivo:
                        for line in arquivo:
                            print(line.replace(
                                "<!--REPLACE_PARSER_HTML-->", 
                                html_tag), end='')
                    #Adiciona os modais das foreign keys
                    with fileinput.FileInput(list_template, inplace=True) as arquivo:
                        for line in arquivo:
                            print(line.replace(
                                "<!--REPLACE_MODAL_HTML-->", 
                                self.html_modals), end='')
        except:
            self._message("Favor colocar a url da app no urls principal.")
    '''
    Função responsável por verificar as opções passadas por parametro 
    e chamar os métodos responsáveis.

    A Função foi criada para que não ocorrece a repetição de código
    '''
    def call_methods(self, options):
        # Verificando se foram passados parâmetros opcionais
        if options['templates']:
            self._message("Trabalhando apenas os templates.")
            self._manage_templates()
            return
        elif options['api']:
            self._message("Trabalhando apenas a api.")
            # Chamando o método para tratar o serializer
            self._manage_serializer()
            # Chamando o método para tratar as views da API
            self._manage_api_view()
            # Chamado o método para tratar as urls da API
            self._manage_api_url()
            return                
        elif options['url']:
            self._message("Trabalhando apenas as urls.")
            # Chamando o método para tratar as urls
            self._manage_url()
            # Chamado o método para tratar as urls da API
            self._manage_api_url()
            return                
        elif options['forms']:
            self._message("Trabalhando apenas os forms.")
            # Chamando o método para tratar os form
            self._manage_form()
            return
        elif options['views']:
            self._message("Trabalhando apenas as views.")
            # Chamando o método para tratar as views
            self._manage_views()
        elif options['renderhtml']:
            self._manage_render_html()
            return
        else:
            # Chamando o método para tratar os form
            self._manage_form()
            # Chamando o método para tratar as views
            self._manage_views()
            # Chamando o método para tratar o serializer
            self._manage_serializer()
            # Chamando o método para tratar as urls
            self._manage_url()
            # Chamando o método para tratar as views da API
            self._manage_api_view()
            # Chamado o método para tratar as urls da API
            self._manage_api_url()
            # Chamando o método para tratar os templates
            self._manage_templates()
            # Chamando o método para gerar os formulários
            self._manage_render_html()
            return

    
    def handle(self, *args, **options):
        """Método invocado internamente pelo Command logo após a 
        validação da passagem de parâmetro.
        """
        # Verificando se o usuário passou o nome da app
        self._message("Gerando os arquivos da app")
        # Pagando o nome da App passada por parâmetro
        app = options['App'] or None
        if (self._contain_number(app) is False):
            # Removendo os espaços em branco
            self.app = app.strip()
            # Pegando o diretório absoluto atual do projeto.
            self.path_root = os.getcwd()
            # Criando o path para a APP informada.
            self.path_app = os.path.join(self.path_root, app)
            # Criando o path para a APP Core.
            self.path_core = os.path.join(self.BASE_DIR, "core")
            # Criando o path para os models baseado no App informada.
            self.path_model = os.path.join(self.path_app, "models.py")
            # Criando o path para os forms baseado na App informada.
            self.path_form = os.path.join(self.path_app, "forms.py")
            # Criando o path para as views baseado na App informada.
            self.path_views = os.path.join(self.path_app, "views.py")
            # Criando o path para as urls baseado na App informada.
            self.path_urls = os.path.join(self.path_app, "urls.py")
            # Criando o path para os serializers baseado na App informada.
            self.path_serializer = os.path.join(self.path_app, "serializers.py")
            # Criando o path para o diretório dos templates baseado na App informada.
            self.path_template_dir = os.path.join(self.path_app, "templates", self.app)
            # Criando o path para a APP informada.
            self.path_app = os.path.join(self.path_root, app)
            # Convertendo os nomes para caracteres minúsculo.
            # para serem usado nos locais que necessitem dos nomes
            # em minúsculo.
            self.app_lower = app.lower()
            # Verificando se o diretório da App informada existe
            if self._check_dir(self.path_app) is False:
                self._message("Diretório não encontrado.")
                return
            # Verifica se app esta instalada, pois precisa dela 
            # para recuperar as instancias dos models
            if apps.is_installed(self.app_lower) is False:
                self._message("Você deve colocar sua app no INSTALLED_APPS do settings.")
                return 
            #Criando uma instancia da app
            self.app_instance = apps.get_app_config(self.app_lower)
            #Verificando se o usuário passou o nome do model
            if options['Model']:
                model = options['Model'] or None
                if (self._contain_number(model) is False):
                    # Removendo os espaços em branco
                    self.model = model.strip()
                    # Verificando se existe no models.py o Model informado
                    if self._check_content(self.path_model, 'class {}'.format(self.model)) is False:
                        self._message("Model informado não encontrado.")
                        return
                try:
                    # Verifica se o model está na app informada
                    # Se o model for abstract ela retornará uma exceção LookupError
                    self.app_instance.get_model(self.model)
                    self._message("Gerando arquivos para o model {}".format(self.model))
                    # Convertendo os nomes para caracteres minúsculo.
                    # para serem usado nos locais que necessitem dos nomes
                    # em minúsculo.
                    self.model_lower = model.lower()
                    self.call_methods(options)
                    self._message("Processo concluído.")
                except LookupError:
                    self._message("Esse model é abastrato. Não vão ser gerados os arquivos.")
            else:
                # recupera todos os models da app
                for model in self.app_instance.get_models():
                    model = model.__name__
                    # Removendo os espaços em branco
                    self.model = model.strip()
                    self._message("Gerando arquivos para o model {}".format(self.model))
                    # Convertendo os nomes para caracteres minúsculo.
                    # para serem usado nos locais que necessitem dos nomes
                    # em minúsculo.
                    self.model_lower = model.lower()
                    #Chama os métodos de geração de arquivos
                    self.call_methods(options)
                    self._message("Processo concluído para o model {}.".format(self.model))
                self._message("Processo concluído.")
                return
