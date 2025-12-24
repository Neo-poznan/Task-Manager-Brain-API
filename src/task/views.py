import json

from django.views.generic import View
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseNotFound
from django.db import connection
from django.db.models import Q

from .forms import TaskForm, CategoryCreationForm
from .models import Task, Category
from .services.use_cases import TaskUseCase
from .infrastructure.database_repository import TaskDatabaseRepository, CategoryDatabaseRepository
from core.http import FormJsonResponse
from core.mixins import UserEntityMixin, ApiLoginRequiredMixin
from core.views import ModelPermissionMixin, ModelApiView


class TasksView(
        ApiLoginRequiredMixin, 
        UserEntityMixin, 
        View,
    ):
    use_case = TaskUseCase(
        task_database_repository=TaskDatabaseRepository(
        Task, 
        connection,
        )
    )

    def get(self, request):
        data = {}
        data['chart_data'] = self.use_case.get_user_task_count_by_categories(
            self.get_user_entity()
        )
        data['tasks'] = self.use_case.get_ordered_user_tasks(
            self.get_user_entity()
        )
        return JsonResponse(data)
    

class DeadlinesView(
        ApiLoginRequiredMixin,
        UserEntityMixin,
        View,
    ):

    use_case = TaskUseCase(
        task_database_repository=TaskDatabaseRepository(
            Task, 
            connection)
        )

    def get(self, request):
        data = {}
        data['calendar_data'] = self.use_case.get_user_tasks_by_deadlines(
            self.get_user_entity()
        )

        return JsonResponse(data)
    

class DeadlinesUpdateView(
        ApiLoginRequiredMixin,
        UserEntityMixin,
        View,
    ):

        use_case = TaskUseCase(
        task_database_repository=TaskDatabaseRepository(
            Task, 
            connection)
        )

        def post(self, request):
            post_data = self.request.body.decode('utf-8')
            post_data_json = json.loads(post_data)

            self.use_case.update_user_deadlines(self.get_user_entity(), post_data_json['new_deadlines'])

            return JsonResponse({})


class TaskView(
            ModelPermissionMixin,
            UserEntityMixin,
            ApiLoginRequiredMixin, 
            ModelApiView,
        ):
    '''
    Принимает form-data с полями:
    name: str
    description: str
    deadline: str - дата в формате YYYY-MM-DD
    category: str - category primary key
    planned_time: str время в формате HH:MM:SS

    При get запросе возвращает json с базовыми значениями формы
    '''
    form_class = TaskForm
    response_class = FormJsonResponse
    model = Task
    pk_url_kwarg = 'task_id'

    use_case = TaskUseCase(
        task_database_repository=TaskDatabaseRepository(
            Task, connection
        )
    ) 

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return HttpResponseNotFound(
                '<h1>404 Not Found</h1><p>Такой задачи не существует</p>'
            )
        except PermissionError:
            return HttpResponseForbidden(
                '<h1>400 Forbidden</h1><p>Вы пытаетесь отредактировать задачу другого пользователя</p>'
            )

    def get_form(self, form_class = None):
        form =  super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.filter(Q(user=self.request.user) | Q(is_custom=False))
        return form

    def form_valid(self, form):
        if not form.instance.order:
            form.instance.order = self.use_case.get_next_task_order(
                self.get_user_entity()
            )
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryView(
        ModelPermissionMixin,
        ApiLoginRequiredMixin, 
        ModelApiView,
    ):
    form_class = CategoryCreationForm
    response_class = FormJsonResponse
    model = Category
    pk_url_kwarg = 'category_id'

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return HttpResponseNotFound(
                '<h1>404 Not Found</h1><p>Такой категории не существует</p>'
            )
        except PermissionError:
            return HttpResponseForbidden(
                '<h1>400 Forbidden</h1><p>Вы пытаетесь отредактировать категорию другого пользователя</p>'
            )

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.is_custom = True
        return super().form_valid(form)


class CategoriesView(
            ApiLoginRequiredMixin, 
            UserEntityMixin, 
            View,
        ):
    template_name = 'task/categories.html'
    use_case = TaskUseCase(
        category_database_repository=CategoryDatabaseRepository(Category, connection),
    )

    def get(self, request):
        categories = self.use_case.get_ordered_user_categories(
                self.get_user_entity()
            )
        return JsonResponse({'categories': categories})
    

class OrderUpdateView(
            ApiLoginRequiredMixin, 
            UserEntityMixin, 
            View,
        ):
    '''
    Принимает post запрос с json, с полями:
    order: массив с id задач, отсортированных в том порядке, к котором они
    будут вставлены в БД
    '''
    
    def put(self, request):
        post_data = self.request.body.decode('utf-8')
        post_data_json = json.loads(post_data)
        use_case = TaskUseCase(
                task_database_repository=TaskDatabaseRepository(
                        Task, 
                        connection,
                    )
            )
        use_case.update_user_task_order(
                self.get_user_entity(), post_data_json['order']
            )
        return HttpResponse('OK')
    
