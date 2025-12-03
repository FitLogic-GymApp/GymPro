import 'package:flutter/foundation.dart';
import '../services/turnstile_service.dart';

enum TurnstileState { idle, scanning, success, error }

class TurnstileProvider extends ChangeNotifier {
  final TurnstileService _turnstileService = TurnstileService();

  TurnstileState _state = TurnstileState.idle;
  String? _message;
  bool _isInsideGym = false;

  TurnstileState get state => _state;
  String? get message => _message;
  bool get isInsideGym => _isInsideGym;

  /// QR tarama simülasyonu başlat
  void startScanning() {
    _state = TurnstileState.scanning;
    _message = null;
    notifyListeners();
  }

  /// Salona giriş yap
  Future<bool> checkIn() async {
    _state = TurnstileState.scanning;
    notifyListeners();

    try {
      final result = await _turnstileService.checkIn();
      _state = result.success ? TurnstileState.success : TurnstileState.error;
      _message = result.message;
      _isInsideGym = result.success;
      notifyListeners();
      return result.success;
    } catch (e) {
      _state = TurnstileState.error;
      _message = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Salondan çıkış yap
  Future<bool> checkOut() async {
    _state = TurnstileState.scanning;
    notifyListeners();

    try {
      final result = await _turnstileService.checkOut();
      _state = result.success ? TurnstileState.success : TurnstileState.error;
      _message = result.message;
      if (result.success) {
        _isInsideGym = false;
      }
      notifyListeners();
      return result.success;
    } catch (e) {
      _state = TurnstileState.error;
      _message = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// State'i sıfırla
  void reset() {
    _state = TurnstileState.idle;
    _message = null;
    notifyListeners();
  }

  /// Çıkış yapıldığında state'i güncelle
  void setOutsideGym() {
    _isInsideGym = false;
    notifyListeners();
  }
}
