import 'package:flutter/foundation.dart';
import '../../../core/services/api_service.dart';
import '../models/trainer_model.dart';

class TrainersProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<Trainer> _trainers = [];
  bool _isLoading = false;
  String? _error;

  List<Trainer> get trainers => _trainers;
  List<Trainer> get trainersInGym => _trainers.where((t) => t.isInGym).toList();
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchTrainers() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get('/trainers');
      _trainers = (response as List).map((e) => Trainer.fromJson(e)).toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
