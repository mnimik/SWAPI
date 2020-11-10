from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('fetch', views.get_swapi, name='fetch'),
    path('info/<str:csv_name>', views.get_info, name='info'),
    path('counter-table', views.counter_table, name='counter'),
]
