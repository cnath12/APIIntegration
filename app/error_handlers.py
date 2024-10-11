from flask import jsonify, request

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f"404 error occurred: {request.url}")
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.warning(f"Unauthorized access attempt: {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        return jsonify({"error": "Rate limit exceeded"}), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500