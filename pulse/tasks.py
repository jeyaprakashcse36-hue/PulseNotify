
from decimal import Decimal

import requests
from celery import shared_task
from django.db import transaction

from .models import NotificationLog, PriceAlert


@shared_task
def check_prices():
    checked = 0
    queued = 0
    failed = 0

    alerts = PriceAlert.objects.filter(
        status=PriceAlert.Status.ACTIVE
    ).iterator()

    for alert in alerts:
        checked += 1
        route = f"{alert.origin}-{alert.destination}"

        try:
            response = requests.get(
                "http://127.0.0.1:8000/api/flights/price/",
                params={"route": route},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            current_price = Decimal(str(data["price"]))

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ):
            failed += 1
            continue

        if current_price <= alert.threshold_price:
            send_notification.delay(
                alert.id,
                str(current_price),
            )
            queued += 1

    return {
        "checked": checked,
        "notifications_queued": queued,
        "failed_price_checks": failed,
    }


@shared_task
def send_notification(alert_id, current_price):
    with transaction.atomic():
        try:
            alert = (
                PriceAlert.objects
                .select_for_update()
                .get(pk=alert_id)
            )
        except PriceAlert.DoesNotExist:
            return {"status": "alert_not_found"}

        if alert.status != PriceAlert.Status.ACTIVE:
            return {"status": "already_processed"}

        price = Decimal(str(current_price))

        if price > alert.threshold_price:
            return {"status": "threshold_not_met"}

        NotificationLog.objects.create(
            alert=alert,
            triggered_price=price,
            message=(
                f"Flight price for {alert.origin} to "
                f"{alert.destination} is INR {price}; "
                f"your threshold is INR {alert.threshold_price}."
            ),
        )

        alert.status = PriceAlert.Status.TRIGGERED
        alert.save(update_fields=["status"])

    return {
        "status": "triggered",
        "alert_id": alert_id,
        "price": str(price),
    }
