import json

from django.views.generic import View
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseNotFound
from django.db import connection

from core.http import FormJsonResponse
from core.mixins import ApiLoginRequiredMixin
from .models import Task, Category
from .services import CategoryService, CategoryUseCase, TaskService, DeadlinesUpdateUseCase, TaskOrderUpdateUseCase, TaskUseCase
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
            ApiLoginRequiredMixin, 
            View,
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

    use_case = TaskUseCase(
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

    def get(self, request, task_id):
        task = self.use_case.get(
            task_id,
            self.request.user.id,
        )
        print(f'Fetched task: {task}')  # Debug statement
        return JsonResponse(task)
    
    def post(self, request):
        post_data = self.request.body.decode('utf-8')
        post_data_json = json.loads(post_data)

        self.use_case.create(
            self.request.user.id,
            post_data_json,
        )

        return JsonResponse({})
    
    def put(self, request, task_id):
        put_data = self.request.body.decode('utf-8')
        put_data_json = json.loads(put_data)

        self.use_case.update(
            self.request.user.id,
            task_id,
            put_data_json,
        )

        return JsonResponse({})


class CategoryView(
        ApiLoginRequiredMixin, 
        View,
    ):
    response_class = FormJsonResponse
    model = Category
    use_case = CategoryUseCase(
        category_repository=CategoryRepository(Category, connection),
    )

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
        except ValueError as e:
            return HttpResponseForbidden(
                f'<h1>400 Forbidden</h1><p>{str(e)}</p>'
            )

    def get(self, request, category_id):
        category = self.use_case.get(
            category_id,
            self.request.user.id,
        )
        return JsonResponse(category)
    
    def post(self, request):
        post_data = self.request.body.decode('utf-8')
        post_data_json = json.loads(post_data)

        self.use_case.create(
            self.request.user.id,
            post_data_json,
        )

        return JsonResponse({})
    
    def put(self, request, category_id):
        put_data = self.request.body.decode('utf-8')
        put_data_json = json.loads(put_data)

        self.use_case.update(
            self.request.user.id,
            category_id,
            put_data_json,
        )

        return JsonResponse({})


class CategoriesView(
            ApiLoginRequiredMixin, 
            View,
        ):
    template_name = 'task/categories.html'
    service = CategoryService(
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
        try:
            use_case.execute(
                self.request.user.id, post_data_json['order']
            )
            return HttpResponse('OK')
        except PermissionError:
            return HttpResponseForbidden('Вы пытаетесь изменить задачу другого пользователя!')
        
