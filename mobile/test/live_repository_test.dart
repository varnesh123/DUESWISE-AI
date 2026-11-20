/// Tests for the Phase 6 live repository and API client.
///
/// These tests verify request/response serialization, endpoint paths,
/// error handling, and mock-vs-live switching without requiring a live
/// backend. A fake [http.Client] is used so no network is involved.
library dueswise.test.live_repository_test;

import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/data/live/api_client.dart' hide NetworkException, NotFoundException;
import 'package:dueswise/data/live/live_finance_repository.dart';
import 'package:dueswise/data/mock/mock_finance_repository.dart';
import 'package:dueswise/data/models/auth_result.dart';
import 'package:dueswise/data/models/dashboard_summary.dart';
import 'package:dueswise/data/models/scam_alert.dart';
import 'package:dueswise/data/models/tax_comparison.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/app/repository_provider.dart';

/// A fake HTTP client that records requests and returns canned responses.
class _FakeClient extends http.BaseClient {
  _FakeClient(this._responses);

  final Map<String, http.Response> _responses;
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    final key = '${request.method} ${request.url.path}';
    final response = _responses[key] ?? http.Response('not found', 404);
    return http.StreamedResponse(
      Stream.value(utf8.encode(response.body)),
      response.statusCode,
    );
  }

  void close() {}

  void setResponse(String method, String path, http.Response response) {
    _responses['$method $path'] = response;
  }

  http.Request? lastRequest() =>
      requests.isNotEmpty && requests.last is http.Request
          ? requests.last as http.Request
          : null;
}

http.Response _okJson(Map<String, dynamic> body) {
  return http.Response(_encodeJson(body), 200);
}

String _encodeJson(Map<String, dynamic> body) {
  final parts = <String>[];
  body.forEach((k, v) {
    parts.add('"$k":${_jsonValue(v)}');
  });
  return '{${parts.join(',')}}';
}

String _jsonValue(dynamic v) {
  if (v is String) return '"${v.replaceAll('"', '\\"')}"';
  if (v is num) return v.toString();
  if (v is bool) return v.toString();
  if (v is List) {
    return '[${v.map(_jsonValue).join(',')}]';
  }
  if (v is Map) {
    final parts = <String>[];
    v.forEach((k, val) => parts.add('"$k":${_jsonValue(val)}'));
    return '{${parts.join(',')}}';
  }
  return 'null';
}

http.Response _errorJson(String code, String message, {int statusCode = 400}) {
  return http.Response(
    '{"error":{"code":"$code","message":"$message","details":{}}}',
    statusCode,
  );
}

