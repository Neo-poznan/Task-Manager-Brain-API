from django.urls import path

from . import views

app_name = 'task'

urlpatterns = [
    path('tasks/', views.MyTasksView.as_view(), name='my_tasks'),
    path('task/<int:task_id>/', views.TaskView.as_view()),
    path('task/', views.TaskView.as_view()),
    path('category/<int:category_id>/', views.CategoryView.as_view()), 
    path('category/', views.CategoryView.as_view()), 
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    path('update-order/', views.OrderUpdateView.as_view(), name='order_update'),
    path('complete-task/<int:task_id>/', views.TaskCompletionView.as_view(), name='task_completion'),
    path('fail-task/<int:task_id>/', views.TaskFailView.as_view(), name='task_fail'),

]

