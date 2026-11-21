/// Live [FinanceRepository] implementation backed by the main backend
/// (FastAPI, default `http://localhost:8000`).
///
/// All network calls go through [ApiClient], which authenticates with a
/// bearer token and translates HTTP errors into [AppException] instances.
///
/// Flutter never calls the independent AI service (`:8001`) directly.
///
/// This repository is the single adapter between the backend's JSON and the
/// UI models. Where the backend uses a different envelope or field name than
/// the UI model (for example list responses use `items`), the mapping happens
/// here so the rest of the app stays backend-agnostic.
library dueswise.data.live.live_finance_repository;

import 'package:shared_preferences/shared_preferences.dart';

import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/data/live/api_client.dart' hide NotFoundException;
import 'package:dueswise/data/live/token_store.dart';
import 'package:dueswise/data/models/auth_result.dart';
import 'package:dueswise/data/models/auth_user.dart';
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

/// Key under which the selected persona index is persisted.
const String _personaKey = 'dueswise_selected_persona';

/// Financial year whose deterministic rules ship with the backend
/// (`backend/app/rules/tax_rules.json`). The backend rejects other years.
const String _supportedTaxYear = 'FY-2025-26';

/// Live repository backed by HTTP calls to the main backend.
class LiveFinanceRepository implements FinanceRepository {
  LiveFinanceRepository({ApiClient? apiClient, TokenStore? tokenStore}) {
    _apiClient = apiClient ?? ApiClient(baseUrl: AppConfig.backendBaseUrl);
    _tokenStore = tokenStore ?? SecureTokenStore();
    _prefs = null;
    _selectedPersona = DemoPersona.salaried;
    _initFuture = _loadTokenAndPersona();
  }

  late final ApiClient _apiClient;
  late final TokenStore _tokenStore;
  SharedPreferences? _prefs;
  late DemoPersona _selectedPersona;
  Future<void>? _initFuture;

  /// Wait until the persisted token and persona have been restored.
  Future<void> _ensureReady() async {
    await (_initFuture ??= _loadTokenAndPersona());
  }

  Future<void> _loadTokenAndPersona() async {
    _prefs = await SharedPreferences.getInstance();
    final token = await _tokenStore.read();
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
    await _ensureReady();
    _selectedPersona = persona;
    await _prefs?.setInt(_personaKey, DemoPersona.values.indexOf(persona));
  }

  // ========================================================================
  // Authentication (real accounts + explicit demo sessions)
  // ========================================================================

  /// Map the UI persona to the backend's demo persona key.
  String _backendPersonaKey(DemoPersona persona) {
    switch (persona) {
      case DemoPersona.salaried:
        return 'salaried';
      case DemoPersona.youngProfessional:
        return 'young_professional';
      case DemoPersona.shopkeeper:
        return 'shopkeeper';
    }
  }

  @override
  Future<AuthResult> login(String email, String password) async {
    await _ensureReady();
    final body = await _apiClient.post(
      '/auth/login',
      body: <String, dynamic>{'email': email.trim(), 'password': password},
      includeAuth: false,
    );
    return _parseAuthResult(body);
  }

  @override
  Future<AuthResult> register(String email, String password, String name) async {
    await _ensureReady();
    final body = await _apiClient.post(
      '/auth/register',
      body: <String, dynamic>{
        'name': name.trim(),
        'email': email.trim(),
        'password': password,
      },
      includeAuth: false,
    );
    return _parseAuthResult(body);
  }

  @override
  Future<AuthResult> loginDemo(DemoPersona persona) async {
    await _ensureReady();
    _selectedPersona = persona;
    await _prefs?.setInt(_personaKey, DemoPersona.values.indexOf(persona));
    final body = await _apiClient.post(
      '/auth/demo',
      body: <String, dynamic>{'persona': _backendPersonaKey(persona)},
      includeAuth: false,
    );
    return _parseAuthResult(body);
  }

  Future<AuthResult> _parseAuthResult(Map<String, dynamic>? body) async {
    if (body == null) {
      throw AppException(
        code: 'INVALID_RESPONSE',
        message: 'Authentication response was empty.',
      );
    }
    final result = AuthResult.fromJson(body);
    if (result.accessToken.isNotEmpty) {
      await _apiClient.persistToken(result.accessToken, _tokenStore.write);
    }
    return result;
  }

  @override
  Future<AuthUser> getCurrentUser() async {
    await _ensureReady();
    final body = await _apiClient.get('/auth/me');
    if (body == null) {
      throw AppException(
        code: 'INVALID_RESPONSE',
        message: 'Account response was empty.',
      );
    }
    return AuthUser.fromJson(body);
  }

