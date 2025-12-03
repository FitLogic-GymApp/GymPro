import 'package:flutter/foundation.dart';
import '../services/auth_service.dart';

enum AuthState { initial, loading, authenticated, unauthenticated, error }

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();

  AuthState _state = AuthState.initial;
  String? _error;
  List<Gym> _gyms = [];

  AuthState get state => _state;
  String? get error => _error;
  User? get user => _authService.currentUser;
  Gym? get selectedGym => _authService.selectedGym;
  List<Gym> get gyms => _gyms;
  bool get isLoggedIn => _authService.isLoggedIn;
  bool get hasSelectedGym => _authService.hasSelectedGym;

  /// Uygulama başlangıcında session kontrol
  Future<void> checkSession() async {
    _state = AuthState.loading;
    notifyListeners();

    try {
      final hasSession = await _authService.checkSession();
      if (hasSession) {
        _state = AuthState.authenticated;
        // Gym listesini de yükle
        await fetchMyGyms();
      } else {
        _state = AuthState.unauthenticated;
      }
    } catch (e) {
      _state = AuthState.unauthenticated;
      _error = e.toString();
    }
    notifyListeners();
  }

  /// Giriş yap
  Future<bool> login(String email, String password) async {
    _state = AuthState.loading;
    _error = null;
    notifyListeners();

    try {
      await _authService.login(email, password);
      _state = AuthState.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      _state = AuthState.error;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Kayıt ol
  Future<bool> register(String name, String email, String password) async {
    _state = AuthState.loading;
    _error = null;
    notifyListeners();

    try {
      await _authService.register(name, email, password);
      _state = AuthState.unauthenticated;
      notifyListeners();
      return true;
    } catch (e) {
      _state = AuthState.error;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Üye olunan salonları getir
  Future<void> fetchMyGyms() async {
    try {
      _gyms = await _authService.getMyGyms();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
    }
  }

  /// Salon seç
  Future<void> selectGym(Gym gym) async {
    await _authService.selectGym(gym);
    notifyListeners();
  }

  /// Seçili salonu temizle (çıkış yaparken)
  void clearSelectedGym() {
    _authService.clearSelectedGym();
    notifyListeners();
  }

  /// Çıkış yap
  Future<void> logout() async {
    await _authService.logout();
    _state = AuthState.unauthenticated;
    _gyms = [];
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
