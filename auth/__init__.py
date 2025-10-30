from flask import Blueprint

# The *blueprint name* is "auth" so your endpoints are auth.*
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")