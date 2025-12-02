import 'package:flutter/material.dart';

class AppColors {
  static const Color primary = Color(0xFF6C5CE7);
  static const Color primaryDark = Color(0xFF5B4CD4);
  static const Color secondary = Color(0xFF00CEC9);
  static const Color accent = Color(0xFFFF7675);
  
  static const Color background = Color(0xFF0D0D0D);
  static const Color surface = Color(0xFF1A1A1A);
  static const Color surfaceLight = Color(0xFF2D2D2D);
  
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFFB0B0B0);
  static const Color textHint = Color(0xFF6B6B6B);
  
  static const Color success = Color(0xFF00B894);
  static const Color warning = Color(0xFFFDAB3D);
  static const Color error = Color(0xFFE74C3C);
  
  static const Color cardGradientStart = Color(0xFF2D2D2D);
  static const Color cardGradientEnd = Color(0xFF1A1A1A);
  
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primary, Color(0xFF8B7CF7)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient cardGradient = LinearGradient(
    colors: [cardGradientStart, cardGradientEnd],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}
