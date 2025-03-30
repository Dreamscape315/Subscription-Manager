"""Route handlers for redirects."""
from flask import Blueprint, redirect, abort, url_for

from app.models.models import RedirectMapping

# Blueprint for redirect routes
redirect_bp = Blueprint('redirect', __name__, url_prefix='/sub')

@redirect_bp.route('/<formatted_name>')
def redirect_to_subscription(formatted_name):
    """Redirect to the actual subscription URL."""
    mapping = RedirectMapping.query.filter_by(unique_id=formatted_name).first()
    if mapping:
        return redirect(mapping.target_url)
    return abort(404, "Not Found")

