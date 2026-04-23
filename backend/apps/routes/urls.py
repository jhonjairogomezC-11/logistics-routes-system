from django.urls import path
from . import views
from . import auth_views

app_name = 'routes'

urlpatterns = [
    # Auth
    path('auth/login/',                      auth_views.LoginView.as_view(),           name='auth-login'),
    path('auth/logout/',                     auth_views.LogoutView.as_view(),          name='auth-logout'),
    path('auth/user/',                       auth_views.UserProfileView.as_view(),     name='auth-user'),
    
    # Routes
    path('routes/',                          views.RouteListCreateView.as_view(),      name='route-list-create'),
    path('routes/import/',                   views.RouteImportView.as_view(),          name='route-import'),
    path('routes/execute/',                  views.RouteExecuteView.as_view(),         name='route-execute'),
    path('routes/<str:id_route>/',           views.RouteDetailView.as_view(),          name='route-detail'),
    path('routes/<str:id_route>/logs/',      views.RouteLogsView.as_view(),            name='route-logs'),
    path('logs/',                            views.GlobalExecutionLogListView.as_view(), name='global-logs'),
    path('dashboard/stats/',                 views.DashboardStatsView.as_view(),       name='dashboard-stats'),
]
