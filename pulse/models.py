
from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class PriceAlert(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        TRIGGERED = "TRIGGERED", "Triggered"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="price_alerts",
    )
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    threshold_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.origin} to {self.destination} "
            f"at {self.threshold_price}"
        )


class NotificationLog(models.Model):
    alert = models.ForeignKey(
        PriceAlert,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    triggered_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    message = models.TextField()
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-notified_at"]

    def __str__(self):
        return (
            f"Alert {self.alert_id}: "
            f"{self.triggered_price} at {self.notified_at}"
        )
