from django.shortcuts import render
from django.http import JsonResponse
from .models import users_collection, products_collection, orders_collection
import json
import bcrypt
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from bson.objectid import ObjectId
import razorpay
from datetime import datetime

# Create a Razorpay client
razorpay_client = razorpay.Client(auth  = ("rzp_test_JDumAGUYVqtCC3", "ZQuFauPLpSKQKZbXhzFTRIKo"))   # Replace with your actual Razorpay key and secret

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"csrfToken": request.META.get("CSRF_COOKIE", "")})

@csrf_exempt
def add_product(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            product = products_collection.insert_one(
                {
                    "name": data["name"],
                    "price": data["price"],
                    "description": data["description"],
                    "category": data["category"],
                    "stock": data["stock"]
                }
            )
            return JsonResponse({"message": "Product added successfully"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def place_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order = orders_collection.insert_one(
                {
                    "firstName": data["firstName"],
                    "lastName": data["lastName"],
                    "address": data["address"],
                    "city": data["city"],
                    "state": data["state"],
                    "zip": data["zip"],
                    "price": data["price"],
                    "productIdQuantityArray": data["productIdQuantityArray"],
                    "paymentStatus": "not paid"
                }
            )

            return JsonResponse({"message": "Order placed successfully", "orderId": str(order.inserted_id)}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            # Fetch the user from the database
            user = users_collection.find_one({"email": email})
            if user and bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                return JsonResponse({"message": "Login successful"}, status=200)
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            hashed_password = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
            user = users_collection.insert_one(
                {
                    "email": data["email"],
                    "username": data["username"],
                    "password": hashed_password.decode('utf-8'),
                    "role": data.get("role", "user"),  # Default role as 'user'
                    "created_at": data.get("created_at", datetime.now().isoformat()),  # Timestamp of signup
                }
            )
            return JsonResponse({"message": "User registered successfully"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_order(request, order_id):
    try:
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if order:
            order["_id"] = str(order["_id"])
            return JsonResponse(order, safe=False)
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def get_admin_orders(request):
    try:
        orders = list(orders_collection.find())
        for order in orders:
            order["_id"] = str(order["_id"])
        return JsonResponse(orders, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def update_order(request, order_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            orders_collection.update_one({"_id": ObjectId(order_id)}, {"$set": data})
            return JsonResponse({"message": "Order updated successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def add_order_to_user(request, user_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data["orderId"]
            users_collection.update_one({"_id": ObjectId(user_id)}, {"$push": {"orders": order_id}})
            return JsonResponse({"message": "Order added to user successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def update_stock(request, product_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            quantity = data["quantity"]
            products_collection.update_one({"_id": ObjectId(product_id)}, {"$inc": {"stock": quantity}})
            return JsonResponse({"message": "Stock updated successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def create_razorpay_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Perform the necessary logic to create a Razorpay order
            # Replace this with your actual logic to create the order
            # Example:
            order_amount = data.get("amount")
            order_currency = data.get("currency", "INR")
            
            # Example of creating a Razorpay order (adjust as per your integration)
            razorpay_order = razorpay_client.order.create({
                'amount': order_amount,
                'currency': order_currency,
                'payment_capture': 1  # Auto-capture payment
            })
            
            # Extract the order ID from Razorpay response
            order_id = razorpay_order['id']
            
            # Return the order details with the generated order ID
            return JsonResponse({
                "amount": order_amount,
                "id": order_id,
                "currency": order_currency,
                "message": "Order created successfully"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def get_all_products(request):
    try:
        products = list(products_collection.find())
        for product in products:
            product['_id'] = str(product['_id'])  # Convert ObjectId to string
        return JsonResponse(products, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def update_product(request, product_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            product = products_collection.find_one({'_id': ObjectId(product_id)})

            if not product:
                return JsonResponse({'error': 'Product not found'}, status=404)

            update_data = {
                'name': data.get('name', product['name']),
                'price': data.get('price', product['price']),
                'stock': data.get('stock', product['stock']),
                'category': data.get('category', product['category']),
                'description': data.get('description', product['description']),
            }
            products_collection.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )
            return JsonResponse({'message': 'Product updated successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def delete_product(request, product_id):
    if request.method == "DELETE":
        try:
            product = products_collection.find_one({'_id': ObjectId(product_id)})

            if not product:
                return JsonResponse({'error': 'Product not found'}, status=404)

            products_collection.delete_one({'_id': ObjectId(product_id)})
            return JsonResponse({'message': 'Product deleted successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)