class Exercise {
  final int exerciseId;
  final String name;
  final String muscleGroup;

  Exercise({
    required this.exerciseId,
    required this.name,
    required this.muscleGroup,
  });

  factory Exercise.fromJson(Map<String, dynamic> json) {
    return Exercise(
      exerciseId: json['exercise_id'] ?? 0,
      name: json['name'] ?? '',
      muscleGroup: json['muscle_group'] ?? '',
    );
  }
}

class WorkoutExercise {
  final String exerciseName;
  final String? muscleGroup;
  final int sets;
  final int reps;
  final int restSec;
  final int orderNo;

  WorkoutExercise({
    required this.exerciseName,
    this.muscleGroup,
    required this.sets,
    required this.reps,
    required this.restSec,
    required this.orderNo,
  });

  factory WorkoutExercise.fromJson(Map<String, dynamic> json) {
    return WorkoutExercise(
      exerciseName: json['exercise_name'] ?? json['name'] ?? '',
      muscleGroup: json['muscle_group'],
      sets: json['sets'] ?? 0,
      reps: json['reps'] ?? 0,
      restSec: json['rest_sec'] ?? 0,
      orderNo: json['order_no'] ?? 0,
    );
  }
}

class FixedWorkout {
  final int fixedId;
  final String title;
  final int durationMin;
  final List<WorkoutExercise>? exercises;

  FixedWorkout({
    required this.fixedId,
    required this.title,
    required this.durationMin,
    this.exercises,
  });

  factory FixedWorkout.fromJson(Map<String, dynamic> json) {
    return FixedWorkout(
      fixedId: json['fixed_id'] ?? 0,
      title: json['title'] ?? '',
      durationMin: json['duration_min'] ?? 0,
      exercises: json['exercises'] != null
          ? (json['exercises'] as List)
              .map((e) => WorkoutExercise.fromJson(e))
              .toList()
          : null,
    );
  }
}

class CustomRoutine {
  final int routineId;
  final String title;
  final DateTime? createdAt;
  final List<WorkoutExercise>? exercises;

  CustomRoutine({
    required this.routineId,
    required this.title,
    this.createdAt,
    this.exercises,
  });

  factory CustomRoutine.fromJson(Map<String, dynamic> json) {
    return CustomRoutine(
      routineId: json['routine_id'] ?? 0,
      title: json['title'] ?? '',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
      exercises: json['exercises'] != null
          ? (json['exercises'] as List)
              .map((e) => WorkoutExercise.fromJson(e))
              .toList()
          : null,
    );
  }
}
