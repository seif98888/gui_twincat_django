from django.urls import path
from . import views

urlpatterns = [
    path('', views.home,name='home_url'),
    path('eingabe/', views.eingabe,name='eingabe_url'),
    path('ausgabe/', views.ausgabe,name='ausgabe_url'),
    path('charts/', views.charts,name='charts_url'),
    path('chart-data/', views.chart_data, name='chart_data_url'),
    path('check-trigger/', views.check_trigger, name='check_trigger_url'),
    path('get-recorded-data/', views.get_recorded_data, name='get_recorded_data_url'),
    path('nothalt/', views.nothalt, name='nothalt_url'),


]
