
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from pulse.models import NotificationLog, PriceAlert, UserProfile
from pulse.tasks import send_notification

User = get_user_model()


class NotificationTaskTests(TestCase):
    """Test threshold handling and duplicate notification protection."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="notification_user",
            password="TestPassword123!",
        )
        self.alert = PriceAlert.objects.create(
            user=self.user,
            origin="MAA",
            destination="BLR",
            threshold_price="5000.00",
        )

    def test_price_below_threshold_triggers_notification(self):
        result = send_notification.apply(
            args=[self.alert.id, "4000.00"]
        ).get()

        self.alert.refresh_from_db()

        self.assertEqual(result["status"], "triggered")
        self.assertEqual(self.alert.status, PriceAlert.Status.TRIGGERED)
        self.assertEqual(
            NotificationLog.objects.filter(alert=self.alert).count(),
            1,
        )

    def test_price_equal_to_threshold_triggers_notification(self):
        result = send_notification.apply(
            args=[self.alert.id, "5000.00"]
        ).get()

        self.alert.refresh_from_db()

        self.assertEqual(result["status"], "triggered")
        self.assertEqual(self.alert.status, PriceAlert.Status.TRIGGERED)
        self.assertEqual(
            NotificationLog.objects.filter(alert=self.alert).count(),
            1,
        )

    def test_price_above_threshold_does_not_trigger(self):
        result = send_notification.apply(
            args=[self.alert.id, "5000.01"]
        ).get()

        self.alert.refresh_from_db()

        self.assertEqual(result["status"], "threshold_not_met")
        self.assertEqual(self.alert.status, PriceAlert.Status.ACTIVE)
        self.assertEqual(
            NotificationLog.objects.filter(alert=self.alert).count(),
            0,
        )

    def test_reprocessing_does_not_create_duplicate_notifications(self):
        first = send_notification.apply(
            args=[self.alert.id, "4000.00"]
        ).get()

        second = send_notification.apply(
            args=[self.alert.id, "3500.00"]
        ).get()

        self.assertEqual(first["status"], "triggered")
        self.assertEqual(second["status"], "already_processed")
        self.assertEqual(
            NotificationLog.objects.filter(alert=self.alert).count(),
            1,
        )


class AlertAccessTests(APITestCase):
    """Test that users can access only their own alerts."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="alert_user_a",
            password="TestPassword123!",
        )
        self.user_b = User.objects.create_user(
            username="alert_user_b",
            password="TestPassword123!",
        )

        self.alert_a = PriceAlert.objects.create(
            user=self.user_a,
            origin="MAA",
            destination="BLR",
            threshold_price="4000.00",
        )
        self.alert_b = PriceAlert.objects.create(
            user=self.user_b,
            origin="MAA",
            destination="DEL",
            threshold_price="5000.00",
        )

    def test_user_sees_only_own_alerts(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/alerts/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.alert_a.id})
        self.assertNotIn(self.alert_b.id, returned_ids)

    def test_user_cannot_deactivate_another_users_alert(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.delete(
            f"/api/alerts/{self.alert_b.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.alert_b.refresh_from_db()
        self.assertEqual(self.alert_b.status, PriceAlert.Status.ACTIVE)


class AdminSummaryPermissionTests(APITestCase):
    """Test role-based access to the admin summary."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="summary_user",
            password="TestPassword123!",
        )
        self.admin_user = User.objects.create_user(
            username="summary_admin",
            password="TestPassword123!",
        )

        profile, _ = UserProfile.objects.get_or_create(
            user=self.admin_user
        )
        profile.role = UserProfile.Role.ADMIN
        profile.save()

        PriceAlert.objects.create(
            user=self.user,
            origin="MAA",
            destination="BLR",
            threshold_price="5000.00",
            status=PriceAlert.Status.ACTIVE,
        )

    def test_regular_user_cannot_access_admin_summary(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/admin/summary/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_summary(self):
        self.client.force_authenticate(user=self.admin_user)

        self.admin_user.refresh_from_db()
        self.admin_user.profile.refresh_from_db()

        # print("Admin username:", self.admin_user.username)
        # print("Admin profile role:", self.admin_user.profile.role)
        # print("Is authenticated:", self.admin_user.is_authenticated)

        response = self.client.get("/api/admin/summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RegistrationAndFlightPriceTests(APITestCase):
    def test_registration_creates_user_with_default_user_role(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "new_test_user",
                "email": "newuser@example.com",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="new_test_user")
        self.assertTrue(user.check_password("StrongTestPassword123!"))
        self.assertEqual(user.profile.role, UserProfile.Role.USER)

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(
            username="existing_test_user",
            password="StrongTestPassword123!",
        )

        response = self.client.post(
            "/api/register/",
            {
                "username": "existing_test_user",
                "email": "another@example.com",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_login_returns_401(self):
        response = self.client.post(
            "/api/login/",
            {
                "username": "unknown_user",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unknown_flight_route_returns_404(self):
        response = self.client.get(
            "/api/flights/price/",
            {"route": "MAA-XYZ"},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_flight_route_returns_400(self):
        response = self.client.get("/api/flights/price/")

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_flight_price_is_within_configured_range(self):
        response = self.client.get(
            "/api/flights/price/",
            {"route": "MAA-BLR"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["route"], "MAA-BLR")
        self.assertEqual(response.data["currency"], "INR")
        self.assertGreaterEqual(response.data["price"], 2000)
        self.assertLessEqual(response.data["price"], 5000)
