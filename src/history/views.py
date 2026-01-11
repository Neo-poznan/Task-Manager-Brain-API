from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import View, ListView
from django.db import connection
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from task.infrastructure import TaskRepository
from task.models import Task
from history.models import History, SharedHistory
from core.mixins import ApiLoginRequiredMixin
from .services import ShareHistoryService, MoveTaskToHistoryUseCase, GetUserHistoryUseCase, HistoryService, ShareHistoryUseCase
from .infrastructure import HistoryRepository, SharedHistoryRepository


class MoveTaskToHistoryView(
            ApiLoginRequiredMixin, 
            View,
        ):

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionError:
            return HttpResponseForbidden(
                '<h1>400 Forbidden</h1><p>Вы пытаетесь удалить задачу другого пользователя</p>'
            )
        except ValidationError as error:
            return JsonResponse({'context': error.messages}, status=400)

    def post(self, request, task_id: int):
        use_case = MoveTaskToHistoryUseCase(
            task_repository=TaskRepository(Task, connection),
            history_repository=HistoryRepository(
                History, 
                connection,
            )
        )
        use_case.execute(
            self.request.user.id, 
            task_id,
            self.request.POST['execution_time'],
            successful=self.request.POST['successful'],
        )
        return JsonResponse({}, status=201)


class HistoryView(
        ApiLoginRequiredMixin, 
        View
    ):
    use_case = GetUserHistoryUseCase(
        HistoryRepository(
            History, 
            connection
        )
    )

    def get(self, request):
        try:
            from_date = self.request.GET['from_date']
            to_date = self.request.GET['to_date']
        except MultiValueDictKeyError:
            return HttpResponseBadRequest(
                '''
                <h1>400</h1>
                <p>
                Для запроса истории в ссылке должны быть переданы query-параметры,
                которые должны включать временной интервал, по которому будет показана история!
                </p>
                '''
            )
        try:
            context = self.use_case.execute(
                self.request.user.id, 
                from_date, to_date
            )
            return JsonResponse({'context': context})

        except ValidationError as exc:
            return HttpResponseBadRequest(
                f'<h1>400</h1><p>{exc.message}</p>'
            )


class HistoryForTodayView(
        ApiLoginRequiredMixin, 
        View
    ):
    use_case = HistoryService(
            HistoryRepository(
                History, 
                connection
            )
        )
    def get(self, request):
        today_history_statistics = self.use_case.get_user_history_statistics_for_today(
                self.request.user.id
            )
        return JsonResponse(today_history_statistics)


class ShareHistoryView(View):
    use_case = ShareHistoryUseCase(
            SharedHistoryRepository(
                SharedHistory, 
                connection
            ),
            GetUserHistoryUseCase(
                HistoryRepository(
                    History, 
                    connection
                )
            )
        )

    def post(self, request):
        try:
            from_date = self.request.GET['from_date']
            to_date = self.request.GET['to_date']

            shared_history_link = self.use_case.execute(
                    self.request.user.id, 
                    from_date, 
                    to_date
                )   
            return JsonResponse({'key': shared_history_link})
        except MultiValueDictKeyError:
            return HttpResponseBadRequest(
                '''
                <h1>400</h1>
                <p>
                Для запроса истории в ссылке должны быть переданы query-параметры, 
                которые должны включать временной интервал, по которому будет сохранена история!
                </p>
                '''
            )
        except ValidationError as exc:
            return HttpResponseBadRequest(
                f'<h1>400</h1><p>{exc.message}</p>'
            )

    def get(self, request):
        try:
            service = ShareHistoryService(
                SharedHistoryRepository(
                    SharedHistory, 
                    connection
                )
            )
            context = service.get_shared_history_by_key(self.request.GET['key'])
            return JsonResponse(context)
        except ObjectDoesNotExist as ex:
            return HttpResponseNotFound(
                    '<h1>404 Not Found</h1><p>Такой сохраненной истории не существует</p>'
                )
    

class GetUserSharedHistories(
            ApiLoginRequiredMixin, 
            ListView
        ):
    template_name = 'history/user_shared_histories.html'
    context_object_name = 'histories'
    use_case = ShareHistoryService(
            SharedHistoryRepository(
                SharedHistory, 
                connection
            )
        )

    def get_queryset(self):
        return self.use_case.get_user_shared_histories(self.request.user.id)


class SharedHistoryDeletionView(
            ApiLoginRequiredMixin, 
            View
        ):
    use_case = ShareHistoryService(
            SharedHistoryRepository(
                SharedHistory, 
                connection
            )
        )

    def dispatch(self, request, *args, **kwargs):
        try:
            if self.request.method != 'DELETE':
                return HttpResponseBadRequest(
                        '<h1>Bab Request</h1><p>Неправильный метод запроса</p>'
                    )
            return super().dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return HttpResponseNotFound(
                    '<h1>404 Not Found</h1><p>Такой сохраненной истории не существует</p>'
                )
        except PermissionError:
            return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1><p>Вы пытаетесь удалить историю другого пользователя</p>'
                )

    def delete(self, request, *args, **kwargs):
        self.use_case.delete_user_shared_history_by_key(
                self.kwargs.get('history_key'), 
                self.get_user_entity()
            )
        return JsonResponse(
                {'redirect_url': reverse_lazy('history:user_shared_histories')}, 
                status=203
            )


class HistoryDeletionView(
            ApiLoginRequiredMixin, 
            View
        ):
    use_case = HistoryService(
        HistoryRepository(
            History,
            connection
        )
    )

    def dispatch(self, request, *args, **kwargs):
        try:
            if self.request.method != 'DELETE':
                return HttpResponseBadRequest(
                        '<h1>Bab Request</h1><p>Неправильный метод запроса</p>'
                    )
            return super().dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return HttpResponseNotFound(
                    '<h1>404 Not Found</h1><p>Такой записи в истории не существует</p>'
                )
        except PermissionError:
            return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1><p>Вы пытаетесь удалить запись в истории другого пользователя</p>'
                )

    def delete(self, request, *args, **kwargs):
        self.use_case.delete_user_history_by_id(
                self.kwargs.get('history_id'), 
                self.request.user.id
            )
        return JsonResponse({}, status=203)

