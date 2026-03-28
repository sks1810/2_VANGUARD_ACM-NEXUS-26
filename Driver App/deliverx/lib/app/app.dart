import 'package:deliverx/presenation/screens/splash_screen.dart';
import 'package:flutter/material.dart';

class DeliverXApp extends StatelessWidget {
  const DeliverXApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'DeliverX Driver',

      theme: ThemeData(primarySwatch: Colors.blue, useMaterial3: true),

      home: const SplashScreen(),
    );
  }
}
