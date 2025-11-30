from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import View, ListView
from django.db import connection
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from task.models import Task
from history.models import History, SharedHistory
from task.mixins import UserEntityMixin, ApiLoginRequiredMixin
from .services.use_cases import HistoryUseCase
from .infrastructure.database_repository import HistoryDatabaseRepository
from .validators import history_query_params_validator, history_dates_interval_validator


class HistoryView(
        ApiLoginRequiredMixin, 
        UserEntityMixin, 
        View
    ) :
    use_case = HistoryUseCase(
            HistoryDatabaseRepository(
                Task, 
                History, 
                SharedHistory, 
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
            history_query_params_validator(from_date, to_date)
            history_dates_interval_validator(from_date, to_date)
        except ValidationError as exc:
            return HttpResponseBadRequest(
                f'<h1>400</h1><p>{exc.message}</p>'
            )        


        context = self.use_case.get_user_history_statistics(
                self.get_user_entity(), 
                from_date, to_date
            )
        context['title'] = 'История'
        return JsonResponse({'context': context})


class ShareHistoryView(UserEntityMixin, View):
    use_case = HistoryUseCase(
            HistoryDatabaseRepository(
                Task, 
                History, 
                SharedHistory, 
                connection
            )
        )

    def post(self, request):
        try:
            from_date = self.request.GET['from_date']
            to_date = self.request.GET['to_date']
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
        try:
            history_query_params_validator(from_date, to_date)
            history_dates_interval_validator(from_date, to_date)
        except ValidationError as exc:
            return HttpResponseBadRequest(
                f'<h1>400</h1><p>{exc.message}</p>'
            )
        shared_history_link = self.use_case.save_user_shared_history(
                self.get_user_entity(), 
                from_date, 
                to_date
            )   
        return JsonResponse({'key': shared_history_link})

    def get(self, request):
        try:
            context = self.use_case.get_shared_history_by_key(self.request.GET['key'])
            
            context['title'] = 'История ' + context['owner'].username 
            return render(request, 'history/history.html', context=context)
        except ObjectDoesNotExist as ex:
            return HttpResponseNotFound(
                    '<h1>404 Not Found</h1><p>Такой сохраненной истории не существует</p>'
                )
    

class GetUserSharedHistories(
            ApiLoginRequiredMixin, 
            UserEntityMixin, 
            ListView
        ):
    template_name = 'history/user_shared_histories.html'
    context_object_name = 'histories'
    use_case = HistoryUseCase(HistoryDatabaseRepository(
            Task, 
            History, 
            SharedHistory, 
            connection
            )
        )

    def get_queryset(self):
        return self.use_case.get_user_shared_histories(self.get_user_entity())


class SharedHistoryDeletionView(
            ApiLoginRequiredMixin, 
            UserEntityMixin, 
            View
        ):
    use_case = HistoryUseCase(
        HistoryDatabaseRepository(
            Task, 
            History, 
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
            UserEntityMixin, 
            View
        ):
    use_case = HistoryUseCase(
            HistoryDatabaseRepository(
                Task, 
                History, 
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
                    '<h1>404 Not Found</h1><p>Такой записи в истории не существует</p>'
                )
        except PermissionError:
            return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1><p>Вы пытаетесь удалить запись в истории другого пользователя</p>'
                )

    def delete(self, request, *args, **kwargs):
        self.use_case.delete_user_history_by_id(
                self.kwargs.get('history_id'), 
                self.get_user_entity()
            )
        return JsonResponse({}, status=203)

