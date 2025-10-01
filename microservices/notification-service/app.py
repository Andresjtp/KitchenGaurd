"""
Notification Microservice
Handles alerts, notifications, and messaging
"""

from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Service configuration
SERVICE_NAME = "notification-service"
SERVICE_PORT = 8005

# In-memory notification storage (in production, use a database)
notifications = []
alert_rules = {
    "low_stock_alert": {
        "enabled": True,
        "channels": ["email", "dashboard"],
        "template": "⚠️ LOW STOCK ALERT: {name} has only {current_stock} units remaining!",
    },
    "product_added": {
        "enabled": True,
        "channels": ["dashboard"],
        "template": "✅ New product added: {name}",
    },
    "product_deleted": {
        "enabled": True,
        "channels": ["dashboard"],
        "template": "🗑️ Product removed: {name}",
    },
}


def register_service():
    """Register this service with the API Gateway"""
    try:
        service_info = {
            "name": SERVICE_NAME,
            "host": "localhost",
            "port": SERVICE_PORT,
            "health_endpoint": f"http://localhost:{SERVICE_PORT}/health",
            "endpoints": [
                {"path": "/notifications", "methods": ["GET", "POST"]},
                {"path": "/events", "methods": ["POST"]},
                {"path": "/alerts", "methods": ["GET"]},
            ],
        }

        response = requests.post(
            "http://localhost:8000/register", json=service_info, timeout=5
        )
        if response.status_code == 200:
            print(f"✅ {SERVICE_NAME} registered with API Gateway")
        else:
            print(f"⚠️ Failed to register with API Gateway: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach API Gateway: {e}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "service": SERVICE_NAME,
            "status": "healthy",
            "port": SERVICE_PORT,
            "notifications_count": len(notifications),
        }
    )


@app.route("/events", methods=["POST"])
def handle_event():
    """Handle events from other services"""
    try:
        event = request.get_json()
        if not event:
            return jsonify({"error": "No event data provided"}), 400

        event_type = event.get("event_type")
        data = event.get("data", {})

        print(f"📨 Received event: {event_type}")

        # Process the event based on type
        if event_type in alert_rules and alert_rules[event_type]["enabled"]:
            notification = create_notification(event_type, data)
            if notification:
                notifications.append(notification)
                send_notification(notification)

        return jsonify({"message": "Event processed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_notification(event_type, data):
    """Create a notification from an event"""
    rule = alert_rules.get(event_type)
    if not rule:
        return None

    try:
        message = rule["template"].format(**data)

        notification = {
            "id": len(notifications) + 1,
            "type": event_type,
            "message": message,
            "channels": rule["channels"],
            "data": data,
            "created_at": datetime.now().isoformat(),
            "sent": False,
            "priority": get_priority(event_type),
        }

        return notification
    except KeyError as e:
        print(f"❌ Template formatting error: {e}")
        return None


def get_priority(event_type):
    """Determine notification priority"""
    high_priority = ["low_stock_alert"]
    medium_priority = ["product_deleted"]

    if event_type in high_priority:
        return "high"
    elif event_type in medium_priority:
        return "medium"
    else:
        return "low"


def send_notification(notification):
    """Send notification via configured channels"""
    for channel in notification["channels"]:
        try:
            if channel == "email":
                send_email_notification(notification)
            elif channel == "dashboard":
                send_dashboard_notification(notification)
            elif channel == "sms":
                send_sms_notification(notification)
        except Exception as e:
            print(f"❌ Failed to send {channel} notification: {e}")


def send_email_notification(notification):
    """Send email notification (simulated)"""
    print(f"📧 EMAIL: {notification['message']}")
    # In production, integrate with SendGrid, SES, or similar service


def send_dashboard_notification(notification):
    """Send real-time notification to dashboard (simulated)"""
    print(f"📊 DASHBOARD: {notification['message']}")
    # In production, use WebSockets or Server-Sent Events


def send_sms_notification(notification):
    """Send SMS notification (simulated)"""
    print(f"📱 SMS: {notification['message']}")
    # In production, integrate with Twilio or similar service


@app.route("/notifications", methods=["GET"])
def get_notifications():
    """Get all notifications with filtering"""
    try:
        # Query parameters
        limit = request.args.get("limit", 50, type=int)
        priority = request.args.get("priority")
        notification_type = request.args.get("type")

        filtered_notifications = notifications.copy()

        # Apply filters
        if priority:
            filtered_notifications = [
                n for n in filtered_notifications if n["priority"] == priority
            ]

        if notification_type:
            filtered_notifications = [
                n for n in filtered_notifications if n["type"] == notification_type
            ]

        # Sort by creation time (newest first) and limit
        filtered_notifications.sort(key=lambda x: x["created_at"], reverse=True)
        filtered_notifications = filtered_notifications[:limit]

        return jsonify(
            {
                "notifications": filtered_notifications,
                "total": len(notifications),
                "filtered": len(filtered_notifications),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/notifications", methods=["POST"])
def create_manual_notification():
    """Create a manual notification"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        notification = {
            "id": len(notifications) + 1,
            "type": "manual",
            "message": data["message"],
            "channels": data.get("channels", ["dashboard"]),
            "data": data.get("data", {}),
            "created_at": datetime.now().isoformat(),
            "sent": False,
            "priority": data.get("priority", "medium"),
        }

        notifications.append(notification)
        send_notification(notification)

        return jsonify(
            {"id": notification["id"], "message": "Notification created successfully"}
        ), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/alerts", methods=["GET"])
def get_alerts():
    """Get high-priority notifications (alerts)"""
    try:
        alerts = [n for n in notifications if n["priority"] == "high"]
        alerts.sort(key=lambda x: x["created_at"], reverse=True)

        return jsonify(
            {
                "alerts": alerts[:20],  # Last 20 alerts
                "count": len(alerts),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/config", methods=["GET"])
def get_alert_config():
    """Get current alert configuration"""
    return jsonify({"alert_rules": alert_rules})


@app.route("/config", methods=["PUT"])
def update_alert_config():
    """Update alert configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No configuration data provided"}), 400

        # Update alert rules
        for event_type, config in data.items():
            if event_type in alert_rules:
                alert_rules[event_type].update(config)

        return jsonify({"message": "Configuration updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"🚀 Starting {SERVICE_NAME} on port {SERVICE_PORT}")

    # Register with API Gateway
    register_service()

    # Start the service
    app.run(debug=True, host="0.0.0.0", port=SERVICE_PORT)
