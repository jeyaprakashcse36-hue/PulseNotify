
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
import random
from django.db.models import Count, F, Value
from django.db.models.functions import Concat
from .models import NotificationLog
from .permissions import IsAdminRole

from .models import PriceAlert
from .serializers import RegisterSerializer, PriceAlertSerializer
User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Registration successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.profile.role,
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.profile.role,
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

class PriceAlertListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alerts = PriceAlert.objects.filter(user=request.user)
        serializer = PriceAlertSerializer(alerts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PriceAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert = serializer.save(user=request.user)

        return Response(
            PriceAlertSerializer(alert).data,
            status=status.HTTP_201_CREATED,
        )


class PriceAlertDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        alert = get_object_or_404(
            PriceAlert,
            pk=pk,
            user=request.user,
        )

        if alert.status != PriceAlert.Status.INACTIVE:
            alert.status = PriceAlert.Status.INACTIVE
            alert.save(update_fields=["status"])

        return Response(status=status.HTTP_204_NO_CONTENT)

class FlightPriceView(APIView):
    permission_classes = [AllowAny]

    ROUTE_PRICES = {
        "MAA-DEL": (4000, 8000),
        "MAA-BOM": (3000, 6000),
        "DEL-BOM": (2500, 5500),
        "BLR-DEL": (3500, 7000),
        "MAA-BLR": (2000, 5000),
    }

    def get(self, request):
        route = request.query_params.get("route", "").strip().upper()

        if not route:
            return Response(
                {"detail": "The route query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if route not in self.ROUTE_PRICES:
            return Response(
                {"detail": "Route not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        min_price, max_price = self.ROUTE_PRICES[route]
        price = random.randint(min_price, max_price)

        return Response(
            {
                "route": route,
                "price": price,
                "currency": "INR",
            },
            status=status.HTTP_200_OK,
        )


class AdminSummaryView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        total_alerts = PriceAlert.objects.count()

        active_alerts = PriceAlert.objects.filter(
            status=PriceAlert.Status.ACTIVE
        ).count()

        triggered_alerts = PriceAlert.objects.filter(
            status=PriceAlert.Status.TRIGGERED
        ).count()

        total_notifications = NotificationLog.objects.count()

        top_routes = list(
            PriceAlert.objects
            .annotate(
                route=Concat(
                    F("origin"),
                    Value("-"),
                    F("destination"),
                )
            )
            .values("route")
            .annotate(alert_count=Count("id"))
            .order_by("-alert_count", "route")[:5]
        )

        return Response(
            {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "total_notifications": total_notifications,
                "top_routes": top_routes,
            },
            status=status.HTTP_200_OK,
        )
