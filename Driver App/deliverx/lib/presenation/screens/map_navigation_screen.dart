import 'dart:async';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/services/location_service.dart';
import '../../core/utils/polyline_utils.dart';

class MapNavigationScreen extends ConsumerStatefulWidget {
  const MapNavigationScreen({super.key});

  @override
  ConsumerState<MapNavigationScreen> createState() =>
      _MapNavigationScreenState();
}

class _MapNavigationScreenState extends ConsumerState<MapNavigationScreen> {
  GoogleMapController? mapController;
  double distanceToCheckpoint = 0; // meters
  double totalRemainingDistance = 0; // meters
  int remainingStops = 0;
  final LocationService locationService = LocationService();

  Set<Marker> markers = {};

  Set<Polyline> polylines = {};

  LatLng? driverLocation;

  int currentCheckpointIndex = 0;

  bool arrivalDetected = false;

  List<LatLng> stops = [];

  @override
  void initState() {
    super.initState();

    _initializeNavigation();

    loadStopsFromFirestore();
  }

  Future<void> loadStopsFromFirestore() async {
    final snapshot = await FirebaseFirestore.instance
        .collection("delivery_plans")
        .where("driver_id", isEqualTo: "driver_A")
        .limit(1)
        .get();

    if (snapshot.docs.isEmpty) {
      print("No delivery plan found");
      return;
    }

    final data = snapshot.docs.first.data();

    final List orders = data["orders"];

    if (orders.isEmpty) {
      print("Orders array empty");
      return;
    }

    /// Sort stops in delivery order
    orders.sort((a, b) => a["delivery_order"].compareTo(b["delivery_order"]));

    stops = orders.map<LatLng>((o) => LatLng(o["lat"], o["lng"])).toList();

    print("Loaded ${stops.length} stops from Firestore");

    _loadMarkers();
  }

  Future<void> _initializeNavigation() async {
    final granted = await locationService.requestPermission();

    if (!granted) return;

    await locationService.getCurrentLocation();

    locationService.startLocationUpdates(_onLocationUpdate);
  }

  void _loadMarkers() {
    if (stops.isEmpty) return;

    Set<Marker> routeMarkers = {};

    for (int i = 0; i < stops.length; i++) {
      routeMarkers.add(
        Marker(
          markerId: MarkerId("stop_$i"),
          position: stops[i],
          icon: BitmapDescriptor.defaultMarkerWithHue(
            i == currentCheckpointIndex
                ? BitmapDescriptor.hueGreen
                : BitmapDescriptor.hueBlue,
          ),
          infoWindow: InfoWindow(title: "Stop ${i + 1}"),
        ),
      );
    }

    setState(() {
      markers = routeMarkers;
    });
  }

  Future<void> _drawRoutePolyline({LatLng? driver}) async {
    if (stops.isEmpty) return;

    List<LatLng> fullRoute = [];

    /// Segment 1: driver → first checkpoint (optional)
    if (driver != null) {
      final firstSegment = await PolylineUtils.getPolylinePoints(
        driver,
        stops[currentCheckpointIndex],
      );

      if (firstSegment.isNotEmpty) {
        fullRoute.addAll(firstSegment);
      }
    }

    /// Remaining checkpoint segments
    for (int i = currentCheckpointIndex; i < stops.length - 1; i++) {
      final segment = await PolylineUtils.getPolylinePoints(
        stops[i],
        stops[i + 1],
      );

      if (segment.isNotEmpty) {
        fullRoute.addAll(segment);
      }
    }

    if (fullRoute.isEmpty) return;

    setState(() {
      polylines.clear();

      polylines.add(
        Polyline(
          polylineId: const PolylineId("delivery_route"),
          points: fullRoute,
          width: 6,
          color: Colors.blue,
        ),
      );
    });
  }

  DateTime? lastRouteUpdate;
  void _onLocationUpdate(Position position) async {
    /// Do nothing until Firestore stops load
    if (stops.isEmpty) return;

    final newLocation = LatLng(position.latitude, position.longitude);

    setState(() {
      driverLocation = newLocation;
    });

    mapController?.animateCamera(CameraUpdate.newLatLng(newLocation));

    /// Prevent excessive Directions API calls
    if (lastRouteUpdate != null &&
        DateTime.now().difference(lastRouteUpdate!).inSeconds < 5) {
      return;
    }

    lastRouteUpdate = DateTime.now();

    /// Draw full navigation route:
    /// driver → stop1 → stop2 → stop3 → ...
    await _drawRoutePolyline(driver: newLocation);

    /// Arrival detection
    final distance = locationService.calculateDistance(
      position.latitude,
      position.longitude,
      stops[currentCheckpointIndex].latitude,
      stops[currentCheckpointIndex].longitude,
    );

    distanceToCheckpoint = distance;

    /// Remaining stops
    remainingStops = stops.length - currentCheckpointIndex - 1;

    /// Estimate total remaining distance
    double total = distance;

    for (int i = currentCheckpointIndex; i < stops.length - 1; i++) {
      total += locationService.calculateDistance(
        stops[i].latitude,
        stops[i].longitude,
        stops[i + 1].latitude,
        stops[i + 1].longitude,
      );
    }

    totalRemainingDistance = total;

    if (distance < 20 && !arrivalDetected) {
      arrivalDetected = true;
      _showArrivalDialog();
    }
  }

  void _showArrivalDialog() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Checkpoint reached"),
        content: const Text("You arrived at delivery location."),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
            },
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  void _completeDelivery() {
    if (currentCheckpointIndex < stops.length - 1) {
      setState(() {
        currentCheckpointIndex++;
        arrivalDetected = false;
      });
    } else {
      _showRouteCompletedDialog();
    }
  }

  void _showRouteCompletedDialog() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Route Completed"),
        content: const Text("All deliveries finished."),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    locationService.stopLocationUpdates();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final checkpoint = stops[currentCheckpointIndex];

    return Scaffold(
      appBar: AppBar(title: const Text("Navigation")),
      body: Column(
        children: [
          Expanded(
            flex: 3,
            child: GoogleMap(
              initialCameraPosition: CameraPosition(
                target: checkpoint,
                zoom: 14,
              ),

              markers: {
                ...markers,
                if (driverLocation != null)
                  Marker(
                    markerId: const MarkerId("driver"),
                    position: driverLocation!,
                    icon: BitmapDescriptor.defaultMarkerWithHue(
                      BitmapDescriptor.hueYellow,
                    ),
                  ),
              },

              polylines: polylines,

              onMapCreated: (GoogleMapController controller) {
                mapController = controller;
              },
            ),
          ),

          Expanded(
            flex: 2,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Navigation Details",
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),

                  const SizedBox(height: 12),

                  /// Current checkpoint
                  Text(
                    "Current Stop: ${currentCheckpointIndex + 1}",
                    style: const TextStyle(fontSize: 16),
                  ),

                  const SizedBox(height: 8),

                  /// Distance to next stop
                  Text(
                    "Distance to next stop: "
                    "${(distanceToCheckpoint / 1000).toStringAsFixed(2)} km",
                  ),

                  const SizedBox(height: 8),

                  /// Remaining stops
                  Text("Remaining stops: $remainingStops"),

                  const SizedBox(height: 8),

                  /// Total journey remaining
                  Text(
                    "Total remaining distance: "
                    "${(totalRemainingDistance / 1000).toStringAsFixed(2)} km",
                  ),

                  const Spacer(),

                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: arrivalDetected ? _completeDelivery : null,
                      child: const Text("Mark Delivered"),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
