class Trainer {
  final int trainerId;
  final String name;
  final String specialty;
  final bool isInGym;
  final double ratingAvg;

  Trainer({
    required this.trainerId,
    required this.name,
    required this.specialty,
    required this.isInGym,
    required this.ratingAvg,
  });

  factory Trainer.fromJson(Map<String, dynamic> json) {
    final rating = json['rating_avg'];
    double ratingValue = 0.0;
    if (rating is num) {
      ratingValue = rating.toDouble();
    } else if (rating is String) {
      ratingValue = double.tryParse(rating) ?? 0.0;
    }
    
    return Trainer(
      trainerId: json['trainer_id'] ?? 0,
      name: json['name'] ?? '',
      specialty: json['specialty'] ?? '',
      isInGym: json['is_in_gym'] == 1 || json['is_in_gym'] == true,
      ratingAvg: ratingValue,
    );
  }
}
