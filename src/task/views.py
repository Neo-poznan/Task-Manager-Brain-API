import json

from django.views.generic import View
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseNotFound
from django.db import connection
from django.db.models import Q

from core.http import FormJsonResponse
from core.mixins import ApiLoginRequiredMixin
from core.views import ModelPermissionMixin, ModelApiView
from .forms import TaskForm, CategoryCreationForm
from .models import Task, Category
from .services import TaskService, DeadlinesUpdateUseCase, TaskOrderUpdateUseCase
from .infrastructure import TaskRepository, CategoryRepository


class TasksView(
        ApiLoginRequiredMixin, 
        View,
    ):
    service = TaskService(
        task_repository=TaskRepository(
        Task, 
        connection,
        )
    )

    def get(self, request):
        data = {}
        data['chart_data'] = self.service.get_user_task_count_by_categories(
            self.request.user.id
        )
        data['tasks'] = self.service.get_ordered_user_tasks(
            self.request.user.id
        )
        return JsonResponse(data)


class TodayTasksView(
        ApiLoginRequiredMixin,
        View,
    ):
    service = TaskService(
        task_repository=TaskRepository(
            Task, 
            connection
        )
    )

    def get(self, request):
        data = {}
        data = self.service.get_user_statistics_for_today(
            self.request.user.id
        )

        return JsonResponse(data)


class DeadlinesView(
        ApiLoginRequiredMixin,
        View,
    ):

    service = TaskService(
    task_repository=TaskRepository(
            Task, 
            connection
        )
    )

    def get(self, request):
        data = {}
        data['calendar_data'] = self.service.get_user_tasks_by_deadlines(
            self.request.user.id
        )

        return JsonResponse(data)
    

class DeadlinesUpdateView(ApiLoginRequiredMixin, View):
    use_case = DeadlinesUpdateUseCase(
        task_repository=TaskRepository(
            Task, 
            connection
        )
    )

    def post(self, request):
        post_data = self.request.body.decode('utf-8')
        post_data_json = json.loads(post_data)

        self.use_case.execute(self.request.user.id, post_data_json['new_deadlines'])

        return JsonResponse({})


class TaskView(
            ModelPermissionMixin,
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

    service = TaskService(
        task_repository=TaskRepository(
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
            form.instance.order = self.service.get_next_task_order(
                self.request.user.id
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
            View,
        ):
    template_name = 'task/categories.html'
    service = TaskService(
        category_repository=CategoryRepository(Category, connection),
    )

    def get(self, request):
        categories = self.service.get_ordered_user_categories(
                self.request.user.id
            )
        return JsonResponse({'categories': categories})


class OrderUpdateView(
            ApiLoginRequiredMixin, 
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
        use_case = TaskOrderUpdateUseCase(
            task_repository=TaskRepository(
                    Task, 
                    connection,
            )
        )
        use_case.execute(
                self.request.user.id, post_data_json['order']
            )
        return HttpResponse('OK')
    
