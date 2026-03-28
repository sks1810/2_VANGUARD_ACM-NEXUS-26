import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/datasources/firestore_datasource.dart';
import '../../data/models/driver_assignment_model.dart';
import '../../data/models/route_model.dart';
import '../../data/models/order_model.dart';

final navigationControllerProvider = Provider<NavigationController>((ref) {
  final datasource = FirestoreDatasource();

  return NavigationController(datasource);
});

class NavigationController {
  final FirestoreDatasource datasource;
  List<String> completedOrders = [];

  NavigationController(this.datasource);

  DriverAssignmentModel? assignment;
  RouteModel? route;
  List<OrderModel> orders = [];

  String? routeId;
  int currentOrderIndex = 0;

  /// STEP 1: Load assignment
  Future<bool> loadAssignment() async {
    assignment = await datasource.getDriverAssignment();

    if (assignment == null) {
      return false;
    }

    if (assignment!.status != "route_ready") {
      return false;
    }

    routeId = assignment!.routeId;
    currentOrderIndex = assignment!.currentOrderIndex;
    completedOrders = assignment!.completedOrders;

    return true;
  }

  /// STEP 2: Load route sequence
  Future<bool> loadRoute() async {
    if (routeId == null) {
      return false;
    }

    route = await datasource.getRoute(routeId!);

    if (route == null) {
      return false;
    }

    return true;
  }

  /// STEP 3: Load checkpoint orders
  Future<bool> loadOrders() async {
    if (route == null) {
      return false;
    }

    orders = await datasource.getOrders(route!.orderSequence);

    if (orders.isEmpty) {
      return false;
    }

    return true;
  }

  /// STEP 4: Full initialization pipeline
  Future<bool> initializeNavigationSession() async {
    final assignmentLoaded = await loadAssignment();

    if (!assignmentLoaded) {
      return false;
    }

    final routeLoaded = await loadRoute();

    if (!routeLoaded) {
      return false;
    }

    final ordersLoaded = await loadOrders();

    if (!ordersLoaded) {
      return false;
    }

    return true;
  }

  /// Current checkpoint order
  OrderModel? get currentOrder {
    if (orders.isEmpty) {
      return null;
    }

    if (currentOrderIndex >= orders.length) {
      return null;
    }

    return orders[currentOrderIndex];
  }

  /// Move to next checkpoint
  Future<void> moveToNextCheckpoint() async {
    if (orders.isEmpty) return;

    final completedOrderId = orders[currentOrderIndex].orderId;

    completedOrders.add(completedOrderId);

    currentOrderIndex++;

    await datasource.updateDeliveryProgress(
      driverId: assignment!.driverId,
      currentOrderIndex: currentOrderIndex,
      completedOrders: completedOrders,
    );
  }

  /// Check if route completed
  bool get isRouteCompleted {
    return currentOrderIndex >= orders.length;
  }
}
