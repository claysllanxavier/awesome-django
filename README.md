# Awesome Django

Projeto padrão para os meus projetos que serão desenvolvidos com o Django.

Conta com o build e a dashboard completa.

## Documentation

### Installation

Add `core` to your `INSTALLED_APPS` setting:

```python
    INSTALLED_APPS = [
        # other apps
        "core",
    ]
```

Add `core.urls` to your project urlpatterns:

```python
    urlpatterns = [
        # other urls
        path('core/', include('core.urls'), name='core'),
    ]
```
Run 
```shell 
    $ python manage.py migrate
```
to create the core models.

Run 
```shell 
    $ python manage.py runserver
```
to run the server

Visit http://127.0.0.1:8000/core/ to list the apps installed in your project.  

### Usage

To generate the files of your model, create one app and write your models. The models should extends `Base`.

Example:

 ```python
 #others imports
 from core.models import Base

#Create your models here.
class NameModel(Base):
    ...
 ```
After this, run the command to generate the files of the app.

 ```shell
    $ python manage.py build <your_app_name> 
 ```
This command will generate all the forms, views, Api Rest and templates for your app based in your models.

To generate the files only one specific model, run this command:


 ```shell
    $ python manage.py build <your_app_name> <your_model_name>
 ```

 This command will generate all the forms, views, Api Rest and templates for your model.

After this procedure add your app in the main urls of your project:

```python
    urlpatterns = [
        # other urls
        path('', include('<your_app>.urls'), name='<your_app>'),
    ]
```
Run
 
```shell 
    $ python manage.py migrate
```
to create the core models.

Run 
```shell 
    $ python manage.py runserver
```
to run the server

Visit http://127.0.0.1:8000/core/ to list the apps installed in your project.

## Built With

* [Django](https://www.djangoproject.com/) - The high-level Python Web framework that encourages rapid development and clean, pragmatic design.
* [Bootstrap 4](https://getbootstrap.com/) - The open source toolkit for developing with HTML, CSS, and JS.
* [Boilerplate Manager](https://github.com/agencia-tecnologia-palmas/boilerplate-manager) - Base project
  