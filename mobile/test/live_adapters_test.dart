/// Regression tests for the live repository <-> backend adapter.
///
/// These lock in the integration fixes:
/// - transaction filters are sent as query parameters (`search`, not `query`)
/// - backend list envelopes (`items`) are read into UI models
/// - demo auth persona mapping and nested `user.id` parsing
/// - tax and scam response shapes map onto the UI models
library dueswise.test.live_adapters_test;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:dueswise/data/live/api_client.dart';
import 'package:dueswise/data/live/live_finance_repository.dart';
import 'package:dueswise/data/models/auth_result.dart';
import 'package:dueswise/data/models/scam_alert.dart';
import 'package:dueswise/data/models/tax_comparison.dart';

/// Fake HTTP client keyed by `METHOD /path` with request recording.
class _FakeClient extends http.BaseClient {
  _FakeClient();

  final Map<String, http.Response> responses = {};
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    final key = '${request.method} ${request.url.path}';
    final response = responses[key] ?? http.Response('{"error":{"code":"NOT_FOUND","message":"not found"}}', 404);
    return http.StreamedResponse(
      Stream.value(utf8.encode(response.body)),
      response.statusCode,
    );
  }

  void respond(String method, String path, Map<String, dynamic> body, {int status = 200}) {
    responses['$method $path'] = http.Response(jsonEncode(body), status);
  }

  http.Request get lastRequest => requests.last as http.Request;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late _FakeClient fake;
  late LiveFinanceRepository repo;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    fake = _FakeClient();
    repo = LiveFinanceRepository(
      apiClient: ApiClient(client: fake, baseUrl: 'http://localhost:8000'),
    );
  });

  test('transactions send filter query params and read the items envelope', () async {
    fake.respond('GET', '/api/v1/transactions', {
      'items': [
        {
          'id': 'txn_1',
          'amount_paise': 89900,
          'currency': 'INR',
          'transaction_type': 'debit',
          'merchant_raw': 'NETFLIX INDIA',
          'merchant_normalized': 'Netflix',
          'category': 'entertainment',
          'payment_method': 'upi',
          'transaction_date': '2026-11-18',
          'source': 'sms',
          'confidence': 0.97,
          'is_suspicious': false,
        }
      ],
      'total': 1,
      'page': 1,
      'page_size': 100,
    });

    final txns = await repo.getTransactions(category: 'entertainment', query: 'netflix');

    expect(txns, hasLength(1));
    expect(txns.first.displayMerchant, 'Netflix');

    final url = fake.lastRequest.url;
    expect(url.queryParameters['category'], 'entertainment');
    expect(url.queryParameters['search'], 'netflix');
    // Regression: the old code sent `query` and dropped the whole query string.
    expect(url.queryParameters.containsKey('query'), isFalse);
  });

  test('dues read the items envelope', () async {
    fake.respond('GET', '/api/v1/dues', {
      'items': [
        {
          'id': 'due_1',
          'title': 'Home EMI',
          'due_type': 'emi',
          'amount_paise': 2000000,
          'due_date': '2026-11-25',
          'frequency': 'monthly',
          'status': 'upcoming',
          'is_mandatory': true,
          'confidence': 1.0,
          'source': 'manual',
        }
      ],
      'total': 1,
    });

    final dues = await repo.getDues();
    expect(dues, hasLength(1));
    expect(dues.first.title, 'Home EMI');
    expect(dues.first.amountPaise, 2000000);
    expect(dues.first.isUpcoming, isTrue);
  });

  test('login uses the demo persona and parses the nested user id', () async {
    await repo.selectPersona(DemoPersona.shopkeeper);
    fake.respond('POST', '/api/v1/auth/demo', {
      'user': {
        'id': '33333333-3333-4333-8333-333333333333',
        'name': 'Rajesh Kumar',
        'persona': 'shopkeeper',
        'currency': 'INR',
      },
      'user_id': '33333333-3333-4333-8333-333333333333',
      'access_token': '33333333-3333-4333-8333-333333333333',
      'token_type': 'bearer',
      'expires_in_minutes': 30,
    });

    final result = await repo.login('demo@example.com', 'anything');

    expect(result.userId, '33333333-3333-4333-8333-333333333333');
    expect(result.accessToken, '33333333-3333-4333-8333-333333333333');
    expect(fake.lastRequest.body, contains('shopkeeper'));
  });

  test('register starts a demo session too (no real accounts)', () async {
    fake.respond('POST', '/api/v1/auth/demo', {
      'user_id': '11111111-1111-4111-8111-111111111111',
      'access_token': '11111111-1111-4111-8111-111111111111',
      'token_type': 'bearer',
      'expires_in_minutes': 30,
    });

    final result = await repo.register('new@example.com', 'password', 'New User');
    expect(result.userId, '11111111-1111-4111-8111-111111111111');
  });

  test('tax comparison sends backend deduction shape and maps its response', () async {
    fake.respond('POST', '/api/v1/tax/compare', {
      'financial_year': 'FY-2025-26',
      'gross_salary_paise': 60000000,
      'old_regime': {
        'taxable_income_paise': 54500000,
        'income_tax_paise': 712500,
        'cess_paise': 28500,
        'total_tax_paise': 741000,
      },
      'new_regime': {
        'taxable_income_paise': 52500000,
        'income_tax_paise': 675000,
        'cess_paise': 27000,
        'total_tax_paise': 702000,
      },
      'lower_tax_regime': 'new',
      'estimated_savings_paise': 39000,
      'disclaimer': 'Illustrative guidance only.',
    });

    final result = await repo.compareTax(TaxComparisonRequest(
      financialYear: 'FY-2025-26',
      annualIncomePaise: 60000000,
      deductionsPaise: 5000000,
    ));

    expect(result.taxYear, 'FY-2025-26');
    expect(result.recommendedLowerTaxRegime, 'new');
    expect(result.estimatedDifferencePaise, 39000);
    expect(result.newRegime.totalTaxPaise, 702000);

    final sent = jsonDecode(fake.lastRequest.body) as Map<String, dynamic>;
    expect(sent['annual_salary_paise'], 60000000);
    expect(sent['financial_year'], 'FY-2025-26');
    expect((sent['deductions'] as Map)['section_80c_paise'], 5000000);
  });

  test('scam analysis maps backend indicators and recommended actions', () async {
    fake.respond('POST', '/api/v1/scams/analyze', {
      'risk_score': 80,
      'risk_level': 'high',
      'verdict': 'scam',
      'indicators': [
        {'code': 'OTP_REQUEST', 'description': 'Requests an OTP or UPI PIN'},
      ],
      'explanation': 'This message asks for a secret credential.',
      'recommended_actions': ['Do not share the OTP.'],
    });

    final explanation = await repo.analyzeScam(
      ScamAnalysisRequest(message: 'Share your OTP now'),
    );

    expect(explanation.summary, 'This message asks for a secret credential.');
    expect(explanation.reasons, contains('Requests an OTP or UPI PIN'));
    expect(explanation.safeAction, 'Do not share the OTP.');

    final sent = jsonDecode(fake.lastRequest.body) as Map<String, dynamic>;
    expect(sent['message'], 'Share your OTP now');
  });

  test('scam alerts read the items envelope and flatten indicators', () async {
    fake.respond('GET', '/api/v1/scams', {
      'items': [
        {
          'id': 'alert_1',
          'message_masked': 'Your account will be blocked',
          'risk_score': 80,
          'risk_level': 'high',
          'verdict': 'scam',
          'indicators': [
            {'code': 'URGENT_THREAT', 'description': 'Creates urgency or threats'},
          ],
          'explanation': 'Urgent wording is a common phishing signal.',
          'status': 'new',
          'created_at': '2026-11-19T10:00:00+05:30',
        }
      ],
      'total': 1,
    });

    final alerts = await repo.getScamAlerts();
    expect(alerts, hasLength(1));
    expect(alerts.first.riskScore, 80);
    expect(alerts.first.indicators, contains('Creates urgency or threats'));
  });

  test('cashflow and investments map backend field names', () async {
    fake.respond('GET', '/api/v1/business/cashflow', {
      'currency': 'INR',
      'current_cash_paise': 4000000,
      'total_sales_paise': 1200000,
      'total_expenses_paise': 500000,
      'pending_receivables_paise': 250000,
      'pending_payables_paise': 100000,
      'projected_cash_balance_paise': 4950000,
      'forecast_date': '2026-11-19',
      'items': [],
    });
    fake.respond('GET', '/api/v1/investments/summary', {
      'currency': 'INR',
      'monthly_surplus_paise': 1000000,
      'suggested_sip_paise': 300000,
      'portfolio': [
        {'asset_name': 'Index Fund', 'asset_type': 'equity', 'value_paise': 5000000, 'weight_percent': 75},
      ],
      'concentration_risk': 'high',
      'educational_disclaimer': 'Educational only.',
    });

    final cashflow = await repo.getBusinessCashflow();
    expect(cashflow.salesPaise, 1200000);
    expect(cashflow.expensesPaise, 500000);
    expect(cashflow.receivablesPaise, 250000);
    expect(cashflow.payablesPaise, 100000);
    expect(cashflow.projectedCashBalancePaise, 4950000);

    final investments = await repo.getInvestmentSummary();
    expect(investments, hasLength(1));
    expect(investments.first.label, 'Index Fund');
    expect(investments.first.currentValuePaise, 5000000);
  });
}
