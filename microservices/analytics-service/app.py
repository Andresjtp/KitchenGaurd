"""
Analytics Microservice
Handles data analytics, reporting, and business intelligence
"""

from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from collections import defaultdict, Counter

app = Flask(__name__)

# Service configuration
SERVICE_NAME = "analytics-service"
SERVICE_PORT = 8006

# In-memory analytics storage (in production, use a time-series database like InfluxDB)
events_log = []
metrics = {
    "inventory_views": 0,
    "products_added": 0,
    "products_updated": 0,
    "products_deleted": 0,
    "total_requests": 0,
}

# Analytics cache
analytics_cache = {}
cache_expiry = {}


def register_service():
    """Register this service with the API Gateway"""
    try:
        service_info = {
            "name": SERVICE_NAME,
            "host": "localhost",
            "port": SERVICE_PORT,
            "health_endpoint": f"http://localhost:{SERVICE_PORT}/health",
            "endpoints": [
                {"path": "/analytics/dashboard", "methods": ["GET"]},
                {"path": "/analytics/inventory", "methods": ["GET"]},
                {"path": "/analytics/events", "methods": ["GET"]},
                {"path": "/events", "methods": ["POST"]},
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
            "events_processed": len(events_log),
            "metrics": metrics,
        }
    )


@app.route("/events", methods=["POST"])
def handle_event():
    """Handle events from other services for analytics"""
    try:
        event = request.get_json()
        if not event:
            return jsonify({"error": "No event data provided"}), 400

        # Add timestamp and store event
        event["processed_at"] = datetime.now().isoformat()
        events_log.append(event)

        # Update metrics
        event_type = event.get("event_type")
        if event_type == "inventory_viewed":
            metrics["inventory_views"] += 1
        elif event_type == "product_added":
            metrics["products_added"] += 1
        elif event_type == "product_updated":
            metrics["products_updated"] += 1
        elif event_type == "product_deleted":
            metrics["products_deleted"] += 1

        metrics["total_requests"] += 1

        # Clear relevant cache entries
        clear_cache_by_pattern(["dashboard", "inventory", "trends"])

        print(f"📊 Processed analytics event: {event_type}")

        return jsonify({"message": "Event processed for analytics"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analytics/dashboard", methods=["GET"])
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        cache_key = "dashboard_analytics"
        cached_result = get_from_cache(cache_key, 300)  # 5 minutes cache
        if cached_result:
            return jsonify(cached_result)

        # Time period filter
        days = request.args.get("days", 7, type=int)
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter recent events
        recent_events = [
            e
            for e in events_log
            if datetime.fromisoformat(e.get("processed_at", "1970-01-01")) > cutoff_date
        ]

        # Calculate analytics
        dashboard_data = {
            "summary": {
                "total_inventory_views": metrics["inventory_views"],
                "total_products_added": metrics["products_added"],
                "total_products_updated": metrics["products_updated"],
                "total_products_deleted": metrics["products_deleted"],
                "total_events": len(recent_events),
            },
            "activity_timeline": get_activity_timeline(recent_events),
            "event_distribution": get_event_distribution(recent_events),
            "daily_activity": get_daily_activity(recent_events, days),
            "top_categories": get_top_categories(recent_events),
            "low_stock_trends": get_low_stock_trends(recent_events),
        }

        # Cache the result
        set_cache(cache_key, dashboard_data, 300)

        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analytics/inventory", methods=["GET"])
def get_inventory_analytics():
    """Get inventory-specific analytics"""
    try:
        cache_key = "inventory_analytics"
        cached_result = get_from_cache(cache_key, 180)  # 3 minutes cache
        if cached_result:
            return jsonify(cached_result)

        # Get inventory data from inventory service
        try:
            inventory_response = requests.get(
                "http://localhost:8001/inventory", timeout=10
            )
            if inventory_response.status_code != 200:
                return jsonify({"error": "Could not fetch inventory data"}), 503

            products = inventory_response.json()
        except requests.exceptions.RequestException:
            return jsonify({"error": "Inventory service unavailable"}), 503

        # Calculate inventory analytics
        inventory_analytics = {
            "total_products": len(products),
            "total_stock_value": sum(
                p["current_stock"] * p["unit_cost"] for p in products
            ),
            "average_stock_level": sum(p["current_stock"] for p in products)
            / len(products)
            if products
            else 0,
            "categories": get_category_analytics(products),
            "stock_distribution": get_stock_distribution(products),
            "value_distribution": get_value_distribution(products),
            "suppliers": get_supplier_analytics(products),
            "low_stock_items": [p for p in products if p["current_stock"] < 10],
            "high_value_items": sorted(
                products,
                key=lambda x: x["current_stock"] * x["unit_cost"],
                reverse=True,
            )[:5],
        }

        # Cache the result
        set_cache(cache_key, inventory_analytics, 180)

        return jsonify(inventory_analytics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analytics/events", methods=["GET"])
def get_events_analytics():
    """Get detailed events analytics"""
    try:
        # Query parameters
        limit = request.args.get("limit", 100, type=int)
        event_type = request.args.get("type")

        filtered_events = events_log.copy()

        # Apply filters
        if event_type:
            filtered_events = [
                e for e in filtered_events if e.get("event_type") == event_type
            ]

        # Sort by timestamp (newest first) and limit
        filtered_events.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
        filtered_events = filtered_events[:limit]

        return jsonify(
            {
                "events": filtered_events,
                "total_events": len(events_log),
                "filtered_count": len(filtered_events),
                "available_types": list(set(e.get("event_type") for e in events_log)),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_activity_timeline(events):
    """Generate activity timeline from events"""
    timeline = []
    for event in sorted(events, key=lambda x: x.get("processed_at", ""), reverse=True)[
        :10
    ]:
        timeline.append(
            {
                "timestamp": event.get("processed_at"),
                "event_type": event.get("event_type"),
                "description": format_event_description(event),
            }
        )
    return timeline


def format_event_description(event):
    """Format event for display"""
    event_type = event.get("event_type", "unknown")
    data = event.get("data", {})

    if event_type == "product_added":
        return f"Added product: {data.get('name', 'Unknown')}"
    elif event_type == "product_updated":
        return f"Updated product ID: {data.get('product_id', 'Unknown')}"
    elif event_type == "product_deleted":
        return f"Deleted product: {data.get('name', 'Unknown')}"
    elif event_type == "low_stock_alert":
        return f"Low stock alert: {data.get('name', 'Unknown')} ({data.get('current_stock', 0)} remaining)"
    else:
        return f"Event: {event_type}"


def get_event_distribution(events):
    """Get distribution of event types"""
    event_types = [e.get("event_type") for e in events]
    return dict(Counter(event_types))


def get_daily_activity(events, days):
    """Get daily activity breakdown"""
    daily_counts = defaultdict(int)

    for event in events:
        date_str = event.get("processed_at", "")[:10]  # Get date part (YYYY-MM-DD)
        daily_counts[date_str] += 1

    # Ensure we have entries for all days
    base_date = datetime.now() - timedelta(days=days)
    daily_activity = []

    for i in range(days):
        date = base_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        daily_activity.append({"date": date_str, "count": daily_counts[date_str]})

    return daily_activity


def get_top_categories(events):
    """Get top product categories from events"""
    categories = []
    for event in events:
        if event.get("event_type") == "product_added":
            category = event.get("data", {}).get("category")
            if category:
                categories.append(category)

    return dict(Counter(categories).most_common(5))


def get_low_stock_trends(events):
    """Analyze low stock alert trends"""
    low_stock_events = [e for e in events if e.get("event_type") == "low_stock_alert"]

    return {
        "total_alerts": len(low_stock_events),
        "recent_alerts": len(
            [
                e
                for e in low_stock_events
                if datetime.fromisoformat(e.get("processed_at", "1970-01-01"))
                > datetime.now() - timedelta(days=1)
            ]
        ),
        "affected_products": len(
            set(e.get("data", {}).get("name") for e in low_stock_events)
        ),
    }


def get_category_analytics(products):
    """Analyze products by category"""
    categories = defaultdict(lambda: {"count": 0, "total_value": 0, "total_stock": 0})

    for product in products:
        category = product.get("category", "Uncategorized")
        categories[category]["count"] += 1
        categories[category]["total_value"] += (
            product["current_stock"] * product["unit_cost"]
        )
        categories[category]["total_stock"] += product["current_stock"]

    return dict(categories)


def get_stock_distribution(products):
    """Analyze stock level distribution"""
    ranges = {"0-10": 0, "11-50": 0, "51-100": 0, "100+": 0}

    for product in products:
        stock = product["current_stock"]
        if stock <= 10:
            ranges["0-10"] += 1
        elif stock <= 50:
            ranges["11-50"] += 1
        elif stock <= 100:
            ranges["51-100"] += 1
        else:
            ranges["100+"] += 1

    return ranges


def get_value_distribution(products):
    """Analyze product value distribution"""
    values = [p["current_stock"] * p["unit_cost"] for p in products]
    if not values:
        return {"min": 0, "max": 0, "average": 0, "median": 0}

    values.sort()
    n = len(values)

    return {
        "min": values[0],
        "max": values[-1],
        "average": sum(values) / n,
        "median": values[n // 2],
    }


def get_supplier_analytics(products):
    """Analyze products by supplier"""
    suppliers = defaultdict(lambda: {"count": 0, "total_value": 0})

    for product in products:
        supplier = product.get("supplier", "Unknown")
        suppliers[supplier]["count"] += 1
        suppliers[supplier]["total_value"] += (
            product["current_stock"] * product["unit_cost"]
        )

    return dict(suppliers)


def get_from_cache(key, max_age_seconds):
    """Get value from cache if not expired"""
    if key in analytics_cache and key in cache_expiry:
        if datetime.now() < cache_expiry[key]:
            return analytics_cache[key]
    return None


def set_cache(key, value, ttl_seconds):
    """Set value in cache with TTL"""
    analytics_cache[key] = value
    cache_expiry[key] = datetime.now() + timedelta(seconds=ttl_seconds)


def clear_cache_by_pattern(patterns):
    """Clear cache entries matching patterns"""
    keys_to_remove = []
    for key in analytics_cache:
        for pattern in patterns:
            if pattern in key:
                keys_to_remove.append(key)
                break

    for key in keys_to_remove:
        analytics_cache.pop(key, None)
        cache_expiry.pop(key, None)


if __name__ == "__main__":
    print(f"🚀 Starting {SERVICE_NAME} on port {SERVICE_PORT}")

    # Register with API Gateway
    register_service()

    # Start the service
    app.run(debug=True, host="0.0.0.0", port=SERVICE_PORT)
