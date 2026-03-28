class OrderModel {
  final String orderId;
  final double latitude;
  final double longitude;
  final String customerName;
  final String address;
  final String phone;
  final String status;

  OrderModel({
    required this.orderId,
    required this.latitude,
    required this.longitude,
    required this.customerName,
    required this.address,
    required this.phone,
    required this.status,
  });

  factory OrderModel.fromMap(String orderId, Map<String, dynamic> map) {
    final location = map['location'];

    return OrderModel(
      orderId: orderId,
      latitude: location['lat'],
      longitude: location['lng'],
      customerName: map['customer_name'] ?? '',
      address: map['address'] ?? '',
      phone: map['phone'] ?? '',
      status: map['status'] ?? 'pending',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      "location": {"lat": latitude, "lng": longitude},
      "customer_name": customerName,
      "address": address,
      "phone": phone,
      "status": status,
    };
  }
}
