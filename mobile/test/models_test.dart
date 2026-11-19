import 'package:flutter_test/flutter_test.dart';
import 'package:dueswise/data/models/dashboard_summary.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/models/tax_comparison.dart';
import 'package:dueswise/core/utils/money.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  group('Money formatting', () {
    test('formats integer paise as INR with Indian grouping', () {
      expect(Money(0).toInr(), '₹0.00');
      expect(Money(89900).toInr(), '₹899.00');
      expect(Money(1200000).toInr(), '₹12,000.00');
      expect(Money(120000000).toInr(), '₹12,00,000.00');
      expect(Money(123456).toInr(), '₹1,234.56');
      expect(Money(100).toInrWhole(), '₹1');
    });

    test('integer paise arithmetic never uses floating point', () {
      final a = Money(1200000);
      final b = Money(350000);
      expect((a - b).paise, 850000);
      expect((a + b).paise, 1550000);
    });
  });

  group('DashboardSummary JSON parsing', () {
    test('parses contract-compliant dashboard JSON', () {
      final json = {
        "currency": "INR",
        "available_balance_paise": 3200000,
        "safe_to_spend_paise": 845000,
        "upcoming_dues_total_paise": 2000000,
        "safety_reserve_paise": 355000,
        "calculated_until": "2026-11-25",
        "next_due": {
          "id": "due_001",
          "title": "Home EMI",
          "amount_paise": 1200000,
          "due_date": "2026-11-25",
          "due_type": "emi",
          "is_mandatory": true,
          "confidence": 0.95
        },
        "explanation": "Available balance minus upcoming mandatory dues, essential expenses and reserve.",
        "data_confidence": "high",
        "last_updated": "2026-11-18T14:00:00+05:30"
      };
      final d = DashboardSummary.fromJson(json);
      expect(d.currency, 'INR');
      expect(d.availableBalancePaise, 3200000);
      expect(d.safeToSpendPaise, 845000);
      expect(d.upcomingDuesTotalPaise, 2000000);
      expect(d.safetyReservePaise, 355000);
      expect(d.nextDue!.title, 'Home EMI');
      expect(d.nextDue!.amountPaise, 1200000);
      expect(d.dataConfidence, 'high');
    });

    test('handles missing optional next_due', () {
      final json = {
        "currency": "INR",
        "available_balance_paise": 100000,
        "safe_to_spend_paise": 40000,
        "upcoming_dues_total_paise": 50000,
        "safety_reserve_paise": 10000,
        "calculated_until": "2026-11-25",
        "data_confidence": "high",
        "last_updated": "2026-11-18T14:00:00+05:30"
      };
      final d = DashboardSummary.fromJson(json);
      expect(d.nextDue, isNull);
    });
  });

  group('Transaction JSON parsing', () {
    test('parses contract-compliant transaction', () {
      final json = {
        "id": "txn_002",
        "amount_paise": 89900,
        "currency": "INR",
        "transaction_type": "debit",
        "merchant_raw": "NETFLIX INDIA",
        "merchant_normalized": "Netflix",
        "category": "entertainment",
        "payment_method": "UPI",
        "transaction_date": "2026-11-05",
        "source": "sms",
        "confidence": 0.97
      };
      final t = Transaction.fromJson(json);
      expect(t.id, 'txn_002');
      expect(t.amountPaise, 89900);
      expect(t.isDebit, isTrue);
      expect(t.isCredit, isFalse);
      expect(t.displayMerchant, 'Netflix');
      expect(t.displayCategory, 'Entertainment');
    });

    test('falls back to merchant_raw when normalized missing', () {
      final json = {
        "id": "txn_001",
        "amount_paise": 10000,
        "currency": "INR",
        "transaction_type": "credit",
        "merchant_raw": "Salary Credit",
        "transaction_date": "2026-11-01",
      };
      final t = Transaction.fromJson(json);
      expect(t.displayMerchant, 'Salary Credit');
      expect(t.category, isNull);
    });
  });

  group('TaxComparison JSON parsing', () {
    test('parses old vs new regime', () {
      final json = {
        "tax_year": "2026-27",
        "old_regime": {
          "taxable_income_paise": 55000000,
          "income_tax_paise": 712500,
          "cess_paise": 28500,
          "total_tax_paise": 741000
        },
        "new_regime": {
          "taxable_income_paise": 52500000,
          "income_tax_paise": 675000,
          "cess_paise": 27000,
          "total_tax_paise": 702000
        },
        "recommended_lower_tax_regime": "new",
        "estimated_difference_paise": 39000,
        "disclaimer": "Illustrative guidance only. Verify applicable rules."
      };
      final tc = TaxComparison.fromJson(json);
      expect(tc.taxYear, '2026-27');
      expect(tc.oldRegime.totalTaxPaise, 741000);
      expect(tc.newRegime.totalTaxPaise, 702000);
      expect(tc.recommendedLowerTaxRegime, 'new');
      expect(tc.estimatedDifferencePaise, 39000);
    });
  });
}
