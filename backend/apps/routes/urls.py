from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('routes/',                            views.RouteListCreateView.as_view(),  name='route-list-create'),
    path('routes/import/',                     views.RouteImportView.as_view(),      name='route-import'),
    path('routes/execute/',                    views.RouteExecuteView.as_view(),     name='route-execute'),
    path('routes/<int:id_route>/',             views.RouteDetailView.as_view(),      name='route-detail'),
    path('routes/<int:id_route>/logs/',        views.RouteLogsView.as_view(),        name='route-logs'),
    path('logs/',                              views.GlobalExecutionLogListView.as_view(), name='global-logs'),
    path('dashboard/stats/',                   views.DashboardStatsView.as_view(),   name='dashboard-stats'),
]
