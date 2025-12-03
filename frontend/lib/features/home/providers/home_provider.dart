import 'package:flutter/foundation.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/auth_service.dart';
import '../models/home_models.dart';

class HomeProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final AuthService _authService = AuthService();

  HomeData? _homeData;
  bool _isLoading = false;
  String? _error;

  HomeData? get homeData => _homeData;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasData => _homeData != null;

  /// Seçili salon ve üye bilgilerini alır
  int? get _gymId => _authService.selectedGym?.gymId;
  int? get _memberId => _authService.currentUser?.memberId;

  Future<void> fetchHomeData() async {
    if (_gymId == null || _memberId == null) {
      _error = 'Salon veya kullanıcı bilgisi bulunamadı';
      notifyListeners();
      return;
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Yeni SaaS endpoint: /api/gym/<gym_id>/dashboard
      final response = await _api.get('/gym/$_gymId/dashboard', queryParams: {
        'member_id': _memberId,
      });
      _homeData = HomeData.fromJson(response);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refresh() async {
    await fetchHomeData();
  }

  void clearData() {
    _homeData = null;
    _error = null;
    notifyListeners();
  }
}
