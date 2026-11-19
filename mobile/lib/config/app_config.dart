/// DuesWise application configuration.
///
/// USE_MOCK_API controls whether the app uses the mock repository
/// (independent demos) or the live backend (Phase 6).
///
/// BACKEND_BASE_URL controls the live backend host. It must be overridden
/// for Android emulator development because `localhost` is not reachable
/// from the emulator — use `10.0.2.2` instead. For a physical device, use
/// the machine's LAN IP.
///
/// Override at build time with:
///   flutter run --dart-define=USE_MOCK_API=false
///   flutter run --dart-define=BACKEND_BASE_URL=http://10.0.2.2:8000
class AppConfig {
  AppConfig._();

  /// Whether to use the mock repository instead of the live backend.
  ///
  /// Defaults to `true` so the app works without any backend service.
  static const bool useMockApi = bool.fromEnvironment(
    'USE_MOCK_API',
    defaultValue: true,
  );

  /// Base URL of the DuesWise financial backend (Developer A).
  ///
  /// Override at build time with `--dart-define=BACKEND_BASE_URL=...`.
  ///
  /// Defaults:
  /// - Android emulator: pass `http://10.0.2.2:8000` (localhost is not
  ///   reachable from the emulator).
  /// - Physical device: pass the machine's LAN IP, e.g.
  ///   `http://192.168.1.42:8000`.
  /// - Desktop / web / iOS simulator: `http://localhost:8000` (default).
  static const String backendBaseUrl = String.fromEnvironment(
    'BACKEND_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const String apiBaseUrl = '$backendBaseUrl/api/v1';

  /// Base URL of the independent AI service (Developer B).
  ///
  /// Flutter must NOT call this service directly. The main backend calls
  /// the AI service. This value is documented only for completeness and
  /// must not be used by Flutter code.
  static const String aiServiceBaseUrl = 'http://localhost:8001/api/v1/ai';

  /// Demo mode banner label shown in settings.
  static const bool demoMode = true;

  /// Whether a live backend URL has been explicitly configured.
  static bool get isLiveBackendConfigured =>
      backendBaseUrl.isNotEmpty && backendBaseUrl != 'http://localhost:8000';
}
