class DriverAssignmentModel {
  final String routeId;
  final String driverId;
  final String status;
  final int currentOrderIndex;
  final List<String> completedOrders;

  DriverAssignmentModel({
    required this.routeId,
    required this.driverId,
    required this.status,
    required this.currentOrderIndex,
    required this.completedOrders,
  });

  factory DriverAssignmentModel.fromMap(Map<String, dynamic> map) {
    return DriverAssignmentModel(
      routeId: map['route_id'],
      driverId: map['driver_id'],
      status: map['status'],
      currentOrderIndex: map['current_order_index'] ?? 0,
      completedOrders: List<String>.from(map['completed_orders'] ?? []),
    );
  }
}
