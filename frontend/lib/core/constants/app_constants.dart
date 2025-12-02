class AppConstants {
  static const String appName = 'GymBro';
  static const String apiBaseUrl = 'http://10.0.2.2:5000/api'; // Android emulator
  static const String apiBaseUrlIOS = 'http://localhost:5000/api';
  static const String apiBaseUrlWeb = 'http://127.0.0.1:5000/api';
  
  static const int defaultMemberId = 1;
  
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration cacheExpiry = Duration(minutes: 5);
}

class AppStrings {
  static const String home = 'Home';
  static const String trainers = 'Trainers';
  static const String workouts = 'Workouts';
  static const String profile = 'Profile';
  
  static const String gymStatus = 'Gym Status';
  static const String activeTrainers = 'Active Trainers';
  static const String myMembership = 'My Membership';
  static const String fixedWorkouts = 'Programs';
  static const String myRoutines = 'My Routines';
  
  static const String noDataFound = 'No data found';
  static const String errorOccurred = 'An error occurred';
  static const String tryAgain = 'Try Again';
}
