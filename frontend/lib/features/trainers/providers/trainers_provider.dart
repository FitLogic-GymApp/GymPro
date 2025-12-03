import 'package:flutter/foundation.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/auth_service.dart';
import '../models/trainer_model.dart';

class TrainersProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final AuthService _authService = AuthService();

  List<Trainer> _trainers = [];
  bool _isLoading = false;
  String? _error;

  List<Trainer> get trainers => _trainers;
  List<Trainer> get trainersInGym => _trainers.where((t) => t.isInGym).toList();
  bool get isLoading => _isLoading;
  String? get error => _error;

  int? get _gymId => _authService.selectedGym?.gymId;

  Future<void> fetchTrainers() async {
    if (_gymId == null) {
      _error = 'Salon bilgisi bulunamadı';
      notifyListeners();
      return;
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // gym_id parametresi ile antrenörleri getir
      final response = await _api.get('/trainers', queryParams: {
        'gym_id': _gymId,
      });
      _trainers = (response as List).map((e) => Trainer.fromJson(e)).toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearData() {
    _trainers = [];
    _error = null;
    notifyListeners();
  }
}
