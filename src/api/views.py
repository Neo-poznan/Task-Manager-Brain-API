from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import View
from django.db import connection
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDictKeyError

from history.services.use_cases import HistoryUseCase
from history.models import History, SharedHistory
from history.infrastructure.database_repository import HistoryDatabaseRepository
from history.serializers import ObjectJSONEncoder
from task.models import Task, Category
from history.validators import history_dates_interval_validator, history_query_params_validator
from task.mixins import LoginRequiredMixinWithRedirectMessage
from task.infrastructure.database_repository import TaskDatabaseRepository, CategoryDatabaseRepository
from task.services.use_cases import TaskUseCase


class HistoryApiView(LoginRequiredMixinWithRedirectMessage, View):
    def get(self, request):
        try:
            from_date = self.request.GET['from_date']
            to_date = self.request.GET['to_date']
        except MultiValueDictKeyError:
            return HttpResponseBadRequest(
                '''
                <h1>400</h1>
                <p>Для запроса истории в ссылке должны быть переданы query-параметры, 
                которые должны включать временной интервал, по которому будет показана история!</p>
                '''
            )
        try:
            history_query_params_validator(from_date, to_date)
            history_dates_interval_validator(from_date, to_date)
        except ValidationError as exc:
            return HttpResponseBadRequest(
                f'<h1>400</h1><p>{exc.message}</p>'
                )
        use_case = HistoryUseCase(HistoryDatabaseRepository(
            task_model=Task, 
            history_model=History, 
            shared_history_model=SharedHistory,
            connection=connection
        ))
        history = use_case.get_user_history_statistics(
                self.request.user.to_domain(), request.GET['from_date'], request.GET['to_date']
            )
        return JsonResponse(history, encoder=ObjectJSONEncoder)


class DeadlinesApiView(LoginRequiredMixinWithRedirectMessage, View):
    def get(self, request):
        use_case = TaskUseCase(
                task_database_repository=TaskDatabaseRepository(Task, connection),
                category_database_repository=CategoryDatabaseRepository(Category),
                history_database_repository=(Task, History, SharedHistory, connection)
            )
        return JsonResponse(
                use_case.get_count_user_tasks_in_categories_by_deadlines(
                    self.request.user.to_domain()
                )
            )

