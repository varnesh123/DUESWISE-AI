/// Dashboard summary per CONTRACTS §4.2 / BLUEPRINT §7.2.
import 'package:dueswise/core/utils/money.dart';

class DashboardSummary {
  final String currency;
  final int availableBalancePaise;
  final int safeToSpendPaise;
  final int upcomingDuesTotalPaise;
  final int safetyReservePaise;
  final String calculatedUntil;
  final NextDue? nextDue;
  final String explanation;
  final String dataConfidence;
  final String lastUpdated;

  DashboardSummary({
    required this.currency,
    required this.availableBalancePaise,
    required this.safeToSpendPaise,
    required this.upcomingDuesTotalPaise,
    required this.safetyReservePaise,
    required this.calculatedUntil,
    this.nextDue,
    required this.explanation,
    required this.dataConfidence,
    required this.lastUpdated,
  });

  Money get availableBalance => Money(availableBalancePaise);
  Money get safeToSpend => Money(safeToSpendPaise);
  Money get upcomingDuesTotal => Money(upcomingDuesTotalPaise);
  Money get safetyReserve => Money(safetyReservePaise);

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      currency: json['currency'] as String? ?? 'INR',
      availableBalancePaise: _asInt(json['available_balance_paise']) ?? 0,
      safeToSpendPaise: _asInt(json['safe_to_spend_paise']) ?? 0,
      upcomingDuesTotalPaise: _asInt(json['upcoming_dues_total_paise']) ?? 0,
      safetyReservePaise: _asInt(json['safety_reserve_paise']) ?? 0,
      calculatedUntil: json['calculated_until'] as String? ?? '',
      nextDue: json['next_due'] != null
          ? NextDue.fromJson(Map<String, dynamic>.from(json['next_due'] as Map))
          : null,
      explanation: json['explanation'] as String? ??
          'Available balance minus upcoming mandatory dues, essential expenses and reserve.',
      dataConfidence: json['data_confidence'] as String? ?? 'high',
      lastUpdated: json['last_updated'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'currency': currency,
      'available_balance_paise': availableBalancePaise,
      'safe_to_spend_paise': safeToSpendPaise,
      'upcoming_dues_total_paise': upcomingDuesTotalPaise,
      'safety_reserve_paise': safetyReservePaise,
      'calculated_until': calculatedUntil,
      if (nextDue != null) 'next_due': nextDue!.toJson(),
      'explanation': explanation,
      'data_confidence': dataConfidence,
      'last_updated': lastUpdated,
    };
  }

  SafeToSpendDisplay toDisplay() => SafeToSpendDisplay(
        availableBalance: availableBalance,
        safeToSpend: safeToSpend,
        upcomingDuesTotal: upcomingDuesTotal,
        safetyReserve: safetyReserve,
      );

  static int? _asInt(dynamic v) {
    if (v == null) return null;
    if (v is int) return v;
    if (v is num) return v.toInt();
    return int.tryParse(v.toString());
  }
}

class NextDue {
  final String id;
  final String title;
  final int amountPaise;
  final String dueDate;
  final String dueType;
  final bool isMandatory;
  final double? confidence;

  NextDue({
    required this.id,
    required this.title,
    required this.amountPaise,
    required this.dueDate,
    this.dueType = 'emi',
    this.isMandatory = true,
    this.confidence,
  });

  Money get amount => Money(amountPaise);

  factory NextDue.fromJson(Map<String, dynamic> json) {
    return NextDue(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      amountPaise: DashboardSummary._asInt(json['amount_paise']) ?? 0,
      dueDate: json['due_date'] as String? ?? '',
      dueType: json['due_type'] as String? ?? 'emi',
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
      'amount_paise': amountPaise,
      'due_date': dueDate,
      'due_type': dueType,
      'is_mandatory': isMandatory,
      if (confidence != null) 'confidence': confidence,
    };
  }
}
