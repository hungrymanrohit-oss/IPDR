"""
URL patterns for flows app.
"""
from django.urls import path
from . import views

app_name = 'flows'

urlpatterns = [
    path('', views.flow_list, name='flow_list'),
    path('<str:flow_id>/', views.flow_detail, name='flow_detail'),
    path('statistics/', views.flow_statistics, name='flow_statistics'),
    path('alerts/', views.flow_alerts, name='flow_alerts'),
    path('interfaces/', views.network_interfaces, name='network_interfaces'),
]