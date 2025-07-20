"""
URL patterns for API app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'flows', views.NetworkFlowViewSet)
router.register(r'statistics', views.FlowStatisticsViewSet)
router.register(r'alerts', views.FlowAlertViewSet)
router.register(r'interfaces', views.NetworkInterfaceViewSet)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('flows/top-talkers/', views.TopTalkersView.as_view(), name='top-talkers'),
    path('flows/protocols/', views.ProtocolDistributionView.as_view(), name='protocols'),
    path('flows/bandwidth/', views.BandwidthView.as_view(), name='bandwidth'),
    path('flows/geographic/', views.GeographicDistributionView.as_view(), name='geographic'),
    path('flows/realtime/', views.RealtimeFlowsView.as_view(), name='realtime'),
]