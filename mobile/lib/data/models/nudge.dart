/// Nudge per CONTRACTS §4.6 / BLUEPRINT §7.5.
class Nudge {
  final String id;
  final String type;
  final String priority; // low, medium, high
  final String title;
  final String message;
  final String createdAt;
  final bool read;

  Nudge({
    required this.id,
    required this.type,
    required this.priority,
    required this.title,
    required this.message,
    required this.createdAt,
    this.read = false,
  });

  bool get isHighPriority => priority == 'high';
  bool get isMediumPriority => priority == 'medium';
  bool get isLowPriority => priority == 'low';

  factory Nudge.fromJson(Map<String, dynamic> json) {
    return Nudge(
      id: json['id'] as String? ?? '',
      type: json['type'] as String? ?? 'general',
      priority: json['priority'] as String? ?? 'medium',
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      read: json['read'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'priority': priority,
      'title': title,
      'message': message,
      'created_at': createdAt,
      'read': read,
    };
  }

  Nudge copyWith({bool? read}) => Nudge(
        id: id,
        type: type,
        priority: priority,
        title: title,
        message: message,
        createdAt: createdAt,
        read: read ?? this.read,
      );
}
