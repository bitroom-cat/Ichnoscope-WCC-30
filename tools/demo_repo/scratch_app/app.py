"""Main Flask application factory for storefront service."""

from flask import Flask, jsonify, render_template

from observability import init_observability
from routes.cart import cart_bp
from routes.checkout import checkout_bp
from routes.discounts import discounts_bp
from routes.inventory import inventory_bp
from routes.shipping import shipping_bp


def create_app() -> Flask:
    """Instantiate and configure Flask shop service."""
    init_observability()

    app = Flask(__name__)
    app.config["TESTING"] = False

    # Register service blueprints
    app.register_blueprint(checkout_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(shipping_bp)
    app.register_blueprint(discounts_bp)

    @app.get("/")
    def index_page():
        """Interactive storefront diagnostics dashboard."""
        return render_template("index.html")

    @app.get("/healthz")
    def health_check():
        """Service health check endpoint returning JSON status."""
        return jsonify({"status": "healthy", "service": "storefront-api"}), 200

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000)
