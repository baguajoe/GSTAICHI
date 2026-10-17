"""Tai Chi Company subscription app API, registered at /api/tcc."""
from flask import Blueprint, jsonify
from .models import db, SiteSettings, Tier
from .tcc_auth import role_required, get_current_user

tcc = Blueprint('tcc', __name__)


@tcc.route('/settings', methods=['GET'])
def get_settings():
    """Public branding and contact info. Every name, color, phone and address in the app comes from here."""
    return jsonify(SiteSettings.get().serialize_public())


@tcc.route('/tiers', methods=['GET'])
def get_tiers():
    """Tiers with their currently offered plans and prices (from the database, never hard-coded)."""
    tiers = Tier.query.order_by(Tier.sort_order, Tier.rank).all()
    return jsonify([t.serialize() for t in tiers])


@tcc.route('/me', methods=['GET'])
@role_required()
def get_me():
    return jsonify(get_current_user().serialize_account())
