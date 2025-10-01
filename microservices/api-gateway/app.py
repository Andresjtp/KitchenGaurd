"""
API Gateway Service
Routes requests to appropriate microservices
Handles authentication, rate limiting, and load balancing
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import requests
from functools import wraps
import time
import threading
from collections import defaultdict, deque

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Gateway configuration
GATEWAY_PORT = 8000

# Service registry to track available services
services = {}
service_health = {}

# Rate limiting storage
rate_limit_store = defaultdict(lambda: deque())
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds


def register_service_info(service_data):
    """Register a service in the service registry"""
    service_name = service_data["name"]
    services[service_name] = {
        "host": service_data["host"],
        "port": service_data["port"],
        "health_endpoint": service_data["health_endpoint"],
        "endpoints": service_data["endpoints"],
        "last_health_check": time.time(),
    }
    service_health[service_name] = True
    print(f"✅ Registered service: {service_name}")


def health_check_services():
    """Periodically check health of all registered services"""
    while True:
        for service_name, service_info in services.items():
            try:
                response = requests.get(service_info["health_endpoint"], timeout=5)
                service_health[service_name] = response.status_code == 200

                if service_health[service_name]:
                    print(f"✅ {service_name} is healthy")
                else:
                    print(
                        f"❌ {service_name} is unhealthy (status: {response.status_code})"
                    )

            except requests.exceptions.RequestException:
                service_health[service_name] = False
                print(f"❌ {service_name} is unreachable")

        time.sleep(30)  # Check every 30 seconds


def rate_limit():
    """Rate limiting decorator"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
            current_time = time.time()

            # Clean old requests outside the window
            client_requests = rate_limit_store[client_ip]
            while (
                client_requests
                and client_requests[0] < current_time - RATE_LIMIT_WINDOW
            ):
                client_requests.popleft()

            # Check if rate limit exceeded
            if len(client_requests) >= RATE_LIMIT_REQUESTS:
                return jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "limit": RATE_LIMIT_REQUESTS,
                        "window": RATE_LIMIT_WINDOW,
                    }
                ), 429

            # Add current request
            client_requests.append(current_time)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def authenticate():
    """Simple authentication middleware (in production, use JWT tokens)"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip auth for health checks and service registration
            if request.endpoint in ["health_check", "register_service"]:
                return f(*args, **kwargs)

            # Simple API key authentication (in production, use proper JWT)
            api_key = request.headers.get("X-API-Key")
            if not api_key or api_key != "kitchenguard-api-key":
                return jsonify({"error": "Authentication required"}), 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@app.route("/health", methods=["GET"])
def health_check():
    """API Gateway health check"""
    healthy_services = sum(1 for status in service_health.values() if status)
    total_services = len(service_health)

    return jsonify(
        {
            "service": "api-gateway",
            "status": "healthy",
            "port": GATEWAY_PORT,
            "registered_services": total_services,
            "healthy_services": healthy_services,
            "services": {
                name: "healthy" if status else "unhealthy"
                for name, status in service_health.items()
            },
        }
    )


@app.route("/register", methods=["POST"])
def register_service():
    """Register a new service with the gateway"""
    try:
        service_data = request.get_json()
        if not service_data or "name" not in service_data:
            return jsonify({"error": "Invalid service data"}), 400

        register_service_info(service_data)
        return jsonify(
            {"message": f"Service {service_data['name']} registered successfully"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/services", methods=["GET"])
@authenticate()
def list_services():
    """List all registered services"""
    return jsonify({"services": services, "health": service_health})


# Route requests to inventory service
@app.route("/api/inventory", methods=["GET", "POST"])
@app.route("/api/inventory/<int:product_id>", methods=["GET", "PUT", "DELETE"])
@app.route("/api/inventory/low-stock", methods=["GET"])
@rate_limit()
@authenticate()
def proxy_inventory_service(product_id=None):
    """Proxy requests to inventory service"""
    return proxy_to_service("inventory-service", request.path.replace("/api", ""))


def proxy_to_service(service_name, path):
    """Generic function to proxy requests to any service"""
    if service_name not in services:
        return jsonify({"error": f"Service {service_name} not found"}), 404

    if not service_health.get(service_name, False):
        return jsonify({"error": f"Service {service_name} is unhealthy"}), 503

    service_info = services[service_name]
    service_url = f"http://{service_info['host']}:{service_info['port']}{path}"

    try:
        # Forward the request to the appropriate service
        if request.method == "GET":
            response = requests.get(service_url, params=request.args, timeout=10)
        elif request.method == "POST":
            response = requests.post(service_url, json=request.get_json(), timeout=10)
        elif request.method == "PUT":
            response = requests.put(service_url, json=request.get_json(), timeout=10)
        elif request.method == "DELETE":
            response = requests.delete(service_url, timeout=10)
        else:
            return jsonify({"error": "Method not allowed"}), 405

        # Return the response from the service
        return response.content, response.status_code, dict(response.headers)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling {service_name}: {e}")
        return jsonify({"error": f"Service {service_name} unavailable"}), 503


@app.before_request
def log_request():
    """Log all incoming requests"""
    g.start_time = time.time()
    print(f"📥 {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def log_response(response):
    """Log response time"""
    if hasattr(g, "start_time"):
        duration = time.time() - g.start_time
        print(
            f"📤 {request.method} {request.path} -> {response.status_code} ({duration:.3f}s)"
        )
    return response


if __name__ == "__main__":
    print(f"🚀 Starting API Gateway on port {GATEWAY_PORT}")

    # Start health check thread
    health_thread = threading.Thread(target=health_check_services, daemon=True)
    health_thread.start()

    # Start the gateway
    app.run(debug=True, host="0.0.0.0", port=GATEWAY_PORT)
