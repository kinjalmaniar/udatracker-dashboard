from flask import Flask, request, jsonify, send_from_directory
from backend.order_tracker import OrderTracker, OrderNotFoundError
from backend.in_memory_storage import InMemoryStorage

app = Flask(__name__, static_folder='../frontend')
in_memory_storage = InMemoryStorage()
order_tracker = OrderTracker(in_memory_storage)


@app.errorhandler(OrderNotFoundError)
def handle_not_found(error):
    return jsonify({"error": str(error)}), 404


@app.errorhandler(ValueError)
def handle_validation_error(error):
    return jsonify({"error": str(error)}), 400


def get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/api/orders', methods=['POST'])
def add_order_api():
    data = get_json_body()
    order = order_tracker.add_order(
        data.get("order_id"),
        data.get("item_name"),
        data.get("quantity"),
        data.get("customer_id"),
        data.get("status", "pending"),
    )
    return jsonify(order), 201


@app.route('/api/orders/<string:order_id>', methods=['GET'])
def get_order_api(order_id):
    order = order_tracker.get_order_by_id(order_id)
    if not order:
        raise OrderNotFoundError(f"Order with ID '{order_id}' not found.")
    return jsonify(order), 200


@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status_api(order_id):
    data = get_json_body()
    order = order_tracker.update_order_status(order_id, data.get("new_status"))
    return jsonify(order), 200


@app.route('/api/orders/<string:order_id>', methods=['DELETE'])
def delete_order_api(order_id):
    order_tracker.delete_order(order_id)
    return '', 204


@app.route('/api/orders', methods=['GET'])
def list_orders_api():
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")

    if customer_id:
        orders = order_tracker.list_orders_by_customer(customer_id, status)
    elif status:
        orders = order_tracker.list_orders_by_status(status)
    else:
        orders = order_tracker.list_all_orders()
    return jsonify(orders), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