  @override
  Future<void> logout() async {
    await _ensureReady();
    // Best-effort server revocation; always clear the local token.
    try {
      await _apiClient.post('/auth/logout');
    } catch (_) {
      // Offline or already-expired sessions are still cleared locally.
    }
    await _apiClient.clearToken(_tokenStore.write);
    _selectedPersona = DemoPersona.salaried;
    await _prefs?.setInt(_personaKey, 0);
  }

  // ========================================================================
  // Dashboard
  // ========================================================================

  @override
  Future<DashboardSummary> getDashboardSummary() async {
    await _ensureReady();
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
    await _ensureReady();
    final params = <String, String>{'page_size': '100'};
    if (category != null && category.isNotEmpty) {
      params['category'] = category;
    }
    // The backend filter parameter is `search` (merchant/category text).
    if (query != null && query.isNotEmpty) {
      params['search'] = query;
    }
    final qs = params.entries
        .map((e) => '${Uri.encodeQueryComponent(e.key)}=${Uri.encodeQueryComponent(e.value)}')
        .join('&');
    final body = await _apiClient.get('/transactions?$qs');
    return _itemsOf(body, 'transactions')
        .map((e) => Transaction.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  @override
  Future<IngestedTransaction> ingestTransaction(Map<String, dynamic> payload) async {
    await _ensureReady();
    final body = await _apiClient.post('/transactions/ingest', body: payload);
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Ingest response was empty.');
    }
    return IngestedTransaction.fromJson(body);
  }

  @override
  Future<Transaction> createTransaction({
    required int amountPaise,
    required String transactionType,
    required String merchant,
    String? category,
    String paymentMethod = 'upi',
    String? transactionDate,
    String? description,
  }) async {
    await _ensureReady();
    final date = transactionDate ?? DateTime.now().toIso8601String().split('T').first;
    final body = await _apiClient.post(
      '/transactions/manual',
      body: <String, dynamic>{
        'amount_paise': amountPaise,
        'transaction_type': transactionType,
        'merchant': merchant,
        if (category != null && category.isNotEmpty) 'category': category,
        'payment_method': paymentMethod,
        'transaction_date': date,
        if (description != null && description.isNotEmpty) 'description': description,
      },
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Transaction response was empty.');
    }
    return Transaction.fromJson(body);
  }

  @override
  Future<Transaction> updateTransaction(
    String id, {
    int? amountPaise,
    String? transactionType,
    String? merchant,
    String? category,
    String? paymentMethod,
    String? transactionDate,
    String? description,
  }) async {
    await _ensureReady();
    final body = await _apiClient.patch(
      '/transactions/$id',
      body: <String, dynamic>{
        if (amountPaise != null) 'amount_paise': amountPaise,
        if (transactionType != null) 'transaction_type': transactionType,
        if (merchant != null) 'merchant': merchant,
        if (category != null) 'category': category,
        if (paymentMethod != null) 'payment_method': paymentMethod,
        if (transactionDate != null) 'transaction_date': transactionDate,
        if (description != null) 'description': description,
      },
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Transaction response was empty.');
    }
    return Transaction.fromJson(body);
  }

  @override
  Future<void> deleteTransaction(String id) async {
    await _ensureReady();
    await _apiClient.delete('/transactions/$id');
  }

  // ========================================================================
  // Dues
  // ========================================================================

  @override
  Future<List<Due>> getDues() async {
    await _ensureReady();
    final body = await _apiClient.get('/dues');
    return _itemsOf(body, 'dues')
        .map((e) => Due.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  @override
  Future<Due> getDue(String id) async {
    await _ensureReady();
    final body = await _apiClient.get('/dues/$id');
    if (body == null) {
      throw NotFoundException(message: 'Due $id not found.');
    }
    return Due.fromJson(body);
  }

  @override
  Future<void> markDuePaid(String dueId) async {
    await _ensureReady();
    final today = DateTime.now().toIso8601String().split('T').first;
    await _apiClient.post(
      '/dues/$dueId/mark-paid',
      body: <String, dynamic>{'paid_date': today},
    );
  }

  @override
  Future<Due> createDue({
    required String title,
    required String dueType,
    required int amountPaise,
    required String dueDate,
    String frequency = 'monthly',
    bool isMandatory = true,
  }) async {
    await _ensureReady();
    final body = await _apiClient.post(
      '/dues',
      body: <String, dynamic>{
        'title': title,
        'due_type': dueType,
        'amount_paise': amountPaise,
        'due_date': dueDate,
        'frequency': frequency,
        'is_mandatory': isMandatory,
      },
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Due response was empty.');
    }
    return Due.fromJson(body);
  }

  @override
  Future<Due> updateDue(
    String id, {
    String? title,
    String? dueType,
    int? amountPaise,
    String? dueDate,
    String? frequency,
    bool? isMandatory,
    String? status,
  }) async {
    await _ensureReady();
    final body = await _apiClient.patch(
      '/dues/$id',
      body: <String, dynamic>{
        if (title != null) 'title': title,
        if (dueType != null) 'due_type': dueType,
        if (amountPaise != null) 'amount_paise': amountPaise,
        if (dueDate != null) 'due_date': dueDate,
        if (frequency != null) 'frequency': frequency,
        if (isMandatory != null) 'is_mandatory': isMandatory,
        if (status != null) 'status': status,
      },
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Due response was empty.');
    }
    return Due.fromJson(body);
  }

  @override
  Future<void> deleteDue(String id) async {
    await _ensureReady();
    await _apiClient.delete('/dues/$id');
  }

  // ========================================================================
  // Subscriptions
  // ========================================================================

  @override
  Future<List<Subscription>> getSubscriptions() async {
    await _ensureReady();
    final body = await _apiClient.get('/subscriptions');
    return _itemsOf(body, 'subscriptions')
        .map((e) => Subscription.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  @override
  Future<void> confirmSubscription(String subId) async {
    await _ensureReady();
    await _apiClient.post('/subscriptions/$subId/confirm');
  }

  @override
  Future<void> dismissSubscription(String subId) async {
    await _ensureReady();
    await _apiClient.post('/subscriptions/$subId/dismiss');
  }

  // ========================================================================
  // Nudges
  // ========================================================================

  @override
  Future<List<Nudge>> getNudges() async {
    await _ensureReady();
    final body = await _apiClient.get('/nudges');
    return _itemsOf(body, 'nudges')
        .map((e) => Nudge.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  @override
  Future<void> markNudgeRead(String nudgeId) async {
    await _ensureReady();
    await _apiClient.post('/nudges/$nudgeId/read');
  }

  // ========================================================================
  // Scam detection
  // ========================================================================

  @override
  Future<ScamExplanation> analyzeScam(ScamAnalysisRequest request) async {
    await _ensureReady();
    final body = await _apiClient.post(
      '/scams/analyze',
      body: <String, dynamic>{
        'message': request.message ?? '',
        'source': 'manual',
      },
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Scam analysis response was empty.');
    }
    final reasons = _indicatorStrings(body['indicators']);
    final actions = (body['recommended_actions'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .where((s) => s.isNotEmpty)
            .toList() ??
        <String>[];
    final riskLevel = body['risk_level'] as String? ?? 'low';
    final score = body['risk_score'];
    final explanation = (body['explanation'] as String?)?.trim();
    return ScamExplanation(
      summary: (explanation != null && explanation.isNotEmpty)
          ? explanation
          : 'Risk level: $riskLevel${score != null ? ' ($score/100)' : ''}',
      reasons: reasons.isEmpty ? <String>['No strong indicators detected.'] : reasons,
      safeAction: actions.isNotEmpty
          ? actions.first
          : 'Do not share your OTP, UPI PIN or password. Verify via your bank’s official app or customer care.',
    );
  }

  @override
  Future<List<ScamAlert>> getScamAlerts() async {
    await _ensureReady();
    final body = await _apiClient.get('/scams');
    return _itemsOf(body, 'scam_alerts').map((raw) {
      final json = Map<String, dynamic>.from(raw as Map);
      final reasons = _indicatorStrings(json['indicators']);
      return ScamAlert(
        id: json['id']?.toString() ?? '',
        riskScore: _asInt(json['risk_score']),
        riskLevel: json['risk_level']?.toString() ?? 'low',
        verdict: json['verdict']?.toString() ?? 'safe',
        indicators: reasons,
        explanation: json['explanation']?.toString() ?? '',
        status: json['status']?.toString() ?? 'new',
      );
    }).toList();
  }

  // ========================================================================
  // Tax comparison
  // ========================================================================

  @override
  Future<TaxComparison> compareTax(TaxComparisonRequest request) async {
    await _ensureReady();
    // The backend expects annual_salary_paise plus itemised deductions and a
    // rules-backed financial year. The UI collects one deduction total, which
    // is mapped to Section 80C (see docs/API_INTEGRATION.md).
    final body = await _apiClient.post(
      '/tax/compare',
      body: <String, dynamic>{
        'financial_year': _supportedTaxYear,
        'annual_salary_paise': request.annualIncomePaise,
        'deductions': <String, dynamic>{
          'section_80c_paise': request.deductionsPaise,
        },
      },
    );
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Tax comparison response was empty.');
    }
    final oldRegime = Map<String, dynamic>.from(body['old_regime'] as Map? ?? {});
    final newRegime = Map<String, dynamic>.from(body['new_regime'] as Map? ?? {});
    return TaxComparison(
      taxYear: body['financial_year']?.toString() ?? _supportedTaxYear,
      oldRegime: TaxRegimeResult.fromJson(oldRegime),
      newRegime: TaxRegimeResult.fromJson(newRegime),
      recommendedLowerTaxRegime:
          body['lower_tax_regime']?.toString() ?? 'new',
      estimatedDifferencePaise: _asInt(body['estimated_savings_paise']),
      disclaimer: body['disclaimer']?.toString() ??
          'Illustrative guidance only. Verify applicable rules.',
    );
  }

  // ========================================================================
  // Business cash flow
  // ========================================================================

  @override
  Future<BusinessCashflow> getBusinessCashflow() async {
    await _ensureReady();
    final body = await _apiClient.get('/business/cashflow');
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Business cashflow response was empty.');
    }
    return BusinessCashflow(
      salesPaise: _asInt(body['total_sales_paise']),
      expensesPaise: _asInt(body['total_expenses_paise']),
      receivablesPaise: _asInt(body['pending_receivables_paise']),
      payablesPaise: _asInt(body['pending_payables_paise']),
      projectedCashBalancePaise: _asInt(body['projected_cash_balance_paise']),
      period: body['forecast_date']?.toString() ?? 'current_month',
    );
  }

  // ========================================================================
  // Investments (simulated, educational)
  // ========================================================================

  @override
  Future<List<InvestmentSummary>> getInvestmentSummary() async {
    await _ensureReady();
    final body = await _apiClient.get('/investments/summary');
    if (body == null) {
      throw AppException(code: 'INVALID_RESPONSE', message: 'Investment response was empty.');
    }

    // Contract-style list (used by the mock fixtures) if present.
    if (body['investments'] is List) {
      return (body['investments'] as List<dynamic>)
          .map((e) => InvestmentSummary.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    }

    // Backend returns a single summary with a portfolio allocation.
    final disclaimer = body['educational_disclaimer']?.toString() ??
        'Simulated educational data. Not a real investment.';
    final portfolio = body['portfolio'] as List<dynamic>? ?? <dynamic>[];
    return portfolio.map((raw) {
      final asset = Map<String, dynamic>.from(raw as Map);
      final value = _asInt(asset['value_paise']);
      return InvestmentSummary(
        label: asset['asset_name']?.toString() ?? 'Asset',
        investedAmountPaise: value,
        currentValuePaise: value,
        gainLossPaise: 0,
        returnPercent: 0,
        assetClass: asset['asset_type']?.toString() ?? 'equity',
        note: '${asset['weight_percent'] ?? 0}% weight · $disclaimer',
      );
    }).toList();
  }

  // ========================================================================
  // Settings / notifications
  // ========================================================================

  @override
  Future<bool> getNotificationsEnabled() async {
    await _ensureReady();
    return _prefs?.getBool('dueswise_notifications') ?? true;
  }

  @override
  Future<void> setNotificationsEnabled(bool enabled) async {
    await _ensureReady();
    await _prefs?.setBool('dueswise_notifications', enabled);
  }

  @override
  Future<int> getWeeklyNudgeCap() async {
    await _ensureReady();
    return _prefs?.getInt('dueswise_nudge_cap') ?? AppConstants.weeklyNudgeCap;
  }

  @override
  Future<void> setWeeklyNudgeCap(int cap) async {
    await _ensureReady();
    await _prefs?.setInt('dueswise_nudge_cap', cap.clamp(1, 10));
  }

  // ========================================================================
  // Helpers
  // ========================================================================

  /// Read a list from responses that may use `items` or the contract key.
  List<dynamic> _itemsOf(Map<String, dynamic>? body, String contractKey) {
    if (body == null) return <dynamic>[];
    final raw = body['items'] ?? body[contractKey];
    return raw is List ? raw : <dynamic>[];
  }

  /// Backend scam indicators are `{code, description}` objects.
  List<String> _indicatorStrings(dynamic indicators) {
    if (indicators is! List) return <String>[];
    return indicators
        .map((i) {
          if (i is Map) {
            final description = i['description']?.toString();
            if (description != null && description.isNotEmpty) return description;
            return i['code']?.toString() ?? '';
          }
          return i.toString();
        })
        .where((s) => s.isNotEmpty)
        .toList();
  }

  int _asInt(dynamic v) {
    if (v is int) return v;
    if (v is num) return v.toInt();
    return int.tryParse(v?.toString() ?? '') ?? 0;
  }
}
