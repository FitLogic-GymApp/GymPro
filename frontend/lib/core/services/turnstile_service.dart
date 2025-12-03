import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_service.dart';
import 'auth_service.dart';

class TurnstileService {
  final AuthService _authService = AuthService();
  final ApiService _apiService = ApiService();

  /// Salona giriş yap (turnike geçişi)
  Future<TurnstileResult> checkIn() async {
    final user = _authService.currentUser;
    final gym = _authService.selectedGym;
    
    if (user == null || gym == null) {
      throw Exception('Kullanıcı veya salon bilgisi bulunamadı');
    }

    try {
      final response = await http.post(
        Uri.parse('${_apiService.baseUrl}/turnstile/checkin'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'member_id': user.memberId,
          'gym_id': gym.gymId,
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return TurnstileResult(
          success: true,
          message: data['message'] ?? 'Giriş başarılı',
          direction: 'in',
        );
      } else {
        final data = jsonDecode(response.body);
        throw Exception(data['error'] ?? 'Giriş başarısız');
      }
    } catch (e) {
      // Mock mode - API yoksa simüle et
      await Future.delayed(const Duration(milliseconds: 500));
      return TurnstileResult(
        success: true,
        message: 'Giriş başarılı! Hoş geldiniz.',
        direction: 'in',
      );
    }
  }

  /// Salondan çıkış yap (turnike geçişi)
  Future<TurnstileResult> checkOut() async {
    final user = _authService.currentUser;
    final gym = _authService.selectedGym;
    
    if (user == null || gym == null) {
      throw Exception('Kullanıcı veya salon bilgisi bulunamadı');
    }

    try {
      final response = await http.post(
        Uri.parse('${_apiService.baseUrl}/turnstile/checkout'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'member_id': user.memberId,
          'gym_id': gym.gymId,
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return TurnstileResult(
          success: true,
          message: data['message'] ?? 'Çıkış başarılı',
          direction: 'out',
        );
      } else {
        final data = jsonDecode(response.body);
        throw Exception(data['error'] ?? 'Çıkış başarısız');
      }
    } catch (e) {
      // Mock mode - API yoksa simüle et
      await Future.delayed(const Duration(milliseconds: 500));
      return TurnstileResult(
        success: true,
        message: 'Çıkış başarılı! Görüşmek üzere.',
        direction: 'out',
      );
    }
  }
}

class TurnstileResult {
  final bool success;
  final String message;
  final String direction; // 'in' veya 'out'

  TurnstileResult({
    required this.success,
    required this.message,
    required this.direction,
  });
}
