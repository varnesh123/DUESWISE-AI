/// Repository provider.
///
/// Holds the single repository instance shared across the app.
///
/// Phase 5 used MockFinanceRepository; Phase 6 can swap in
/// LiveFinanceRepository here without touching any UI code.
///
/// The implementation is chosen by AppConfig.useMockApi (default true),
/// overridable at build time with --dart-define=USE_MOCK_API=false.
import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/data/live/live_finance_repository.dart';
import 'package:dueswise/data/mock/mock_finance_repository.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

class AppRepository {
  static FinanceRepository _instance = _createRepository();

  static FinanceRepository get instance => _instance;

  static FinanceRepository _createRepository() {
    if (AppConfig.useMockApi) {
      return MockFinanceRepository();
    }
    return LiveFinanceRepository();
  }

  /// Switch the repository implementation at runtime (primarily for testing).
  static void setRepository(FinanceRepository repository) {
    _instance = repository;
  }
}
