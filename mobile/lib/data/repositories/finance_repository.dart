/// Repository interface for all application data.
///
/// Implementations: MockFinanceRepository (Phase 5), LiveFinanceRepository (Phase 6).
/// The UI depends only on this interface, never on mock JSON or a concrete API.
import '../models/auth_result.dart';
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
  /// Authentication / demo session.
  Future<AuthResult> login(String email, String password);
  Future<AuthResult> register(String email, String password, String name);
  Future<void> logout();

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

  /// Dues.
  Future<List<Due>> getDues();
  Future<Due> getDue(String id);
  Future<void> markDuePaid(String dueId);

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
