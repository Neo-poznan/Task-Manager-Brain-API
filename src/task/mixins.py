from django.http import JsonResponse


class UserEntityMixin:

    def get_user_entity(self):
        return self.request.user.to_domain()


class ApiLoginRequiredMixin:

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({}, status=401)
        return super().dispatch(request, *args, **kwargs)

