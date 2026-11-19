/// Live [FinanceRepository] implementation backed by the main backend
/// (Developer A, port 8000).
///
/// All network calls go through [ApiClient], which authenticates with a
/// bearer token and translates HTTP errors into [AppException] instances.
///
/// Flutter never calls the independent AI service (`:8001`) directly.
///
/// Some endpoints used by the mock repository (mark-as-paid, confirm /
/// dismiss subscription, mark nudge read) are not yet defined in
/// CONTRACTS.md. They are implemented here with documented assumptions
/// and flagged for Developer A confirmation.
library dueswise.data.live.live_finance_repository;

import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/data/live/api_client.dart' hide NotFoundException;
import 'package:dueswise/data/models/auth_result.dart';
import 'package:dueswise/data/models/business_cashflow.dart';
import 'package:dueswise/data/models/dashboard_summary.dart';
import 'package:dueswise/data/models/due.dart';
import 'package:dueswise/data/models/investment_summary.dart';
import 'package:dueswise/data/models/nudge.dart';
import 'package:dueswise/data/models/scam_alert.dart';
import 'package:dueswise/data/models/subscription.dart';
import 'package:dueswise/data/models/tax_comparison.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Key under which the access token is persisted.
const String _tokenKey = 'dueswise_access_token';

/// Key under which the selected persona index is persisted.
const String _personaKey = 'dueswise_selected_persona';

/// Live repository backed by HTTP calls to the main backend.
class LiveFinanceRepository implements FinanceRepository {
  LiveFinanceRepository() {
    _apiClient = ApiClient(baseUrl: AppConfig.backendBaseUrl);
    _prefs = null;
    _selectedPersona = DemoPersona.salaried;
    _loadTokenAndPersona();
  }

  late final ApiClient _apiClient;
  SharedPreferences? _prefs;
  late DemoPersona _selectedPersona;

  Future<void> _loadTokenAndPersona() async {
    _prefs = await SharedPreferences.getInstance();
    final token = _prefs?.getString(_tokenKey);
    _apiClient.setAccessToken(token);
    final personaIndex = _prefs?.getInt(_personaKey) ?? 0;
    _selectedPersona = DemoPersona.values[personaIndex.clamp(0, DemoPersona.values.length - 1)];
  }

  @override
  DemoPersona get selectedPersona => _selectedPersona;

  @override
  List<DemoPersona> get availablePersonas => DemoPersona.values;

  @override
  Future<void> selectPersona(DemoPersona persona) async {
    _selectedPersona = persona;
    await _prefs?.setInt(_personaKey, DemoPersona.values.indexOf(persona));
  }

  // ========================================================================
  // Authentication
  // ========================================================================

  @override
  Future<AuthResult> login(String email, String password) async {
    final body = await _apiClient.post(
      '/auth/login',
      body: <String, dynamic>{
        'email': email,
        'password': password,
      },
      includeAuth: false,
    );
    return _parseAuthResult(body);
  }

  @override
  Future<AuthResult> register(String email, String password, String name) async {
    final body = await _apiClient.post(
      '/auth/register',
      body: <String, dynamic>{
        'email': email,
        'password': password,
        'name': name,
      },
      includeAuth: false,
    );
    return _parseAuthResult(body);
  }

  AuthResult _parseAuthResult(Map<String, dynamic>? body) {
    if (body == null) {
      throw AppException(
        code: 'INVALID_RESPONSE',
        message: 'Authentication response was empty.',
      );
    }
    final result = AuthResult.fromJson(body);
    if (result.accessToken.isNotEmpty) {
      _apiClient.persistToken(result.accessToken, (t) async {
        await _prefs?.setString(_tokenKey, t ?? '');
      });
    }
    return result;
  }

  @override
  Future<void> logout() async {
    await _apiClient.clearToken((t) async {
      await _prefs?.setString(_tokenKey, t ?? '');
    });
    _selectedPersona = DemoPersona.salaried;
    await _prefs?.setInt(_personaKey, 0);
  }

  // ========================================================================
  // Dashboard
  // ========================================================================

