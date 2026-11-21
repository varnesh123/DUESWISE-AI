/// Mock repository backed by bundled JSON fixtures.
///
/// All Phase 5 screens depend on FinanceRepository; this is the default
/// implementation (USE_MOCK_API=true). Deterministic, no network required.
import 'mock_data_loader.dart';

import '../models/auth_result.dart';
import '../models/auth_user.dart';
import '../models/business_cashflow.dart';
import '../models/dashboard_summary.dart';
import '../models/investment_summary.dart';
import '../models/nudge.dart';
import '../models/scam_alert.dart';
import '../models/subscription.dart';
import '../models/due.dart';
import '../models/transaction.dart';
import '../repositories/finance_repository.dart';
import '../models/tax_comparison.dart';
import '../../core/constants/app_constants.dart';

class MockFinanceRepository implements FinanceRepository {
  MockFinanceRepository() {
    _loader = MockDataLoader.instance;
    _reloadFixtures();
  }

  late final MockDataLoader _loader;

  DemoPersona _selectedPersona = DemoPersona.salaried;

  // Mutable local state (in-memory, reset per session).
  List<Transaction> _transactions = [];
  List<Due> _dues = [];
  List<Subscription> _subscriptions = [];
  List<Nudge> _nudges = [];
  List<ScamAlert> _scamAlerts = [];

  bool _notificationsEnabled = true;
  int _weeklyNudgeCap = AppConstants.weeklyNudgeCap;

  @override
  DemoPersona get selectedPersona => _selectedPersona;

  @override
  List<DemoPersona> get availablePersonas => DemoPersona.values;

  @override
  Future<void> selectPersona(DemoPersona persona) async {
    _selectedPersona = persona;
    // Reload deterministic fixtures consistent with the chosen persona.
    await _reloadFixtures();
  }

  Future<void> _reloadFixtures() async {
    _transactions = await _loader.loadTransactions();
    _dues = await _loader.loadDues();
    _subscriptions = await _loader.loadSubscriptions();
    _nudges = await _loader.loadNudges();
    _scamAlerts = await _loader.loadScamAlerts();
  }

