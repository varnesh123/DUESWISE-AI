/// Simulated educational investment / SIP summary (mock only, never real).
import 'package:dueswise/core/utils/money.dart';

class InvestmentSummary {
  final String label;
  final int investedAmountPaise;
  final int currentValuePaise;
  final int gainLossPaise;
  final double returnPercent;
  final String assetClass;
  final String note;

  InvestmentSummary({
    required this.label,
    required this.investedAmountPaise,
    required this.currentValuePaise,
    required this.gainLossPaise,
    required this.returnPercent,
    required this.assetClass,
    required this.note,
  });

  Money get investedAmount => Money(investedAmountPaise);
  Money get currentValue => Money(currentValuePaise);
  Money get gainLoss => Money(gainLossPaise);

  bool get isGain => gainLossPaise >= 0;

  factory InvestmentSummary.fromJson(Map<String, dynamic> json) {
    return InvestmentSummary(
      label: json['label'] as String? ?? 'SIP',
      investedAmountPaise: int.tryParse(json['invested_amount_paise']?.toString() ?? '') ?? 0,
      currentValuePaise: int.tryParse(json['current_value_paise']?.toString() ?? '') ?? 0,
      gainLossPaise: int.tryParse(json['gain_loss_paise']?.toString() ?? '') ?? 0,
      returnPercent: (json['return_percent'] is num)
          ? (json['return_percent'] as num).toDouble()
          : 0.0,
      assetClass: json['asset_class'] as String? ?? 'Equity',
      note: json['note'] as String? ??
          'Simulated educational data. Not a real investment.',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'label': label,
      'invested_amount_paise': investedAmountPaise,
      'current_value_paise': currentValuePaise,
      'gain_loss_paise': gainLossPaise,
      'return_percent': returnPercent,
      'asset_class': assetClass,
      'note': note,
    };
  }
}
