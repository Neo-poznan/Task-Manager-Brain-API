import json

from django.views.generic import CreateView, UpdateView, View, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotFound
from django.shortcuts import render
from django.db import connection
from django.http import QueryDict

from django.http.multipartparser import MultiPartParser

from .mixins import TitleMixin, UserEntityMixin, LoginRequiredMixinWithRedirectMessage
from .forms import TaskCreationForm, CategoryCreationForm, TaskHistoryForm
from .models import Task, Category
from .services.use_cases import TaskUseCase
from .infrastructure.database_repository import TaskDatabaseRepository, CategoryDatabaseRepository
from history.infrastructure.database_repository import HistoryDatabaseRepository
from history.models import History, SharedHistory
from task.http import FormJsonResponse


class FormParseMixin:
    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        if self.request.method == "PUT":
            parsed = MultiPartParser(self.request.META, self.request, self.request.upload_handlers).parse()
            kwargs.update(
                {
                    "data": parsed[0],
                    "files": parsed[1],
                }
            )
        return kwargs


class ModelPermissionMixin:
    def get_object(self, queryset = ...):
        object = super().get_object()
        if object is None:
            return
        elif not object.user == self.request.user:
            raise PermissionError('Permission denied')
        return object


class DeleteMixin:
    def delete_object(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()


class ModelApiView(FormParseMixin, UpdateView, DeleteMixin):
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())
    
    def post(self, *args, **kwargs):
        self.request.POST
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        super().put(*args, **kwargs)
        return JsonResponse({})
    
    def delete(self, *args, **kwargs):
         self.delete_object()
         return JsonResponse({})

    def get_object(self, queryset = ...):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if not pk:
            return
        object = super().get_object()
        return object


class MyTasksView(
            LoginRequiredMixinWithRedirectMessage, 
            UserEntityMixin, 
            View,
        ):
    template_name = 'task/index.html'
    use_case = TaskUseCase(
            task_database_repository=TaskDatabaseRepository(
                Task, 
                connection)
            )

    def get(self, request):
        data = {}
        data['chart_data'] = self.use_case.get_user_task_count_by_categories(
            self.get_user_entity()
        )
        data['calendar_data'] = self.use_case.get_count_user_tasks_in_categories_by_deadlines(
            self.get_user_entity()
        )
        data['tasks'] = self.use_case.get_ordered_user_tasks(
            self.get_user_entity()
        )
        return JsonResponse(data)


class TaskView(
            ModelPermissionMixin,
            UserEntityMixin,
            LoginRequiredMixinWithRedirectMessage, 
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
    form_class = TaskCreationForm
    response_class = FormJsonResponse
    template_name = ''
    success_url = '/'
    model = Task
    pk_url_kwarg = 'task_id'

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
    
    def form_valid(self, form):
        use_case = TaskUseCase(
            task_database_repository=TaskDatabaseRepository(
                Task, connection
            )
        ) 
        form.instance.order = use_case.get_next_task_order(
            self.get_user_entity()
        )
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryView(
        ModelPermissionMixin,
        LoginRequiredMixinWithRedirectMessage, 
        ModelApiView,
    ):
    form_class = CategoryCreationForm
    response_class = FormJsonResponse
    model = Category
    success_url = '/'
    template_name = ''
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
            LoginRequiredMixinWithRedirectMessage, 
            UserEntityMixin, 
            View
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
            LoginRequiredMixinWithRedirectMessage, 
            UserEntityMixin, 
            View
        ):
    '''
    Принимает post запрос с json, с полями:
    order: массив с id задач, отсортированных в том порядке, к котором они
    будут вставлены в БД
    '''

    def get(self, request):
        return HttpResponseBadRequest(
                '<h1>Bab Request</h1><p>Неправильный метод запроса</p>'
            )
    
    def put(self, request):
        post_data = self.request.body.decode('utf-8')
        post_data_json = json.loads(post_data)
        use_case = TaskUseCase(
                task_database_repository=TaskDatabaseRepository(
                        Task, 
                        connection
                    )
            )
        use_case.update_user_task_order(
                self.get_user_entity(), post_data_json['order']
            )
        return HttpResponse('OK')


class TaskCompletionView(
            LoginRequiredMixinWithRedirectMessage, 
            UserEntityMixin, 
            TitleMixin, 
            View
        ):
    title = 'Подтверждение выполнения задачи'

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionError:
            return HttpResponseForbidden(
                    '<h1>400 Forbidden</h1><p>Вы пытаетесь удалить задачу другого пользователя</p>'
                )

    def get(self, request, task_id: int):
        return render(
            request, 
            'task/save_task_to_history.html',
            context={
                'form': TaskHistoryForm(), 
                'label': 'Сколько времени вам понадобилось на процесс выполнения непосредственно этой задачи'
                }
        )

    def post(self, request, task_id: int):
        use_case = TaskUseCase(
            task_database_repository=TaskDatabaseRepository(Task, connection),
            history_database_repository=HistoryDatabaseRepository(
                    Task, 
                    History, 
                    SharedHistory, 
                    connection
                )
        )
        use_case.save_completed_task_to_history(
                self.get_user_entity(), 
                task_id, 
                self.request.POST['execution_time']
            )
        return HttpResponseRedirect(reverse_lazy('task:my_tasks'))
    

class TaskFailView(
            LoginRequiredMixinWithRedirectMessage, 
            UserEntityMixin, 
            TitleMixin, 
            View
        ): 
    title = 'Подтверждение провала задачи'

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionError:
            return HttpResponseForbidden(
                    '<h1>400 Forbidden</h1><p>Вы пытаетесь удалить задачу другого пользователя</p>'
                )

    def get(self, request, task_id: int):
        return render(
            request,
            'task/save_task_to_history.html', 
            context={
                'form': TaskHistoryForm(), 
                'label': 'Сколько времени вам понадобилось на то, чтобы понять, что вы не сможете выполнить задачу'
            }
        )

    def post(self, request, task_id: int):
        use_case = TaskUseCase(
            task_database_repository=TaskDatabaseRepository(Task, connection),
            history_database_repository=HistoryDatabaseRepository(
                Task, 
                History,
                SharedHistory, 
                connection
            )
        )
        use_case.save_failed_task_to_history(
            self.get_user_entity(), 
            task_id, 
            self.request.POST['execution_time']
        )

        return HttpResponseRedirect(reverse_lazy('task:my_tasks'))
    
