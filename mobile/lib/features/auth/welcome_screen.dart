import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/app.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';

/// Welcome screen: entry point with demo/persona selection.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.account_balance_wallet, size: 96, color: AppTheme.primary),
                const SizedBox(height: 24),
                Text(
                  'DuesWise',
                  style: Theme.of(context).textTheme.displayLarge?.copyWith(fontWeight: FontWeight.w800, color: AppTheme.primary),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  AppConstants.tagline,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(color: AppTheme.onSurfaceVariant),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                Text(
                  'AI-powered personal finance for India.\nSafe-to-spend, dues, nudges — all synthetic demo data.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.onSurfaceVariant),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                FilledButton.icon(
                  onPressed: () => context.push(AppRoutes.login),
                  icon: const Icon(Icons.login),
                  label: const Text('Log in'),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () => context.push(AppRoutes.register),
                  icon: const Icon(Icons.person_add),
                  label: const Text('Create account'),
                ),
                const SizedBox(height: 12),
                TextButton.icon(
                  onPressed: () => context.push(AppRoutes.persona),
                  icon: const Icon(Icons.person_outlined),
                  label: const Text('Continue with demo data'),
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.warningContainer,
                    borderRadius: BorderRadius.all(Radius.circular(12)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline, color: AppTheme.warning, size: 20),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Demo mode — all data is synthetic. No real banking.',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.warning),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
