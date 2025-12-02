import 'package:flutter/foundation.dart';
import '../../../core/services/api_service.dart';
import '../../../core/constants/app_constants.dart';
import '../models/workout_models.dart';

class WorkoutsProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<FixedWorkout> _fixedWorkouts = [];
  List<CustomRoutine> _myRoutines = [];
  List<Exercise> _exercises = [];
  List<String> _muscleGroups = [];
  
  FixedWorkout? _selectedFixedWorkout;
  CustomRoutine? _selectedRoutine;
  
  bool _isLoading = false;
  String? _error;

  List<FixedWorkout> get fixedWorkouts => _fixedWorkouts;
  List<CustomRoutine> get myRoutines => _myRoutines;
  List<Exercise> get exercises => _exercises;
  List<String> get muscleGroups => _muscleGroups;
  FixedWorkout? get selectedFixedWorkout => _selectedFixedWorkout;
  CustomRoutine? get selectedRoutine => _selectedRoutine;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchFixedWorkouts() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get('/fixed-workouts');
      _fixedWorkouts = (response as List)
          .map((e) => FixedWorkout.fromJson(e))
          .toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchFixedWorkoutDetail(int fixedId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get('/fixed-workouts/$fixedId');
      _selectedFixedWorkout = FixedWorkout.fromJson(response);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchMyRoutines({int? memberId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get('/my-routines', queryParams: {
        'member_id': memberId ?? AppConstants.defaultMemberId,
      });
      _myRoutines = (response as List)
          .map((e) => CustomRoutine.fromJson(e))
          .toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchRoutineDetail(int routineId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _api.get('/my-routines/$routineId');
      _selectedRoutine = CustomRoutine.fromJson(response);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> createRoutine(String title, {int? memberId}) async {
    try {
      await _api.post('/my-routines', body: {
        'member_id': memberId ?? AppConstants.defaultMemberId,
        'title': title,
      });
      await fetchMyRoutines(memberId: memberId);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> updateRoutine(int routineId, String title) async {
    try {
      await _api.put('/my-routines/$routineId', body: {'title': title});
      await fetchMyRoutines();
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> deleteRoutine(int routineId) async {
    try {
      await _api.delete('/my-routines/$routineId');
      _myRoutines.removeWhere((r) => r.routineId == routineId);
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> fetchExercises({String? muscleGroup}) async {
    try {
      final queryParams = muscleGroup != null 
          ? {'muscle_group': muscleGroup} 
          : null;
      final response = await _api.get('/exercises', queryParams: queryParams);
      _exercises = (response as List)
          .map((e) => Exercise.fromJson(e))
          .toList();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> fetchMuscleGroups() async {
    try {
      final response = await _api.get('/muscle-groups');
      _muscleGroups = List<String>.from(response);
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<bool> addExerciseToRoutine({
    required int routineId,
    required int exerciseId,
    int sets = 3,
    int reps = 10,
    int restSec = 60,
    int orderNo = 1,
  }) async {
    try {
      await _api.post('/my-routines/$routineId/add-exercise', body: {
        'exercise_id': exerciseId,
        'sets': sets,
        'reps': reps,
        'rest_sec': restSec,
        'order_no': orderNo,
      });
      await fetchRoutineDetail(routineId);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> removeExerciseFromRoutine(int routineId, int exerciseId) async {
    try {
      await _api.delete('/my-routines/$routineId/remove-exercise/$exerciseId');
      await fetchRoutineDetail(routineId);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  void clearSelectedWorkout() {
    _selectedFixedWorkout = null;
    _selectedRoutine = null;
    notifyListeners();
  }
}
