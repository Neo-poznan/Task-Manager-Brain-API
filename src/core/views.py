from django.http.multipartparser import MultiPartParser
from django.http.response import JsonResponse, HttpResponseRedirectBase, HttpResponseBase
from django.views.generic import UpdateView


class PutFormParseMixin:

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


class ObjectDeletionMixin:

    def delete_object(self):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({}, status=204)


class SkipConfigurationCheckMixin:

    def get_template_names(self, *args, **kwargs) -> str:
        return ''
    
    def get_success_url(self, *args, **kwargs) -> str:
        return '/'


class ModelApiView(PutFormParseMixin, SkipConfigurationCheckMixin, UpdateView, ObjectDeletionMixin):

    def get(self, *args, **kwargs):
        response = self.get_response(super().get(*args, **kwargs))
        return response 
    
    def post(self, *args, **kwargs):
        response = self.get_response(super().post(*args, **kwargs))
        return response 

    def put(self, *args, **kwargs):
        response = self.get_response(super().put(*args, **kwargs))
        return response 
    
    def delete(self, *args, **kwargs):
        response = self.get_response(super().delete_object())
        return response 
    
    def get_response(self, response) -> HttpResponseBase:
        if isinstance(response, HttpResponseRedirectBase):
            return JsonResponse({})
        return response

    def get_object(self, queryset = ...):
        return self._get_object_if_exists()
    
    def _get_object_if_exists(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if not pk:
            return
        object = super().get_object()
        return object

