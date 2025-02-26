from flask import Blueprint, request, jsonify
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime

# Import your db models as needed
# from api.models import db, User, Order, Payment

paypal_api = Blueprint('paypal_api', __name__)
CORS(paypal_api)

# PayPal API Configuration
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"  # Use "https://api-m.paypal.com" for production

# Helper function to get PayPal access token
def get_paypal_access_token():
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = "grant_type=client_credentials"
    response = requests.post(
        url, 
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get PayPal access token: {response.text}")

# Create Order
def create_order(cart):
    access_token = get_paypal_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
    
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": "100"  # In real app, calculate from cart
                }
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        return {
            "jsonResponse": response.json(),
            "httpStatusCode": response.status_code
        }
    else:
        raise Exception(f"Failed to create order: {response.text}")

@paypal_api.route("/orders", methods=["POST"])
def create_paypal_order():
    try:
        cart = request.json.get("cart", {})
        result = create_order(cart)
        return jsonify(result["jsonResponse"]), result["httpStatusCode"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Capture Order
def capture_order(order_id):
    access_token = get_paypal_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code in [200, 201]:
        return {
            "jsonResponse": response.json(),
            "httpStatusCode": response.status_code
        }
    else:
        raise Exception(f"Failed to capture order: {response.text}")

@paypal_api.route("/orders/<order_id>/capture", methods=["POST"])
def capture_paypal_order(order_id):
    try:
        result = capture_order(order_id)
        
        # Here you would typically update your database
        # For example:
        # order = Order.query.filter_by(paypal_order_id=order_id).first()
        # if order:
        #     order.status = "COMPLETED"
        #     order.completed_at = datetime.now()
        #     db.session.commit()
        
        return jsonify(result["jsonResponse"]), result["httpStatusCode"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Order Details (additional utility route)
@paypal_api.route("/orders/<order_id>", methods=["GET"])
def get_order_details(order_id):
    try:
        access_token = get_paypal_access_token()
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": f"Failed to get order details: {response.text}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500