  @override
  Future<DashboardSummary> getDashboardSummary() async {
    final body = await _apiClient.get('/dashboard/summary');
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Dashboard response was empty.');
    }
    return DashboardSummary.fromJson(body);
  }

  @override
  Future<void> refreshDashboard() async {
    await getDashboardSummary();
  }

  // ========================================================================
  // Transactions
  // ========================================================================

  @override
  Future<List<Transaction>> getTransactions({String? category, String? query}) async {
    final queryParams = <String, String>{};
    if (category != null && category.isNotEmpty) {
      queryParams['category'] = category;
    }
    if (query != null && query.isNotEmpty) {
      queryParams['query'] = query;
    }
    final uri = Uri.parse('$_apiBaseUrl/transactions').replace(queryParameters: queryParams);
    final body = await _apiClient.get(uri.path);
    if (body == null) return <Transaction>[];
    final list = body['transactions'] as List<dynamic>? ?? <dynamic>[];
    return list.map((e) => Transaction.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  String get _apiBaseUrl => AppConfig.apiBaseUrl;

  @override
  Future<IngestedTransaction> ingestTransaction(Map<String, dynamic> payload) async {
    final body = await _apiClient.post(
      '/transactions/ingest',
      body: payload,
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Ingest response was empty.');
    }
    return IngestedTransaction.fromJson(body);
  }

  // ========================================================================
  // Dues
  // ========================================================================

  @override
  Future<List<Due>> getDues() async {
    final body = await _apiClient.get('/dues');
    if (body == null) return <Due>[];
    final list = body['dues'] as List<dynamic>? ?? <dynamic>[];
    return list.map((e) => Due.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  @override
  Future<Due> getDue(String id) async {
    // NOTE: CONTRACTS.md does not define a per-due detail endpoint.
    // Assumption: GET /api/v1/dues/{id}. Confirm with Developer A.
    final body = await _apiClient.get('/dues/$id');
    if (body == null) {
      throw NotFoundException(message: 'Due $id not found.');
    }
    return Due.fromJson(body);
  }

  @override
  Future<void> markDuePaid(String dueId) async {
    // NOTE: CONTRACTS.md does not define a mark-as-paid endpoint.
    // Assumption: PATCH /api/v1/dues/{id}/pay. Confirm with Developer A.
    await _apiClient.patch('/dues/$dueId/pay');
  }

  // ========================================================================
  // Subscriptions
  // ========================================================================

  @override
  Future<List<Subscription>> getSubscriptions() async {
    final body = await _apiClient.get('/subscriptions');
    if (body == null) return <Subscription>[];
    final list = body['subscriptions'] as List<dynamic>? ?? <dynamic>[];
    return list.map((e) => Subscription.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  @override
  Future<void> confirmSubscription(String subId) async {
    // NOTE: CONTRACTS.md does not define a confirm-subscription endpoint.
    // Assumption: POST /api/v1/subscriptions/{id}/confirm. Confirm with Developer A.
    await _apiClient.post('/subscriptions/$subId/confirm');
  }

  @override
  Future<void> dismissSubscription(String subId) async {
    // NOTE: CONTRACTS.md does not define a dismiss-subscription endpoint.
    // Assumption: POST /api/v1/subscriptions/{id}/dismiss. Confirm with Developer A.
    await _apiClient.post('/subscriptions/$subId/dismiss');
  }

  // ========================================================================
  // Nudges
  // ========================================================================

  @override
  Future<List<Nudge>> getNudges() async {
    final body = await _apiClient.get('/nudges');
    if (body == null) return <Nudge>[];
    final list = body['nudges'] as List<dynamic>? ?? <dynamic>[];
    return list.map((e) => Nudge.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  @override
  Future<void> markNudgeRead(String nudgeId) async {
    // NOTE: CONTRACTS.md does not define a mark-nudge-read endpoint.
    // Assumption: POST /api/v1/nudges/{id}/read. Confirm with Developer A.
    await _apiClient.post('/nudges/$nudgeId/read');
  }

  // ========================================================================
  // Scam
  // ========================================================================

  @override
  Future<ScamExplanation> analyzeScam(ScamAnalysisRequest request) async {
    final body = await _apiClient.post(
      '/scam-alerts/analyze',
      body: request.toJson(),
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Scam analysis response was empty.');
    }
    return ScamExplanation.fromJson(body);
  }

  @override
  Future<List<ScamAlert>> getScamAlerts() async {
    final body = await _apiClient.get('/scam-alerts');
    if (body == null) return <ScamAlert>[];
    final list = body['scam_alerts'] as List<dynamic>? ?? <dynamic>[];
    return list.map((e) => ScamAlert.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  // ========================================================================
  // Tax
  // ========================================================================

  @override
  Future<TaxComparison> compareTax(TaxComparisonRequest request) async {
    final body = await _apiClient.post(
      '/tax/compare',
      body: request.toJson(),
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Tax comparison response was empty.');
    }
    return TaxComparison.fromJson(body);
  }

  // ========================================================================
  // Business cash flow
  // ========================================================================

  @override
  Future<BusinessCashflow> getBusinessCashflow() async {
    final body = await _apiClient.get('/business/cashflow');
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Business cashflow response was empty.');
    }
    return BusinessCashflow.fromJson(body);
  }

  // ========================================================================
  // Investments
  // ========================================================================

  @override
  Future<List<InvestmentSummary>> getInvestmentSummary() async {
    final body = await _apiClient.get('/investments/summary');
    if (body == null) return <InvestmentSummary>[];
    final list = body['investments'] as List<dynamic>? ?? <dynamic>[];
    return list.map((e) => InvestmentSummary.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  // ========================================================================
  // Settings / notifications
  // ========================================================================

  @override
  Future<bool> getNotificationsEnabled() async {
    return _prefs?.getBool('dueswise_notifications') ?? true;
  }

  @override
  Future<void> setNotificationsEnabled(bool enabled) async {
    await _prefs?.setBool('dueswise_notifications', enabled);
  }

  @override
  Future<int> getWeeklyNudgeCap() async {
    return _prefs?.getInt('dueswise_nudge_cap') ?? AppConstants.weeklyNudgeCap;
  }

  @override
  Future<void> setWeeklyNudgeCap(int cap) async {
    await _prefs?.setInt('dueswise_nudge_cap', cap.clamp(1, 10));
  }
}