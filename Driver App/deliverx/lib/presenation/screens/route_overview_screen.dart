import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

import 'map_navigation_screen.dart';

class RouteOverviewScreen extends StatefulWidget {
  const RouteOverviewScreen({super.key});

  @override
  State<RouteOverviewScreen> createState() => _RouteOverviewScreenState();
}

class _RouteOverviewScreenState extends State<RouteOverviewScreen> {
  int totalStops = 0;

  @override
  void initState() {
    super.initState();
    loadRouteStats();
  }

  Future<void> loadRouteStats() async {
    final snapshot = await FirebaseFirestore.instance
        .collection("delivery_plans")
        .where("driver_id", isEqualTo: "driver_A")
        .limit(1)
        .get();

    if (snapshot.docs.isEmpty) return;

    final data = snapshot.docs.first.data();

    List orders = data["orders"];

    setState(() {
      totalStops = orders.length;
    });
  }

  @override
  Widget build(BuildContext context) {
    final completedStops = 0; // placeholder until tracking added
    final remainingStops = totalStops - completedStops;

    return Scaffold(
      appBar: AppBar(title: const Text("Route Overview")),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 20),

            _infoCard(title: "Total Deliveries", value: totalStops.toString()),

            const SizedBox(height: 16),

            _infoCard(title: "Completed", value: completedStops.toString()),

            const SizedBox(height: 16),

            _infoCard(title: "Remaining", value: remainingStops.toString()),

            const Spacer(),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const MapNavigationScreen(),
                    ),
                  );
                },
                child: const Text(
                  "Start Navigation",
                  style: TextStyle(fontSize: 18),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoCard({required String title, required String value}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(fontSize: 16)),
          Text(
            value,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
