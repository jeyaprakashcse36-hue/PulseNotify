
from django.contrib import admin
from django.urls import path

from pulse.views import (
    LoginView,
    PriceAlertDeactivateView,
    PriceAlertListCreateView,
    RegisterView,
    FlightPriceView,
    AdminSummaryView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/login/", LoginView.as_view(), name="login"),
    path(
        "api/alerts/",
        PriceAlertListCreateView.as_view(),
        name="alert-list-create",
    ),
    path(
        "api/alerts/<int:pk>/",
        PriceAlertDeactivateView.as_view(),
        name="alert-deactivate",
    ),
    path(
    "api/flights/price/",
    FlightPriceView.as_view(),
    name="flight-price",
    ),
    path(
    "api/admin/summary/",
    AdminSummaryView.as_view(),
    name="admin-summary",
),
]
