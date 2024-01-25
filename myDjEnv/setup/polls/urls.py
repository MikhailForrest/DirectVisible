from django.urls import path
from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path('map', views.map_button, name='map'),
    path('zones', views.zones, name='zones'),
    path('fortraces', views.fortraces, name = 'fortraces'),
    path('firehose', views.firehose, name = 'firehose'),
    path('heights',views.heights, name = 'heights')

]