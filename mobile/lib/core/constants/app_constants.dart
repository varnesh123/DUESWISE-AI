/// Central application constants.
library dueswise.core.constants;

class AppConstants {
  AppConstants._();

  static const String appName = 'DuesWise';
  static const String tagline = 'Spend smart, stay ahead';

  // ISO-8601 date / timestamp formats used across the app.
  static const String dateFormat = 'yyyy-MM-dd';
  static const String timestampFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSZ";
  static const String displayDateFormat = 'dd MMM';

  // Timezone used for financial date calculations (Asia/Kolkata).
  static const String timeZone = 'Asia/Kolkata';

  // Default weekly nudge cap (per BLUEPRINT §10.3).
  static const int weeklyNudgeCap = 4;
  static const String quietHoursStart = '22:00';
  static const String quietHoursEnd = '08:00';

  // Enums (CONTRACTS §6 / BLUEPRINT).
  static const List<String> transactionTypes = ['debit', 'credit'];
  static const List<String> paymentMethods = ['UPI', 'card', 'bank_transfer', 'cash', 'other'];
  static const List<String> riskLevels = ['low', 'medium', 'high', 'critical'];
  static const List<String> dueStatuses = ['upcoming', 'due', 'paid', 'overdue'];
  static const List<String> subscriptionStatuses = ['active', 'cancelled', 'paused', 'uncertain'];
  static const List<String> categories = [
    'food',
    'groceries',
    'entertainment',
    'transport',
    'shopping',
    'rent',
    'emi',
    'insurance',
    'utilities',
    'healthcare',
    'education',
    'investments',
    'income',
    'transfers',
    'business',
    'other',
  ];
}
