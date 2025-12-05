import re

from django import forms
from django.utils.dateparse import parse_duration

from .models import Task as Task
from .models import Category as Category

from .helpers.colors import hex_color_to_rgba_with_default_obscurity, rgba_color_with_default_obscurity_to_hex


def parse_duration_with_days(value: str):
        if re.findall(r'^\d+ day', value):
            days_count = re.findall(r'^(\d+) day', value)[0]
            time_part = re.findall(r'\d+:\d+:\d+$', value)[0]
            hours, minutes, seconds = map(int, time_part.split(':'))
            time_part_with_days = f"{int(days_count) * 24 + hours:02}:{minutes:02}:{seconds:02}"
            return time_part_with_days
        else:
            return parse_duration(value)


class TaskForm(forms.ModelForm):


    class Meta:
        model = Task
        fields = ['name', 'description', 'category', 'deadline', 'planned_time']


    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'name-id-for-label',
            'placeholder': 'Название...',
        }),
        label='Название задачи'
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'description-id-for-label',
            'placeholder': 'Описание... (можно Markdown)',
        }),
        required=False,
        label='Описание задачи (необязательно)'
    )

    deadline = forms.DateField(
        widget=forms.DateInput(attrs={''
            'type': 'date',
            'id': 'deadline-id-for-label',
        }),
        required=False,
        label='Крайняя дата выполнения задачи (необязательно)'
    )

    planned_time = forms.DurationField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'id': 'planned-time-id-for-label',
            'step': '1',

        }),
        label = 'Планируемое время на процесс выполнения задачи (будет округлено до десятков минут)'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        object = kwargs.pop('instance', None)
        if object:
            self.initial['planned_time'] = parse_duration_with_days(str(object.planned_time))
            

class CategoryCreationForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description', 'color']


    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'name-id-for-label',
            'placeholder': 'Название',
        }),
        required=True,
        label='Название категории'
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'description-id-for-label',
            'placeholder': 'Описание... (можно Markdown)',
        }),
        required=False,
        label='Описание категории (необязательно)'
    )
    
    color = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'color',
            'id': 'color-id-for-label',
        }),
        label='Цвет категории на диаграмме'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        object = kwargs.pop('instance', None)
        if object:
            self.initial['color'] = rgba_color_with_default_obscurity_to_hex(object.color)


    def clean_color(self):
        return hex_color_to_rgba_with_default_obscurity(self.cleaned_data['color'])

