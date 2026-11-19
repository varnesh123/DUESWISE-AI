/// Real integration test: Flutter live repository ⇄ running FastAPI backend.
///
/// Not mocked. Requires the backend (and, with EXPECT_AI=true, the AI service)
/// to be running. Run with:
///
///   flutter test test/integration/live_backend_test.dart \
///     --dart-define=LIVE_BACKEND=http://127.0.0.1:8099 \
///     --dart-define=EXPECT_AI=true
///
/// When LIVE_BACKEND is not provided the test is skipped so the normal
/// offline suite stays green.
@Tags(['integration'])
library dueswise.test.integration.live_backend_test;

import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/data/live/api_client.dart' hide NotFoundException;
import 'package:dueswise/data/live/live_finance_repository.dart';
import 'package:dueswise/data/models/auth_result.dart';
import 'package:dueswise/data/models/scam_alert.dart';
import 'package:dueswise/data/models/tax_comparison.dart';

const String backendBase = String.fromEnvironment('LIVE_BACKEND');
const bool expectAi = bool.fromEnvironment('EXPECT_AI');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // flutter_test installs HttpOverrides that stub every request; this suite is
  // a real integration test and must reach the running backend.
  HttpOverrides.global = null;

  if (backendBase.isEmpty) {
    test(
      'live backend integration suite',
      () {},
      skip: 'Set --dart-define=LIVE_BACKEND=http://127.0.0.1:8099 to run',
    );
    return;
  }

  late LiveFinanceRepository repo;
  late ApiClient authed;

  setUpAll(() {
    SharedPreferences.setMockInitialValues({});
    repo = LiveFinanceRepository(apiClient: ApiClient(baseUrl: backendBase));
    authed = ApiClient(baseUrl: backendBase);
  });

  test('demo login issues a bearer token for the selected persona', () async {
    await repo.selectPersona(DemoPersona.salaried);
    final auth = await repo.login('demo@example.com', 'demo');

    expect(auth.accessToken, isNotEmpty);
    expect(auth.userId, isNotEmpty);
    authed.setAccessToken(auth.accessToken);
  });

  test('dashboard summary loads from the live database', () async {
    final summary = await repo.getDashboardSummary();
    expect(summary.currency, 'INR');
    expect(summary.availableBalancePaise, greaterThanOrEqualTo(0));
    expect(summary.safeToSpendPaise, greaterThanOrEqualTo(0));
  });

  test('manual ingestion stores a transaction that filters can find', () async {
    final ingested = await repo.ingestTransaction({
      'merchant_raw': 'ZOMATO ORDER 8812',
      'amount_paise': 45500,
      'transaction_type': 'debit',
    });

    expect(ingested.transaction.id, isNotEmpty);
    expect(ingested.transaction.amountPaise, 45500);
    expect(ingested.transaction.displayMerchant.toLowerCase(), contains('zomato'));

    if (expectAi) {
      // Proves the backend really called the AI service over HTTP.
      expect(ingested.processing['ai_used'], isTrue);
    }

    final filtered = await repo.getTransactions(category: 'food');
    expect(filtered.any((t) => t.id == ingested.transaction.id), isTrue);

    final searched = await repo.getTransactions(query: 'zomato');
    expect(searched, isNotEmpty);
    expect(searched.first.displayMerchant.toLowerCase(), contains('zomato'));
  });

  test('dues can be created, fetched and marked paid', () async {
    final created = await authed.post('/dues', body: {
      'title': 'E2E Rent',
      'due_type': 'rent',
      'amount_paise': 1500000,
      'due_date': '2026-12-01',
      'frequency': 'monthly',
      'is_mandatory': true,
    });
    expect(created, isNotNull);
    final dueId = created!['id'] as String;

    final due = await repo.getDue(dueId);
    expect(due.title, 'E2E Rent');
    expect(due.status, 'upcoming');

    await repo.markDuePaid(dueId);
    final paid = await repo.getDue(dueId);
    expect(paid.status, 'paid');

    final all = await repo.getDues();
    expect(all.any((d) => d.id == dueId), isTrue);
  });

  test('subscriptions and nudges respond with list envelopes', () async {
    final subs = await repo.getSubscriptions();
    expect(subs, isA<List<dynamic>>());

    final nudges = await repo.getNudges();
    expect(nudges, isA<List<dynamic>>());
  });

  test('scam analysis runs and the alert is listed', () async {
    final explanation = await repo.analyzeScam(
      ScamAnalysisRequest(
        message: 'Your account will be blocked. Share your OTP at http://fake.example now.',
      ),
    );
    expect(explanation.summary, isNotEmpty);
    expect(explanation.reasons, isNotEmpty);
    expect(explanation.safeAction, isNotEmpty);

    final alerts = await repo.getScamAlerts();
    expect(alerts, isNotEmpty);
    expect(alerts.first.riskScore, greaterThan(0));
  });

  test('tax comparison uses the shipped rules', () async {
    final result = await repo.compareTax(TaxComparisonRequest(
      financialYear: 'FY-2025-26',
      annualIncomePaise: 60000000,
      deductionsPaise: 5000000,
    ));
    expect(result.taxYear, 'FY-2025-26');
    expect(result.recommendedLowerTaxRegime, anyOf('old', 'new'));
    expect(result.oldRegime.totalTaxPaise, greaterThanOrEqualTo(0));
    expect(result.newRegime.totalTaxPaise, greaterThanOrEqualTo(0));
  });

  test('business cash flow and investments load', () async {
    final cashflow = await repo.getBusinessCashflow();
    expect(cashflow.projectedCashBalancePaise, greaterThanOrEqualTo(0));

    final investments = await repo.getInvestmentSummary();
    expect(investments, isNotEmpty);
    expect(investments.first.note, isNotEmpty);
  });

  test('unauthenticated calls surface a typed error', () async {
    SharedPreferences.setMockInitialValues({});
    final fresh = LiveFinanceRepository(apiClient: ApiClient(baseUrl: backendBase));
    try {
      await fresh.getDashboardSummary();
      fail('Expected an AppException for a missing bearer token');
    } on AppException catch (e) {
      expect(e.code, 'UNAUTHORIZED');
    }
  });
}
