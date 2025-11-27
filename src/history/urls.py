from django.urls import path

from . import views

app_name = 'history'

urlpatterns = [
    path('', views.HistoryView.as_view(), name='history'),
    path('share/', views.ShareHistoryView.as_view(), name='share'),
    path('my-shared-histories/', views.GetUserSharedHistories.as_view(), name='user_shared_histories'),
    path('delete-shared-history/<str:history_key>/', views.SharedHistoryDeletionView.as_view(), name='delete_shared_history'),
    path('delete-history/<int:history_id>/', views.HistoryDeletionView.as_view(), name='delete_history'),
]

