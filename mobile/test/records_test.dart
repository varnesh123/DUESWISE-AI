/// Tests for user-entered records, real-account endpoints, and amount parsing.
library dueswise.test.records_test;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/data/live/api_client.dart';
import 'package:dueswise/data/live/live_finance_repository.dart';
import 'package:dueswise/data/live/token_store.dart';
import 'package:dueswise/data/mock/mock_finance_repository.dart';

class _FakeClient extends http.BaseClient {
  _FakeClient();

  final Map<String, http.Response> responses = {};
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    final key = '${request.method} ${request.url.path}';
    final response =
        responses[key] ?? http.Response('{"error":{"code":"NOT_FOUND","message":"not found"}}', 404);
    return http.StreamedResponse(
      Stream.value(utf8.encode(response.body)),
      response.statusCode,
      headers: {'content-type': 'application/json'},
    );
  }

  void respond(String method, String path, Map<String, dynamic> body, {int status = 200}) {
    responses['$method $path'] = http.Response(jsonEncode(body), status);
  }

  void respondEmpty(String method, String path, {int status = 204}) {
    responses['$method $path'] = http.Response('', status);
  }

  http.Request get lastRequest => requests.last as http.Request;

  Map<String, dynamic> get lastBody =>
      jsonDecode((requests.last as http.Request).body) as Map<String, dynamic>;
}

Map<String, dynamic> _dueJson({
  String id = 'due-1',
  String title = 'Home rent',
  int amount = 1200000,
  String frequency = 'monthly',
}) {
  return {
    'id': id,
    'title': title,
    'due_type': 'rent',
    'amount_paise': amount,
    'due_date': '2026-12-01',
    'frequency': frequency,
    'status': 'upcoming',
    'is_mandatory': true,
    'confidence': 1.0,
    'source': 'manual',
  };
}

