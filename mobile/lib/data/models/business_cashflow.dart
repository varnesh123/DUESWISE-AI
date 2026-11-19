/// Small-business cash flow per CONTRACTS §4.9 / BLUEPRINT.
import 'package:dueswise/core/utils/money.dart';

class BusinessCashflow {
  final int salesPaise;
  final int expensesPaise;
  final int receivablesPaise;
  final int payablesPaise;
  final int projectedCashBalancePaise;
  final String period;

  BusinessCashflow({
    required this.salesPaise,
    required this.expensesPaise,
    required this.receivablesPaise,
    required this.payablesPaise,
    required this.projectedCashBalancePaise,
    required this.period,
  });

  Money get sales => Money(salesPaise);
  Money get expenses => Money(expensesPaise);
  Money get receivables => Money(receivablesPaise);
  Money get payables => Money(payablesPaise);
  Money get projectedCashBalance => Money(projectedCashBalancePaise);

  /// Net operating cash flow = sales - expenses.
  int get netOperatingFlowPaise => salesPaise - expensesPaise;

  /// Working capital gap = receivables - payables.
  int get workingCapitalGapPaise => receivablesPaise - payablesPaise;

  factory BusinessCashflow.fromJson(Map<String, dynamic> json) {
    return BusinessCashflow(
      salesPaise: int.tryParse(json['sales_paise']?.toString() ?? '') ?? 0,
      expensesPaise: int.tryParse(json['expenses_paise']?.toString() ?? '') ?? 0,
      receivablesPaise: int.tryParse(json['receivables_paise']?.toString() ?? '') ?? 0,
      payablesPaise: int.tryParse(json['payables_paise']?.toString() ?? '') ?? 0,
      projectedCashBalancePaise: int.tryParse(json['projected_cash_balance_paise']?.toString() ?? '') ?? 0,
      period: json['period'] as String? ?? 'current_month',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'sales_paise': salesPaise,
      'expenses_paise': expensesPaise,
      'receivables_paise': receivablesPaise,
      'payables_paise': payablesPaise,
      'projected_cash_balance_paise': projectedCashBalancePaise,
      'period': period,
    };
  }
}
