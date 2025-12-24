from typing import Union, Any

from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.forms import ModelChoiceField, FileField, ModelForm
from django.db.models.fields.files import FieldFile


class FormJsonResponse(TemplateResponse):
    '''
    This response class converts form to json and 
    allow to return json response in 
    django generic view classes
    '''
    def __init__(self, request, template, context=None, content_type=None, status=None, charset=None, using=None):
        super().__init__(request, template, context, content_type, status, charset, using)  

    def render(self):
        form = self.context_data['form']
        if form.errors:
            return JsonResponse({'context': str(form.errors).replace('__all__', '')}, status=400)
        else:
            return JsonResponse({'context': self._get_form_initial_values(form)}, status=200)

    def _get_form_initial_values(self, form: ModelForm) -> dict[str, Any]:
        '''
        Returned dict example structure:
        {
            'username': 'John_952'
            'first_name': None
            'role': '1'
            'role_choices': [{'id': 1,'name': 'Admin'}, {'id': 2, 'name': 'User'}]
            'avatar': <FieldFile: '/media/user_images/avatar123.jpg'>
        }
        '''
        form_initial_values = {}
        form_initial_values.update(self._get_all_initial_values_from_form(form))
        form_initial_values.update(self._get_choices_of_form_choice_fields_from_form(form))
        form_initial_values.update(self._get_file_urls_from_form(form))
        form_initial_values.update(self._get_form_null_fields(form))
        return form_initial_values
    
    def _get_all_initial_values_from_form(self, form: ModelForm) -> dict[str, str]:
        return {field_name: str(field_value) for field_name, field_value in form.initial.items()}

    def _get_file_urls_from_form(self, form: ModelForm) -> dict[str, FieldFile]:
        form_file_fields = self._get_form_file_fields(form)
        return {field_name: form.initial[field_name].url for field_name, field_value in form_file_fields.items()}

    def _get_form_file_fields(self, form) -> dict[str, FileField]:
        return dict(filter(lambda item: isinstance(item[1], FileField), form.fields.items()))  

    def _get_choices_of_form_choice_fields_from_form(self, form: ModelForm) -> dict[str, list[dict[str, Union[str, int]]]]:
        form_choice_fields = self._get_form_choice_fields(form)
        choice_fields_choices = {}
        for field_name, field in form_choice_fields.items():
            choice_fields_choices[field_name + '_choices'] = list(map(lambda item: {'id': item.id, 'name': item.name}, field.queryset))
        return choice_fields_choices

    def _get_form_choice_fields(self, form: ModelForm) -> dict[str, ModelChoiceField]:
        return dict(filter(lambda item: isinstance(item[1], ModelChoiceField), form.fields.items()))
    
    def _get_form_null_fields(self, form: ModelForm) -> dict[str, None]:
        return {field_name: field_value for field_name, field_value in form.initial.items() if field_value is None}