Map<String, dynamic> _txnJson({
  String id = 'txn-1',
  String merchant = 'Grocery store',
  int amount = 45000,
}) {
  return {
    'id': id,
    'amount_paise': amount,
    'currency': 'INR',
    'transaction_type': 'debit',
    'merchant_raw': merchant,
    'merchant_normalized': merchant,
    'category': 'groceries',
    'payment_method': 'upi',
    'transaction_date': '2026-11-20',
    'source': 'manual',
    'confidence': 1.0,
    'is_suspicious': false,
  };
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('parseRupeesToPaise', () {
    test('parses whole rupees and decimals without floating point', () {
      expect(parseRupeesToPaise('1200'), 120000);
      expect(parseRupeesToPaise('₹1,200.50'), 120050);
      expect(parseRupeesToPaise(' 899.9 '), 89990);
      expect(parseRupeesToPaise('0'), 0);
    });

    test('rejects invalid and negative amounts', () {
      expect(parseRupeesToPaise(''), isNull);
      expect(parseRupeesToPaise('-1'), isNull);
      expect(parseRupeesToPaise('1.2.3'), isNull);
      expect(parseRupeesToPaise('abc'), isNull);
    });
  });

  group('Mock repository record CRUD', () {
    late MockFinanceRepository repo;

    setUp(() {
      repo = MockFinanceRepository();
    });

    test('creates, edits, and deletes a due', () async {
      final created = await repo.createDue(
        title: 'Internet bill',
        dueType: 'utility',
        amountPaise: 79900,
        dueDate: '2026-12-10',
      );
      expect(created.status, 'upcoming');
      expect((await repo.getDues()).any((d) => d.id == created.id), isTrue);

      final updated = await repo.updateDue(
        created.id,
        title: 'Internet + TV',
        amountPaise: 99900,
        frequency: 'quarterly',
      );
      expect(updated.title, 'Internet + TV');
      expect(updated.amountPaise, 99900);
      expect(updated.frequency, 'quarterly');

      await repo.deleteDue(created.id);
      expect((await repo.getDues()).any((d) => d.id == created.id), isFalse);
    });

    test('creates, edits, and deletes a transaction', () async {
      final created = await repo.createTransaction(
        amountPaise: 45000,
        transactionType: 'debit',
        merchant: 'Corner shop',
        category: 'groceries',
      );
      expect(created.merchantNormalized, 'Corner shop');

      final updated = await repo.updateTransaction(
        created.id,
        amountPaise: 49000,
        merchant: 'Supermarket',
        category: 'food',
      );
      expect(updated.amountPaise, 49000);
      expect(updated.displayMerchant, 'Supermarket');
      expect(updated.category, 'food');

      await repo.deleteTransaction(created.id);
      expect((await repo.getTransactions()).any((t) => t.id == created.id), isFalse);
    });
  });

  group('Live repository record endpoints', () {
    late _FakeClient fake;
    late LiveFinanceRepository repo;

    setUp(() {
      SharedPreferences.setMockInitialValues({});
      fake = _FakeClient();
      repo = LiveFinanceRepository(
        apiClient: ApiClient(client: fake, baseUrl: 'http://localhost:8000'),
        tokenStore: InMemoryTokenStore('session-token'),
      );
    });

    test('creates a transaction through the manual endpoint', () async {
      fake.respond('POST', '/api/v1/transactions/manual', _txnJson(), status: 201);

      final txn = await repo.createTransaction(
        amountPaise: 45000,
        transactionType: 'debit',
        merchant: 'Grocery store',
        category: 'groceries',
      );

      expect(txn.amountPaise, 45000);
      expect(fake.lastRequest.url.path, '/api/v1/transactions/manual');
      expect(fake.lastBody['merchant'], 'Grocery store');
      expect(fake.lastBody['amount_paise'], 45000);
      expect(fake.lastRequest.headers['authorization'], 'Bearer session-token');
    });

    test('updates and deletes a transaction', () async {
      fake.respond('PATCH', '/api/v1/transactions/txn-1', _txnJson(amount: 99000));
      fake.respondEmpty('DELETE', '/api/v1/transactions/txn-1');

      final updated = await repo.updateTransaction('txn-1', amountPaise: 99000);
      expect(updated.amountPaise, 99000);
      expect(fake.lastRequest.method, 'PATCH');

      await repo.deleteTransaction('txn-1');
      expect(fake.lastRequest.method, 'DELETE');
      expect(fake.lastRequest.url.path, '/api/v1/transactions/txn-1');
    });

    test('creates, updates, and deletes a due', () async {
      fake.respond('POST', '/api/v1/dues', _dueJson(), status: 201);
      fake.respond('PATCH', '/api/v1/dues/due-1', _dueJson(title: 'New rent', amount: 1500000));
      fake.respondEmpty('DELETE', '/api/v1/dues/due-1');

      final created = await repo.createDue(
        title: 'Home rent',
        dueType: 'rent',
        amountPaise: 1200000,
        dueDate: '2026-12-01',
      );
      expect(created.frequency, 'monthly');
      expect(fake.lastBody['frequency'], 'monthly');

      final updated = await repo.updateDue('due-1', title: 'New rent', amountPaise: 1500000);
      expect(updated.title, 'New rent');
      expect(updated.amountPaise, 1500000);

      await repo.deleteDue('due-1');
      expect(fake.lastRequest.method, 'DELETE');
    });

    test('fetches the signed-in account and logs out', () async {
      fake.respond('GET', '/api/v1/auth/me', {
        'id': 'user-1',
        'name': 'Asha',
        'email': 'asha@example.com',
        'persona': 'individual',
        'currency': 'INR',
        'is_demo': false,
      });
      fake.respondEmpty('POST', '/api/v1/auth/logout');

      final user = await repo.getCurrentUser();
      expect(user.name, 'Asha');
      expect(user.isDemo, isFalse);

      await repo.logout();
      expect(fake.lastRequest.url.path, '/api/v1/auth/logout');
    });
  });
}
