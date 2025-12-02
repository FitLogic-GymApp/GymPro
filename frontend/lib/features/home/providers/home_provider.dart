import 'package:flutter/foundation.dart';
import '../../../core/services/api_service.dart';
import '../../../core/constants/app_constants.dart';
import '../models/home_models.dart';

class HomeProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  HomeData? _homeData;
  bool _isLoading = false;
  String? _error;

  HomeData? get homeData => _homeData;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasData => _homeData != null;

  Future<void> fetchHomeData({int? memberId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get('/home', queryParams: {
        'member_id': memberId ?? AppConstants.defaultMemberId,
      });
      _homeData = HomeData.fromJson(response);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refresh({int? memberId}) async {
    await fetchHomeData(memberId: memberId);
  }
}
