/// Repository interface for all application data.
///
/// Implementations: MockFinanceRepository (Phase 5), LiveFinanceRepository (Phase 6).
/// The UI depends only on this interface, never on mock JSON or a concrete API.
import '../models/auth_result.dart';
import '../models/auth_user.dart';
import '../models/dashboard_summary.dart';
import '../models/business_cashflow.dart';
import '../models/due.dart';
import '../models/investment_summary.dart';
import '../models/nudge.dart';
import '../models/scam_alert.dart';
import '../models/subscription.dart';
import '../models/tax_comparison.dart';
import '../models/transaction.dart';

abstract class FinanceRepository {
  /// Real account authentication.
  Future<AuthResult> login(String email, String password);
  Future<AuthResult> register(String email, String password, String name);
  Future<void> logout();
  Future<AuthUser> getCurrentUser();

  /// Explicit demo session (separate from real login).
  Future<AuthResult> loginDemo(DemoPersona persona);

  /// Currently selected demo persona.
  DemoPersona get selectedPersona;
  Future<void> selectPersona(DemoPersona persona);
  List<DemoPersona> get availablePersonas;

  /// Dashboard.
  Future<DashboardSummary> getDashboardSummary();
  Future<void> refreshDashboard();

  /// Transactions.
  Future<List<Transaction>> getTransactions({String? category, String? query});
  Future<IngestedTransaction> ingestTransaction(Map<String, dynamic> payload);
  Future<Transaction> createTransaction({
    required int amountPaise,
    required String transactionType,
    required String merchant,
    String? category,
    String paymentMethod = 'upi',
    String? transactionDate,
    String? description,
  });
  Future<Transaction> updateTransaction(
    String id, {
    int? amountPaise,
    String? transactionType,
    String? merchant,
    String? category,
    String? paymentMethod,
    String? transactionDate,
    String? description,
  });
  Future<void> deleteTransaction(String id);

  /// Dues.
  Future<List<Due>> getDues();
  Future<Due> getDue(String id);
  Future<void> markDuePaid(String dueId);
  Future<Due> createDue({
    required String title,
    required String dueType,
    required int amountPaise,
    required String dueDate,
    String frequency = 'monthly',
    bool isMandatory = true,
  });
  Future<Due> updateDue(
    String id, {
    String? title,
    String? dueType,
    int? amountPaise,
    String? dueDate,
    String? frequency,
    bool? isMandatory,
    String? status,
  });
  Future<void> deleteDue(String id);

  /// Subscriptions.
  Future<List<Subscription>> getSubscriptions();
  Future<void> confirmSubscription(String subId);
  Future<void> dismissSubscription(String subId);

  /// Nudges / insights.
  Future<List<Nudge>> getNudges();
  Future<void> markNudgeRead(String nudgeId);

  /// Scam.
  Future<ScamExplanation> analyzeScam(ScamAnalysisRequest request);
  Future<List<ScamAlert>> getScamAlerts();

  /// Tax.
  Future<TaxComparison> compareTax(TaxComparisonRequest request);

  /// Business cash flow.
  Future<BusinessCashflow> getBusinessCashflow();

  /// Investments (simulated).
  Future<List<InvestmentSummary>> getInvestmentSummary();

  /// Settings / notifications.
  Future<bool> getNotificationsEnabled();
  Future<void> setNotificationsEnabled(bool enabled);
  Future<int> getWeeklyNudgeCap();
  Future<void> setWeeklyNudgeCap(int cap);
}
