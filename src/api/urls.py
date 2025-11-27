from django.urls import path

from .import views

app_name = 'api'

urlpatterns = [
    path('history/', views.HistoryApiView.as_view()),
    path('deadlines/', views.DeadlinesApiView.as_view()),
]

