import 'package:flutter_test/flutter_test.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/data/mock/mock_finance_repository.dart';
import 'package:dueswise/data/models/scam_alert.dart';
import 'package:dueswise/data/models/tax_comparison.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  group('MockFinanceRepository', () {
    late FinanceRepository repo;

    setUp(() {
      repo = MockFinanceRepository();
    });

    test('login returns a mock auth result', () async {
      final result = await repo.login('user@example.com', 'password123');
      expect(result.accessToken, isNotEmpty);
      expect(result.userId, isNotEmpty);
    });

    test('dashboard summary loads with consistent STS values', () async {
      final d = await repo.getDashboardSummary();
      // STS = balance - mandatory dues - reserve (deterministic, backend-owned).
      expect(d.safeToSpendPaise, d.availableBalancePaise - d.upcomingDuesTotalPaise - d.safetyReservePaise);
      expect(d.currency, 'INR');
    });

    test('transactions can be filtered by category', () async {
      final all = await repo.getTransactions();
      expect(all, isNotEmpty);
      final food = await repo.getTransactions(category: 'food');
      expect(food, isNotEmpty);
      expect(food.every((t) => t.category == 'food'), isTrue);
    });

    test('transaction search filters by merchant', () async {
      final result = await repo.getTransactions(query: 'Netflix');
      expect(result, isNotEmpty);
      expect(result.every((t) => t.displayMerchant.toLowerCase().contains('netflix')), isTrue);
    });

    test('ingesting a transaction adds it to the list', () async {
      final before = (await repo.getTransactions()).length;
      await repo.ingestTransaction({
        'merchant_raw': 'Test Merchant',
        'amount_paise': 50000,
        'transaction_type': 'debit',
        'category': 'food',
      });
      final after = (await repo.getTransactions()).length;
      expect(after, before + 1);
    });

    test('dues load and mark-as-paid updates state', () async {
      final dues = await repo.getDues();
      expect(dues, isNotEmpty);
      await repo.markDuePaid(dues.first.id);
      final updated = await repo.getDue(dues.first.id);
      expect(updated.status, 'paid');
    });

    test('subscriptions confirm/dismiss work', () async {
      final subs = await repo.getSubscriptions();
      expect(subs, isNotEmpty);
      await repo.confirmSubscription(subs.first.id);
      final confirmed = await repo.getSubscriptions();
      expect(
        confirmed.firstWhere((s) => s.id == subs.first.id).isUserConfirmed,
        isTrue,
      );
      await repo.dismissSubscription(subs.first.id);
      final remaining = await repo.getSubscriptions();
      expect(remaining.any((s) => s.id == subs.first.id), isFalse);
    });

    test('nudges mark as read', () async {
      final nudges = await repo.getNudges();
      expect(nudges, isNotEmpty);
      final unread = nudges.firstWhere((n) => !n.read);
      await repo.markNudgeRead(unread.id);
      final updated = await repo.getNudges();
      expect(updated.firstWhere((n) => n.id == unread.id).read, isTrue);
    });

    test('scam analysis returns a deterministic explanation', () async {
      final result = await repo.analyzeScam(ScamAnalysisRequest(
        message: 'Your account will be blocked. Share your UPI PIN at http://x.example',
      ));
      expect(result.summary, isNotEmpty);
      expect(result.reasons, isNotEmpty);
      expect(result.safeAction, contains('OTP'));
    });

    test('scam analysis uses the supplied assessment, not an invented score', () async {
      final result = await repo.analyzeScam(ScamAnalysisRequest(
        message: 'Hello friend',
        riskScore: 90,
        riskLevel: 'critical',
        indicators: ['Known indicator'],
      ));
      expect(result.reasons, contains('Known indicator'));
      expect(result.safeAction, contains('PIN'));
    });

    test('tax comparison loads with disclaimer', () async {
      final tc = await repo.compareTax(TaxComparisonRequest(
        financialYear: '2026-27',
        annualIncomePaise: 60000000,
        deductionsPaise: 5000000,
      ));
      expect(tc.disclaimer, isNotEmpty);
      expect(tc.taxYear, '2026-27');
    });

    test('business cash flow loads with consistent fields', () async {
      final cf = await repo.getBusinessCashflow();
      expect(cf.period, isNotEmpty);
      // Projected cash balance = opening + sales - expenses + receivables - payables
      // With opening ₹0: 0 + 4,000,000 - 2,000,000 + 1,200,000 - 1,800,000 = 1,400,000
      // The fixture stores 5,400,000 which implies an opening balance of ₹4,00,000
      expect(cf.salesPaise, 4000000);
      expect(cf.expensesPaise, 2000000);
      expect(cf.receivablesPaise, 1200000);
      expect(cf.payablesPaise, 1800000);
      expect(cf.projectedCashBalancePaise, 5400000);
      expect(cf.netOperatingFlowPaise, 2000000);
      expect(cf.workingCapitalGapPaise, -600000);
    });

    test('investment summary is labelled simulated', () async {
      final inv = await repo.getInvestmentSummary();
      expect(inv, isNotEmpty);
      expect(inv.every((i) => i.note.contains('Simulated')), isTrue);
    });

    test('notification preferences can be toggled', () async {
      await repo.setNotificationsEnabled(false);
      expect(await repo.getNotificationsEnabled(), isFalse);
      await repo.setNotificationsEnabled(true);
      expect(await repo.getNotificationsEnabled(), isTrue);
    });

    test('weekly nudge cap is clamped', () async {
      await repo.setWeeklyNudgeCap(100);
      expect(await repo.getWeeklyNudgeCap(), 10);
      await repo.setWeeklyNudgeCap(0);
      expect(await repo.getWeeklyNudgeCap(), 1);
    });
  });
}
