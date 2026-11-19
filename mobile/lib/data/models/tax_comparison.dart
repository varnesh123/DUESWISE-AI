/// Tax comparison per CONTRACTS §4.8 / BLUEPRINT §7.7.
import 'package:dueswise/core/utils/money.dart';

class TaxRegimeResult {
  final int taxableIncomePaise;
  final int incomeTaxPaise;
  final int cessPaise;
  final int totalTaxPaise;

  TaxRegimeResult({
    required this.taxableIncomePaise,
    required this.incomeTaxPaise,
    required this.cessPaise,
    required this.totalTaxPaise,
  });

  Money get taxableIncome => Money(taxableIncomePaise);
  Money get incomeTax => Money(incomeTaxPaise);
  Money get cess => Money(cessPaise);
  Money get totalTax => Money(totalTaxPaise);

  factory TaxRegimeResult.fromJson(Map<String, dynamic> json) {
    return TaxRegimeResult(
      taxableIncomePaise: int.tryParse(json['taxable_income_paise']?.toString() ?? '') ?? 0,
      incomeTaxPaise: int.tryParse(json['income_tax_paise']?.toString() ?? '') ?? 0,
      cessPaise: int.tryParse(json['cess_paise']?.toString() ?? '') ?? 0,
      totalTaxPaise: int.tryParse(json['total_tax_paise']?.toString() ?? '') ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'taxable_income_paise': taxableIncomePaise,
      'income_tax_paise': incomeTaxPaise,
      'cess_paise': cessPaise,
      'total_tax_paise': totalTaxPaise,
    };
  }
}

class TaxComparison {
  final String taxYear;
  final TaxRegimeResult oldRegime;
  final TaxRegimeResult newRegime;
  final String recommendedLowerTaxRegime;
  final int estimatedDifferencePaise;
  final String disclaimer;

  TaxComparison({
    required this.taxYear,
    required this.oldRegime,
    required this.newRegime,
    required this.recommendedLowerTaxRegime,
    required this.estimatedDifferencePaise,
    required this.disclaimer,
  });

  Money get estimatedDifference => Money(estimatedDifferencePaise);

  factory TaxComparison.fromJson(Map<String, dynamic> json) {
    return TaxComparison(
      taxYear: json['tax_year'] as String? ?? '2026-27',
      oldRegime: TaxRegimeResult.fromJson(
        Map<String, dynamic>.from(json['old_regime'] as Map? ?? {}),
      ),
      newRegime: TaxRegimeResult.fromJson(
        Map<String, dynamic>.from(json['new_regime'] as Map? ?? {}),
      ),
      recommendedLowerTaxRegime:
          json['recommended_lower_tax_regime'] as String? ?? 'new',
      estimatedDifferencePaise: int.tryParse(json['estimated_difference_paise']?.toString() ?? '') ?? 0,
      disclaimer: json['disclaimer'] as String? ??
          'Illustrative guidance only. Verify applicable rules.',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'tax_year': taxYear,
      'old_regime': oldRegime.toJson(),
      'new_regime': newRegime.toJson(),
      'recommended_lower_tax_regime': recommendedLowerTaxRegime,
      'estimated_difference_paise': estimatedDifferencePaise,
      'disclaimer': disclaimer,
    };
  }
}

/// Input to the tax comparison endpoint.
class TaxComparisonRequest {
  final String financialYear;
  final int annualIncomePaise;
  final int deductionsPaise;

  TaxComparisonRequest({
    required this.financialYear,
    required this.annualIncomePaise,
    required this.deductionsPaise,
  });

  Map<String, dynamic> toJson() {
    return {
      'financial_year': financialYear,
      'annual_income_paise': annualIncomePaise,
      'deductions_paise': deductionsPaise,
    };
  }
}
