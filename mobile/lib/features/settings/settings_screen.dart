import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Settings: profile, notifications, privacy, demo mode.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  bool _notifications = true;
  int _nudgeCap = AppConstants.weeklyNudgeCap;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final n = await _repo.getNotificationsEnabled();
    final c = await _repo.getWeeklyNudgeCap();
    if (mounted) setState(() { _notifications = n; _nudgeCap = c; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Settings')),
      body: _loading
          ? const LoadingState(message: 'Loading settings…')
          : ListView(
              children: [
                const SizedBox(height: 12),
                // Profile section
                _sectionTitle('Profile'),
                ListTile(
                  leading: const Icon(Icons.person_outline),
                  title: const Text('Demo account'),
                  subtitle: const Text('Synthetic demo user — no real banking'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(AppRoutes.persona),
                ),
                const Divider(height: 1),
                // Notifications
                _sectionTitle('Notifications'),
                SwitchListTile(
                  value: _notifications,
                  onChanged: (v) async {
                    await _repo.setNotificationsEnabled(v);
                    setState(() => _notifications = v);
                  },
                  title: const Text('Enable notifications'),
                  subtitle: const Text('Local demo notifications only'),
                  secondary: const Icon(Icons.notifications_outlined),
                ),
                ListTile(
                  leading: const Icon(Icons.schedule_outlined),
                  title: const Text('Quiet hours'),
                  subtitle: const Text('${AppConstants.quietHoursStart} – ${AppConstants.quietHoursEnd}'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                ListTile(
                  leading: const Icon(Icons.remove_circle_outline),
                  title: const Text('Weekly nudge cap'),
                  subtitle: Text('$_nudgeCap per week'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _editNudgeCap(),
                ),
                const Divider(height: 1),
                // Privacy / demo
                _sectionTitle('Privacy & demo'),
                ListTile(
                  leading: const Icon(Icons.person_outline),
                  title: const Text('Demo mode'),
                  subtitle: const Text('All data is synthetic'),
                  trailing: const Text('ON', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                ),
                ListTile(
                  leading: const Icon(Icons.security_outlined),
                  title: const Text('AI availability'),
                  subtitle: const Text('Deterministic fallbacks active'),
                  trailing: const Icon(Icons.check_circle, color: AppTheme.success),
                ),
                ListTile(
                  leading: const Icon(Icons.description_outlined),
                  title: const Text('Privacy notice'),
                  subtitle: const Text('No OTPs, PINs or passwords are sent anywhere.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                const Divider(height: 1),
                // Actions
                ListTile(
                  leading: const Icon(Icons.logout, color: AppTheme.danger),
                  title: const Text('Log out', style: TextStyle(color: AppTheme.danger)),
                  onTap: () => context.go(AppRoutes.welcome),
                ),
                const SizedBox(height: 20),
              ],
            ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.onSurfaceVariant)),
    );
  }

  Future<void> _editNudgeCap() async {
    final controller = TextEditingController(text: _nudgeCap.toString());
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Weekly nudge cap'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Max nudges per week'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final v = int.tryParse(controller.text) ?? 1;
              _repo.setWeeklyNudgeCap(v.clamp(1, 10));
              setState(() => _nudgeCap = v.clamp(1, 10));
              Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}
