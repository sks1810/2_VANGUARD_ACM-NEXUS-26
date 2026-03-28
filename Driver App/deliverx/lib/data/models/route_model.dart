class RouteModel {
  final String routeId;
  final List<String> orderSequence;

  RouteModel({required this.routeId, required this.orderSequence});

  factory RouteModel.fromMap(String routeId, Map<String, dynamic> map) {
    return RouteModel(
      routeId: routeId,
      orderSequence: List<String>.from(map['order_sequence'] ?? []),
    );
  }

  Map<String, dynamic> toMap() {
    return {'order_sequence': orderSequence};
  }
}
