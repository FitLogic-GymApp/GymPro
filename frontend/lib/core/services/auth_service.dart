import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class User {
  final int memberId;
  final String name;
  final String email;

  User({required this.memberId, required this.name, required this.email});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      memberId: json['member_id'] ?? 0,
      name: json['name'] ?? '',
      email: json['email'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'member_id': memberId,
        'name': name,
        'email': email,
      };
}

class Gym {
  final int gymId;
  final String name;
  final String location;
  final String membershipType;
  final bool isActive;

  Gym({
    required this.gymId,
    required this.name,
    required this.location,
    required this.membershipType,
    required this.isActive,
  });

  factory Gym.fromJson(Map<String, dynamic> json) {
    return Gym(
      gymId: json['gym_id'] ?? 0,
      name: json['name'] ?? '',
      location: json['location'] ?? '',
      membershipType: json['type'] ?? 'timed',
      isActive: json['is_active'] == 1 || json['is_active'] == true,
    );
  }
}

class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  final ApiService _api = ApiService();

  static const String _keyMemberId = 'member_id';
  static const String _keyUserName = 'user_name';
  static const String _keyUserEmail = 'user_email';
  static const String _keySelectedGymId = 'selected_gym_id';
  static const String _keySelectedGymName = 'selected_gym_name';

  User? _currentUser;
  Gym? _selectedGym;

  User? get currentUser => _currentUser;
  Gym? get selectedGym => _selectedGym;
  bool get isLoggedIn => _currentUser != null;
  bool get hasSelectedGym => _selectedGym != null;

  /// Uygulama başlangıcında session'ı kontrol et
  Future<bool> checkSession() async {
    final prefs = await SharedPreferences.getInstance();
    final memberId = prefs.getInt(_keyMemberId);
    final userName = prefs.getString(_keyUserName);
    final userEmail = prefs.getString(_keyUserEmail);

    if (memberId != null && userName != null) {
      _currentUser = User(
        memberId: memberId,
        name: userName,
        email: userEmail ?? '',
      );

      // Seçili gym varsa onu da yükle
      final gymId = prefs.getInt(_keySelectedGymId);
      final gymName = prefs.getString(_keySelectedGymName);
      if (gymId != null && gymName != null) {
        _selectedGym = Gym(
          gymId: gymId,
          name: gymName,
          location: '',
          membershipType: 'timed',
          isActive: true,
        );
      }
      return true;
    }
    return false;
  }

  /// Kullanıcı girişi
  Future<User> login(String email, String password) async {
    final response = await _api.post('/login', body: {
      'email': email,
      'password': password,
    });

    final user = User(
      memberId: response['member_id'],
      name: response['name'],
      email: email,
    );

    await _saveUser(user);
    _currentUser = user;
    return user;
  }

  /// Yeni kullanıcı kaydı
  Future<void> register(String name, String email, String password) async {
    await _api.post('/register', body: {
      'name': name,
      'email': email,
      'password': password,
    });
  }

  /// Kullanıcının üye olduğu salonları getir
  Future<List<Gym>> getMyGyms() async {
    if (_currentUser == null) throw Exception('Not logged in');

    final response = await _api.get('/my-gyms', queryParams: {
      'member_id': _currentUser!.memberId,
    });

    return (response as List).map((json) => Gym.fromJson(json)).toList();
  }

  /// Salon seç
  Future<void> selectGym(Gym gym) async {
    _selectedGym = gym;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keySelectedGymId, gym.gymId);
    await prefs.setString(_keySelectedGymName, gym.name);
  }

  /// Seçili salonu temizle (çıkış yaparken)
  void clearSelectedGym() {
    _selectedGym = null;
    SharedPreferences.getInstance().then((prefs) {
      prefs.remove(_keySelectedGymId);
      prefs.remove(_keySelectedGymName);
    });
  }

  /// Çıkış yap
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    _currentUser = null;
    _selectedGym = null;
  }

  /// Kullanıcıyı kaydet
  Future<void> _saveUser(User user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyMemberId, user.memberId);
    await prefs.setString(_keyUserName, user.name);
    await prefs.setString(_keyUserEmail, user.email);
  }
}