/// A client that always throws to simulate network failure.
class _ThrowingClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    throw http.ClientException('connection refused');
  }

  void close() {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  SharedPreferences.setMockInitialValues({});

  group('ApiClient endpoint paths and headers', () {
    late _FakeClient fakeClient;
    late ApiClient client;

    setUp(() {
      fakeClient = _FakeClient({});
      client = ApiClient(client: fakeClient, baseUrl: 'http://localhost:8000');
    });

    test('GET request hits the correct backend path with auth header', () async {
      fakeClient.setResponse('GET', '/api/v1/dashboard/summary', _okJson({'currency': 'INR'}));
      client.setAccessToken('test_token_123');

      await client.get('/dashboard/summary');

      final req = fakeClient.lastRequest();
      expect(req, isNotNull);
      expect(req!.url.toString(), 'http://localhost:8000/api/v1/dashboard/summary');
      expect(req.headers['authorization'], 'Bearer test_token_123');
      expect(req.headers['content-type'], 'application/json');
    });

    test('POST request sends JSON body without auth when includeAuth=false', () async {
      fakeClient.setResponse('POST', '/api/v1/auth/login', _okJson({'access_token': 'tok', 'user_id': 'u1', 'expires_in_minutes': 30}));
      client.setAccessToken('existing_token');

      await client.post('/auth/login', body: {'email': 'a@b.com', 'password': 'pw'}, includeAuth: false);

      final req = fakeClient.lastRequest();
      expect(req, isNotNull);
      expect(req!.url.toString(), 'http://localhost:8000/api/v1/auth/login');
      expect(req.headers.containsKey('authorization'), isFalse);
      expect(req.body, contains('email'));
    });

    test('Network exception throws NetworkException', () async {
      final throwingClient = _ThrowingClient();
      final badClient = ApiClient(client: throwingClient, baseUrl: 'http://localhost:8000');

      try {
        await badClient.get('/dashboard/summary');
        fail('Expected AppException');
      } on AppException catch (e) {
        expect(e.code, 'NETWORK_ERROR');
      }
    });

    test('401 response throws UnauthorizedException', () async {
      fakeClient.setResponse('GET', '/api/v1/dashboard/summary', _errorJson('UNAUTHORIZED', 'Token expired', statusCode: 401));

      try {
        await client.get('/dashboard/summary');
        fail('Expected AppException');
      } on AppException catch (e) {
        expect(e.code, 'UNAUTHORIZED');
      }
    });

    test('Server error response throws AppException with contract code', () async {
      fakeClient.setResponse('GET', '/api/v1/dues', _errorJson('VALIDATION_ERROR', 'Invalid request', statusCode: 422));

      try {
        await client.get('/dues');
        fail('Expected AppException');
      } on AppException catch (e) {
        expect(e.code, 'VALIDATION_ERROR');
      }
    });

    test('Empty 200 response returns null body', () async {
      fakeClient.setResponse('GET', '/api/v1/dues', http.Response('', 200));
      final result = await client.get('/dues');
      expect(result, isNull);
    });
  });
group('LiveFinanceRepository serialization', () {
  test('Dashboard JSON maps to DashboardSummary model', () {
    final json = {
      'currency': 'INR',
      'available_balance_paise': 3200000,
      'safe_to_spend_paise': 845000,
      'upcoming_dues_total_paise': 2000000,
      'safety_reserve_paise': 355000,
      'calculated_until': '2026-11-25',
      'explanation': 'Available balance minus upcoming mandatory dues.',
      'data_confidence': 'high',
      'last_updated': '2026-11-18T14:00:00+05:30',
    };
    final d = DashboardSummary.fromJson(json);
    expect(d.currency, 'INR');
    expect(d.availableBalancePaise, 3200000);
    expect(d.explanation, isNotEmpty);
  });

  test('Transaction JSON uses integer paise and snake_case', () {
    final json = {
      'id': 'txn_002',
      'amount_paise': 89900,
      'currency': 'INR',
      'transaction_type': 'debit',
      'merchant_raw': 'NETFLIX INDIA',
      'merchant_normalized': 'Netflix',
      'category': 'entertainment',
      'payment_method': 'UPI',
      'transaction_date': '2026-11-05',
      'source': 'sms',
      'confidence': 0.97,
    };
    final t = Transaction.fromJson(json);
    expect(t.amountPaise, 89900);
    expect(t.transactionType, 'debit');
    expect(t.displayMerchant, 'Netflix');
  });

  test('Tax comparison JSON matches contract schema', () {
    final json = {
      'tax_year': '2026-27',
      'old_regime': {
        'taxable_income_paise': 55000000,
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
      'recommended_lower_tax_regime': 'new',
      'estimated_difference_paise': 39000,
      'disclaimer': 'Illustrative guidance only.',
    };
    final tc = TaxComparison.fromJson(json);
    expect(tc.taxYear, '2026-27');
    expect(tc.estimatedDifferencePaise, 39000);
  });

  test('Scam analysis request serializes with snake_case', () {
    final req = ScamAnalysisRequest(
      message: 'Share your OTP now',
      riskScore: 80,
      riskLevel: 'high',
      indicators: ['Requests UPI PIN'],
    );
    final json = req.toJson();
    expect(json['risk_score'], 80);
    expect(json['risk_level'], 'high');
    expect(json['indicators'], ['Requests UPI PIN']);
  });

  test('Auth result serializes bearer token fields', () {
    final json = {
      'access_token': 'abc123',
      'token_type': 'Bearer',
      'expires_in_minutes': 30,
      'user_id': 'user_1',
    };
    final result = AuthResult.fromJson(json);
    expect(result.accessToken, 'abc123');
    expect(result.tokenType, 'Bearer');
    expect(result.expiresInMinutes, 30);
    expect(result.userId, 'user_1');
  });
});

group('Mock vs live repository switching', () {
  test('AppRepository defaults to mock when USE_MOCK_API=true', () {
    expect(AppConfig.useMockApi, isTrue);
    final repo = AppRepository.instance;
    expect(repo, isA<MockFinanceRepository>());
  });

  test('Mock repository works without backend services', () async {
    final repo = MockFinanceRepository();
    final summary = await repo.getDashboardSummary();
    expect(summary.currency, 'INR');
    final txns = await repo.getTransactions();
    expect(txns, isNotEmpty);
  });

  test('Mock and live repositories share the same interface', () {
    final mock = MockFinanceRepository();
    final live = LiveFinanceRepository();
    expect(mock, isA<FinanceRepository>());
    expect(live, isA<FinanceRepository>());
  });
});

group('Live repository error handling (no backend)', () {
  test('Live repository throws NetworkException when backend is down', () async {
    final repo = LiveFinanceRepository();
    try {
      await repo.getDashboardSummary();
      fail('Expected AppException');
    } on AppException catch (_) {
      // Expected when no backend is running
    }
  });
});
}