import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/features/auth/login_screen.dart';
import 'package:dueswise/features/auth/persona_selection_screen.dart';
import 'package:dueswise/features/auth/welcome_screen.dart';
import 'package:dueswise/features/dashboard/dashboard_screen.dart';
import 'package:dueswise/features/transactions/transaction_list_screen.dart';
import 'package:dueswise/features/transactions/transaction_detail_screen.dart';
import 'package:dueswise/features/dues/due_list_screen.dart';
import 'package:dueswise/features/dues/due_detail_screen.dart';
import 'package:dueswise/features/subscriptions/subscription_list_screen.dart';
import 'package:dueswise/features/insights/nudge_list_screen.dart';
import 'package:dueswise/features/scam_detection/scam_analysis_screen.dart';
import 'package:dueswise/features/tax/tax_comparison_screen.dart';
import 'package:dueswise/features/business/cashflow_screen.dart';
import 'package:dueswise/features/investments/investment_screen.dart';
import 'package:dueswise/features/settings/settings_screen.dart';

class DuesWiseApp extends StatelessWidget {
  const DuesWiseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: AppConstants.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: _router,
    );
  }
}

final GoRouter _router = GoRouter(
  initialLocation: '/welcome',
  routes: [
    GoRoute(path: '/welcome', builder: (_, __) => const WelcomeScreen()),
    GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
    GoRoute(path: '/persona', builder: (_, __) => const PersonaSelectionScreen()),
    GoRoute(path: '/dashboard', builder: (_, __) => const DashboardScreen()),
    GoRoute(path: '/transactions', builder: (_, __) => const TransactionListScreen()),
    GoRoute(
      path: '/transactions/:id',
      builder: (_, state) => TransactionDetailScreen(transactionId: state.pathParameters['id']!),
    ),
    GoRoute(path: '/dues', builder: (_, __) => const DueListScreen()),
    GoRoute(path: '/dues/:id', builder: (_, state) => DueDetailScreen(dueId: state.pathParameters['id']!)),
    GoRoute(path: '/subscriptions', builder: (_, __) => const SubscriptionListScreen()),
    GoRoute(path: '/insights', builder: (_, __) => const NudgeListScreen()),
    GoRoute(path: '/scam', builder: (_, __) => const ScamAnalysisScreen()),
    GoRoute(path: '/tax', builder: (_, __) => const TaxComparisonScreen()),
    GoRoute(path: '/business', builder: (_, __) => const CashflowScreen()),
    GoRoute(path: '/investments', builder: (_, __) => const InvestmentScreen()),
    GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
  ],
);
