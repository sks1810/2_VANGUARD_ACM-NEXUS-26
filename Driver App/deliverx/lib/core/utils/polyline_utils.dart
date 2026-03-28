import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:google_maps_flutter/google_maps_flutter.dart';

class PolylineUtils {
  /// Replace with your Google Directions API key
  static const String apiKey = "AIzaSyAMqo3YmyQgyTfgbKBtzQYZ7demtSfyi7I";

  static Future<List<LatLng>> getPolylinePoints(
    LatLng origin,
    LatLng destination,
  ) async {
    final url =
        "https://maps.googleapis.com/maps/api/directions/json"
        "?origin=${origin.latitude},${origin.longitude}"
        "&destination=${destination.latitude},${destination.longitude}"
        "&mode=driving"
        "&key=$apiKey";

    final response = await http.get(Uri.parse(url));

    if (response.statusCode != 200) {
      return [];
    }

    final data = json.decode(response.body);

    if (data["routes"].isEmpty) {
      return [];
    }

    final points = data["routes"][0]["overview_polyline"]["points"];

    return _decodePolyline(points);
  }

  /// Decode encoded Google polyline
  static List<LatLng> _decodePolyline(String encoded) {
    List<LatLng> polylineCoordinates = [];

    int index = 0;
    int len = encoded.length;
    int lat = 0;
    int lng = 0;

    while (index < len) {
      int b;
      int shift = 0;
      int result = 0;

      do {
        b = encoded.codeUnitAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);

      int dlat = ((result & 1) != 0 ? ~(result >> 1) : (result >> 1));

      lat += dlat;

      shift = 0;
      result = 0;

      do {
        b = encoded.codeUnitAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);

      int dlng = ((result & 1) != 0 ? ~(result >> 1) : (result >> 1));

      lng += dlng;

      polylineCoordinates.add(LatLng(lat / 1E5, lng / 1E5));
    }

    return polylineCoordinates;
  }
}
