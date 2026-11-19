/// Upcoming due per CONTRACTS §4.4 / BLUEPRINT §7.3.
import 'package:dueswise/core/utils/money.dart';

class Due {
  final String id;
  final String title;
  final String dueType; // emi, rent, subscription, insurance, utility, other
  final int amountPaise;
  final String dueDate; // YYYY-MM-DD
  final String status; // upcoming, due, paid, overdue
  final bool isMandatory;
  final double? confidence;

  Due({
    required this.id,
    required this.title,
    required this.dueType,
    required this.amountPaise,
    required this.dueDate,
    required this.status,
    this.isMandatory = true,
    this.confidence,
  });

  Money get amount => Money(amountPaise);

  bool get isUpcoming => status == 'upcoming';
  bool get isDue => status == 'due';
  bool get isOverdue => status == 'overdue';
  bool get isPaid => status == 'paid';

  String get displayCategory => dueType
      .split('_')
      .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '')
      .join(' ');

  factory Due.fromJson(Map<String, dynamic> json) {
    return Due(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      dueType: json['due_type'] as String? ?? 'other',
      amountPaise: int.tryParse(json['amount_paise']?.toString() ?? '') ?? 0,
      dueDate: json['due_date'] as String? ?? '',
      status: json['status'] as String? ?? 'upcoming',
      isMandatory: json['is_mandatory'] as bool? ?? true,
      confidence: json['confidence'] is num
          ? (json['confidence'] as num).toDouble()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'due_type': dueType,
      'amount_paise': amountPaise,
      'due_date': dueDate,
      'status': status,
      'is_mandatory': isMandatory,
      if (confidence != null) 'confidence': confidence,
    };
  }

  Due copyWith({
    String? id,
    String? title,
    String? dueType,
    int? amountPaise,
    String? dueDate,
    String? status,
    bool? isMandatory,
    double? confidence,
  }) {
    return Due(
      id: id ?? this.id,
      title: title ?? this.title,
      dueType: dueType ?? this.dueType,
      amountPaise: amountPaise ?? this.amountPaise,
      dueDate: dueDate ?? this.dueDate,
      status: status ?? this.status,
      isMandatory: isMandatory ?? this.isMandatory,
      confidence: confidence ?? this.confidence,
    );
  }
}
