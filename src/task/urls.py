from django.urls import path

from . import views

app_name = 'task'

urlpatterns = [
    path('tasks/', views.MyTasksView.as_view(), name='my_tasks'),
    path('create-task/', views.TaskCreationView.as_view(), name='task_creation'),
    path('create-category/', views.CategoryCreationView.as_view(), name='category_creation'),
    path('task/<int:task_id>/', views.TaskUpdateView.as_view(), name='task'),
    path('category/<int:category_id>/', views.CategoryUpdateView.as_view(), name='category'),
    path('delete-category/<int:category_id>/', views.CategoryDeletionView.as_view(), name='category_deletion'),
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    path('update-order/', views.OrderUpdateView.as_view(), name='order_update'),
    path('complete-task/<int:task_id>/', views.TaskCompletionView.as_view(), name='task_completion'),
    path('fail-task/<int:task_id>/', views.TaskFailView.as_view(), name='task_fail'),

]

