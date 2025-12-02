class GymStatus {
  final int peopleInside;
  final int capacity;
  final double occupancyPercentage;

  GymStatus({
    required this.peopleInside,
    required this.capacity,
    required this.occupancyPercentage,
  });

  factory GymStatus.fromJson(Map<String, dynamic> json) {
    return GymStatus(
      peopleInside: json['people_inside'] ?? 0,
      capacity: json['capacity'] ?? 1,
      occupancyPercentage: (json['occupancy_percentage'] ?? 0).toDouble(),
    );
  }

  String get statusText {
    if (occupancyPercentage < 30) return 'Not Crowded';
    if (occupancyPercentage < 60) return 'Moderate';
    if (occupancyPercentage < 85) return 'Busy';
    return 'Very Crowded';
  }
}

class ActiveTrainer {
  final String name;
  final String specialty;

  ActiveTrainer({required this.name, required this.specialty});

  factory ActiveTrainer.fromJson(Map<String, dynamic> json) {
    return ActiveTrainer(
      name: json['name'] ?? '',
      specialty: json['specialty'] ?? '',
    );
  }
}

class MembershipSummary {
  final String type;
  final String infoText;
  final int remaining;

  MembershipSummary({
    required this.type,
    required this.infoText,
    required this.remaining,
  });

  factory MembershipSummary.fromJson(Map<String, dynamic> json) {
    return MembershipSummary(
      type: json['type'] ?? '',
      infoText: json['info_text'] ?? 'No active membership',
      remaining: json['remaining'] ?? 0,
    );
  }
}

class HomeData {
  final GymStatus gymStatus;
  final List<ActiveTrainer> activeTrainers;
  final MembershipSummary membership;

  HomeData({
    required this.gymStatus,
    required this.activeTrainers,
    required this.membership,
  });

  factory HomeData.fromJson(Map<String, dynamic> json) {
    return HomeData(
      gymStatus: GymStatus.fromJson(json['gym_status'] ?? {}),
      activeTrainers: (json['active_trainers'] as List?)
              ?.map((e) => ActiveTrainer.fromJson(e))
              .toList() ??
          [],
      membership: MembershipSummary.fromJson(json['my_membership'] ?? {}),
    );
  }
}
