from django.urls import path

from . import views


urlpatterns = [
    path("", views.ClientElectricBillListView.as_view()),
    path("<int:pk>/", views.ClientElectricBillDetailView.as_view()),
    path("create/", views.ClientElectricBillCreateView.as_view()),
]
                                                                                                                                                                                                                                                                                     from django.urls import path

from . import views


urlpatterns = [
    path("", views.ClientElectricBillListView.as_view()),
    path("<int:pk>/", views.ClientElectricBillDetailView.as_view()),
    path("create/", views.ClientElectricBillCreateView.as_view()),
]
