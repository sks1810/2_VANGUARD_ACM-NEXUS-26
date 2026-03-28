import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/driver_assignment_model.dart';
import '../models/route_model.dart';
import '../models/order_model.dart';

class FirestoreDatasource {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Replace later with authenticated driver ID
  final String driverId = "driver_A";

  String _todayDocId() {
    return "driver_A_2026-03-28";
  }

  /// STEP 1: Load driver assignment
  Future<DriverAssignmentModel?> getDriverAssignment() async {
    try {
      final snapshot = await _firestore
          .collection("driver_assignments")
          .doc(_todayDocId())
          .get();

      if (!snapshot.exists) {
        return null;
      }

      return DriverAssignmentModel.fromMap(snapshot.data()!);
    } catch (e) {
      print("Assignment fetch error: $e");
      return null;
    }
  }

  /// STEP 2: Load route document
  Future<void> updateDeliveryProgress({
    required String driverId,
    required int currentOrderIndex,
    required List<String> completedOrders,
  }) async {
    try {
      final now = DateTime.now();

      final docId = "${driverId}_${now.year}_${now.month}_${now.day}";

      await _firestore.collection("driver_assignments").doc(docId).update({
        "current_order_index": currentOrderIndex,
        "completed_orders": completedOrders,
        "last_updated_at": FieldValue.serverTimestamp(),
      });
    } catch (e) {
      print("Progress update error: $e");
    }
  }

  Future<RouteModel?> getRoute(String routeId) async {
    try {
      final snapshot = await _firestore.collection("routes").doc(routeId).get();

      if (!snapshot.exists) {
        return null;
      }

      return RouteModel.fromMap(routeId, snapshot.data()!);
    } catch (e) {
      print("Route fetch error: $e");
      return null;
    }
  }

  /// STEP 3: Load checkpoint orders in sequence
  Future<List<OrderModel>> getOrders(List<String> orderIds) async {
    try {
      final List<OrderModel> orders = [];

      for (final id in orderIds) {
        final snapshot = await _firestore.collection("orders").doc(id).get();

        if (snapshot.exists) {
          orders.add(OrderModel.fromMap(id, snapshot.data()!));
        }
      }

      return orders;
    } catch (e) {
      print("Orders fetch error: $e");
      return [];
    }
  }
}
