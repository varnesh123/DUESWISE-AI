/// Subscription per CONTRACTS §4.5 / BLUEPRINT §7.4.
import 'package:dueswise/core/utils/money.dart';

class Subscription {
  final String id;
  final String merchant;
  final String category;
  final int expectedAmountPaise;
  final String frequency; // monthly, yearly, quarterly, weekly
  final String nextDueDate; // YYYY-MM-DD
  final double detectionConfidence;
  final String status; // active, cancelled, paused, uncertain
  final bool isUserConfirmed;
  final int priceChangePercent;

  Subscription({
    required this.id,
    required this.merchant,
    required this.category,
    required this.expectedAmountPaise,
    required this.frequency,
    required this.nextDueDate,
    required this.detectionConfidence,
    required this.status,
    required this.isUserConfirmed,
    this.priceChangePercent = 0,
  });

  Money get expectedAmount => Money(expectedAmountPaise);

  bool get isActive => status == 'active';

  factory Subscription.fromJson(Map<String, dynamic> json) {
    return Subscription(
      id: json['id'] as String? ?? '',
      merchant: json['merchant'] as String? ?? '',
      category: json['category'] as String? ?? '',
      expectedAmountPaise: int.tryParse(json['expected_amount_paise']?.toString() ?? '') ?? 0,
      frequency: json['frequency'] as String? ?? 'monthly',
      nextDueDate: json['next_due_date'] as String? ?? '',
      detectionConfidence: (json['detection_confidence'] is num)
          ? (json['detection_confidence'] as num).toDouble()
          : 0.0,
      status: json['status'] as String? ?? 'active',
      isUserConfirmed: json['is_user_confirmed'] as bool? ?? false,
      priceChangePercent: int.tryParse(json['price_change_percent']?.toString() ?? '') ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'merchant': merchant,
      'category': category,
      'expected_amount_paise': expectedAmountPaise,
      'frequency': frequency,
      'next_due_date': nextDueDate,
      'detection_confidence': detectionConfidence,
      'status': status,
      'is_user_confirmed': isUserConfirmed,
      'price_change_percent': priceChangePercent,
    };
  }

  Subscription copyWith({
    String? id,
    String? merchant,
    String? category,
    int? expectedAmountPaise,
    String? frequency,
    String? nextDueDate,
    double? detectionConfidence,
    String? status,
    bool? isUserConfirmed,
    int? priceChangePercent,
  }) {
    return Subscription(
      id: id ?? this.id,
      merchant: merchant ?? this.merchant,
      category: category ?? this.category,
      expectedAmountPaise: expectedAmountPaise ?? this.expectedAmountPaise,
      frequency: frequency ?? this.frequency,
      nextDueDate: nextDueDate ?? this.nextDueDate,
      detectionConfidence: detectionConfidence ?? this.detectionConfidence,
      status: status ?? this.status,
      isUserConfirmed: isUserConfirmed ?? this.isUserConfirmed,
      priceChangePercent: priceChangePercent ?? this.priceChangePercent,
    );
  }
}