  // ---- Dashboard ----
  @override
  Future<DashboardSummary> getDashboardSummary() async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _loader.loadDashboard(_selectedPersona);
  }

  @override
  Future<void> refreshDashboard() async {
    await getDashboardSummary();
  }

  // ---- Auth ----
  @override
  Future<AuthResult> login(String email, String password) async {
    await Future.delayed(const Duration(milliseconds: 600));
    return AuthResult(
      accessToken: 'mock_access_token_${_selectedPersona.name}',
      userId: 'user_${_selectedPersona.name}',
      expiresInMinutes: 30,
    );
  }

  @override
  Future<AuthResult> register(String email, String password, String name) async {
    await Future.delayed(const Duration(milliseconds: 600));
    return AuthResult(
      accessToken: 'mock_access_token_new',
      userId: 'user_new',
      expiresInMinutes: 30,
    );
  }

  @override
  Future<AuthUser> getCurrentUser() async {
    return AuthUser(
      id: 'user_${_selectedPersona.name}',
      name: _selectedPersona.label,
      persona: _selectedPersona.name,
      isDemo: true,
    );
  }

  @override
  Future<AuthResult> loginDemo(DemoPersona persona) async {
    await selectPersona(persona);
    return AuthResult(
      accessToken: 'mock_access_token_${persona.name}',
      userId: 'user_${persona.name}',
      expiresInMinutes: 30,
    );
  }

  @override
  Future<void> logout() async {
    await Future.delayed(const Duration(milliseconds: 300));
  }

  // ---- Transactions ----
  @override
  Future<List<Transaction>> getTransactions({String? category, String? query}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    var result = List<Transaction>.from(_transactions);
    if (category != null && category.isNotEmpty) {
      result = result.where((t) => t.category == category).toList();
    }
    if (query != null && query.isNotEmpty) {
      final q = query.toLowerCase();
      result = result.where((t) {
        return t.displayMerchant.toLowerCase().contains(q) ||
            (t.category ?? '').toLowerCase().contains(q);
      }).toList();
    }
    return result;
  }

  @override
  Future<IngestedTransaction> ingestTransaction(Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 500));
    final txn = Transaction.fromJson(Map<String, dynamic>.from(payload));
    _transactions.insert(0, txn);
    return IngestedTransaction(
      status: 'processed',
      transaction: txn,
      processing: {
        'parse_confidence': 0.96,
        'recurring_match': false,
        'fraud_risk': 'low',
      },
    );
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
    await Future.delayed(const Duration(milliseconds: 300));
    final txn = Transaction(
      id: 'mock_txn_${DateTime.now().microsecondsSinceEpoch}',
      amountPaise: amountPaise,
      currency: 'INR',
      transactionType: transactionType,
      merchantRaw: merchant,
      merchantNormalized: merchant,
      category: (category == null || category.isEmpty) ? 'other' : category,
      paymentMethod: paymentMethod,
      transactionDate:
          transactionDate ?? DateTime.now().toIso8601String().split('T').first,
      source: 'manual',
      confidence: 1.0,
    );
    _transactions.insert(0, txn);
    return txn;
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
    await Future.delayed(const Duration(milliseconds: 300));
    final index = _transactions.indexWhere((t) => t.id == id);
    if (index < 0) throw StateError('Transaction not found');
    final old = _transactions[index];
    final updated = Transaction(
      id: old.id,
      amountPaise: amountPaise ?? old.amountPaise,
      currency: old.currency,
      transactionType: transactionType ?? old.transactionType,
      merchantRaw: merchant ?? old.merchantRaw,
      merchantNormalized: merchant ?? old.merchantNormalized,
      category: category ?? old.category,
      paymentMethod: paymentMethod ?? old.paymentMethod,
      paymentApp: old.paymentApp,
      gateway: old.gateway,
      transactionDate: transactionDate ?? old.transactionDate,
      source: old.source,
      confidence: old.confidence,
    );
    _transactions[index] = updated;
    return updated;
  }

  @override
  Future<void> deleteTransaction(String id) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _transactions.removeWhere((t) => t.id == id);
  }

  // ---- Dues ----
  @override
  Future<List<Due>> getDues() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return List<Due>.from(_dues);
  }

  @override
  Future<Due> getDue(String id) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final due = _dues.firstWhere((d) => d.id == id, orElse: () => throw StateError('Due not found'));
    return due;
  }

  @override
  Future<void> markDuePaid(String dueId) async {
    await Future.delayed(const Duration(milliseconds: 300));
    _dues = _dues.map((d) => d.id == dueId ? d.copyWith(status: 'paid') : d).toList();
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
    await Future.delayed(const Duration(milliseconds: 300));
    final due = Due(
      id: 'mock_due_${DateTime.now().microsecondsSinceEpoch}',
      title: title,
      dueType: dueType,
      amountPaise: amountPaise,
      dueDate: dueDate,
      frequency: frequency,
      status: 'upcoming',
      isMandatory: isMandatory,
      confidence: 1.0,
    );
    _dues.add(due);
    _dues.sort((a, b) => a.dueDate.compareTo(b.dueDate));
    return due;
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
    await Future.delayed(const Duration(milliseconds: 300));
    final index = _dues.indexWhere((d) => d.id == id);
    if (index < 0) throw StateError('Due not found');
    final updated = _dues[index].copyWith(
      title: title,
      dueType: dueType,
      amountPaise: amountPaise,
      dueDate: dueDate,
      frequency: frequency,
      isMandatory: isMandatory,
      status: status,
    );
    _dues[index] = updated;
    return updated;
  }

  @override
  Future<void> deleteDue(String id) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _dues.removeWhere((d) => d.id == id);
  }

  // ---- Subscriptions ----
  @override
  Future<List<Subscription>> getSubscriptions() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return List<Subscription>.from(_subscriptions);
  }

  @override
  Future<void> confirmSubscription(String subId) async {
    await Future.delayed(const Duration(milliseconds: 300));
    _subscriptions = _subscriptions.map((s) => s.copyWith(isUserConfirmed: true)).toList();
  }

  @override
  Future<void> dismissSubscription(String subId) async {
    await Future.delayed(const Duration(milliseconds: 300));
    _subscriptions.removeWhere((s) => s.id == subId);
  }

  // ---- Nudges ----
  @override
  Future<List<Nudge>> getNudges() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return List<Nudge>.from(_nudges);
  }

  @override
  Future<void> markNudgeRead(String nudgeId) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _nudges = _nudges.map((n) => n.id == nudgeId ? n.copyWith(read: true) : n).toList();
  }

  // ---- Scam ----
  @override
  Future<ScamExplanation> analyzeScam(ScamAnalysisRequest request) async {
    await Future.delayed(const Duration(milliseconds: 700));
    // Deterministic mock scoring based on message content (demo only).
    // Uses supplied indicators when provided (backend-calculated), otherwise detects from message.
    final msg = (request.message ?? '').toLowerCase();
    int score = 0;
    final indicators = <String>[];

    if (request.indicators != null && request.indicators!.isNotEmpty) {
      indicators.addAll(request.indicators!);
      // Estimate score from supplied indicators
      for (final ind in request.indicators!) {
        final lower = ind.toLowerCase();
        if (lower.contains('upi pin') || lower.contains('otp') || lower.contains('pin')) score += 45;
        if (lower.contains('link') || lower.contains('http')) score += 30;
        if (lower.contains('blocked') || lower.contains('suspend') || lower.contains('urgent')) score += 20;
        if (lower.contains('collect') || lower.contains('request money')) score += 25;
      }
    } else {
      if (msg.contains('upi pin') || msg.contains('otp') || msg.contains('pin')) {
        score += 45;
        indicators.add('Requests UPI PIN / OTP');
      }
      if (msg.contains('http') || msg.contains('link') || msg.contains('bit.ly')) {
        score += 30;
        indicators.add('Suspicious external link');
      }
      if (msg.contains('blocked') || msg.contains('suspend') || msg.contains('urgent')) {
        score += 20;
        indicators.add('Urgent account-blocking threat');
      }
      if (msg.contains('collect') || msg.contains('request money')) {
        score += 25;
        indicators.add('Unknown collect request');
      }
    }
    score = score.clamp(0, 100);
    final level = _riskLevel(score);
    return ScamExplanation(
      summary: _scamSummary(level),
      reasons: indicators.isNotEmpty ? indicators : ['No strong indicators detected.'],
      safeAction:
          'Do not share your OTP, UPI PIN or password. Verify via your bank’s official app or customer care.',
    );
  }

  @override
  Future<List<ScamAlert>> getScamAlerts() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return List<ScamAlert>.from(_scamAlerts);
  }

  // ---- Tax ----
  @override
  Future<TaxComparison> compareTax(TaxComparisonRequest request) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return _loader.loadTaxComparison();
  }

  // ---- Business ----
  @override
  Future<BusinessCashflow> getBusinessCashflow() async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _loader.loadBusinessCashflow();
  }

  // ---- Investments ----
  @override
  Future<List<InvestmentSummary>> getInvestmentSummary() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return _loader.loadInvestments();
  }

  // ---- Settings ----
  @override
  Future<bool> getNotificationsEnabled() async => _notificationsEnabled;

  @override
  Future<void> setNotificationsEnabled(bool enabled) async {
    _notificationsEnabled = enabled;
  }

  @override
  Future<int> getWeeklyNudgeCap() async => _weeklyNudgeCap;

  @override
  Future<void> setWeeklyNudgeCap(int cap) async {
    _weeklyNudgeCap = cap.clamp(1, 10);
  }

  String _riskLevel(int score) {
    if (score >= 75) return 'critical';
    if (score >= 50) return 'high';
    if (score >= 25) return 'medium';
    return 'low';
  }

  String _scamSummary(String level) {
    switch (level) {
      case 'critical':
        return 'This message shows strong signs of a phishing attempt and should be treated as unsafe.';
      case 'high':
        return 'This message shows several signs of a possible phishing attempt.';
      case 'medium':
        return 'This message shows some warning signs that deserve caution.';
      default:
        return 'This message has a few minor warning signs, so it is worth a quick check.';
    }
  }
}
