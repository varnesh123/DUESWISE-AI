import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/subscription.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Active subscriptions list with confirm/dismiss.
class SubscriptionListScreen extends StatefulWidget {
  const SubscriptionListScreen({super.key});

  @override
  State<SubscriptionListScreen> createState() => _SubscriptionListScreenState();
}

class _SubscriptionListScreenState extends State<SubscriptionListScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  List<Subscription> _subs = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final subs = await _repo.getSubscriptions();
      if (mounted) setState(() { _subs = subs; _loading = false; _error = null; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString(); });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Subscriptions')),
      body: _loading
          ? const LoadingState(message: 'Loading subscriptions…')
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : _subs.isEmpty
              ? const EmptyState(icon: Icons.subscriptions_outlined, title: 'No subscriptions', message: 'Detected subscriptions appear here.')
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _subs.length,
                  itemBuilder: (context, i) {
                    final s = _subs[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: AppTheme.primaryContainer,
                          child: const Icon(Icons.subscriptions, color: AppTheme.primary),
                        ),
                        title: Text(s.merchant, style: const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Text('${s.nextDueDate} • ${s.frequency} • ${s.displayCategory}'),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(s.expectedAmount.toInrWhole(), style: const TextStyle(fontWeight: FontWeight.w700)),
                            Text(s.isUserConfirmed ? 'Confirmed' : 'Detected', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600)),
                          ],
                        ),
                        onTap: () => _showActions(context, s),
                      ),
                    );
                  },
                ),
    );
  }

  void _showActions(BuildContext context, Subscription s) {
    showModalBottomSheet(
      context: context,
      builder: (sheetContext) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.check_circle, color: AppTheme.success),
            title: const Text('Confirm subscription'),
            onTap: () async {
              Navigator.pop(sheetContext);
              try {
                await _repo.confirmSubscription(s.id);
                await _load();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Could not confirm: $e'), backgroundColor: AppTheme.danger),
                  );
                }
              }
            },
          ),
          ListTile(
            leading: const Icon(Icons.delete_outline, color: AppTheme.danger),
            title: const Text('Dismiss detection'),
            onTap: () async {
              Navigator.pop(sheetContext);
              try {
                await _repo.dismissSubscription(s.id);
                await _load();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Could not dismiss: $e'), backgroundColor: AppTheme.danger),
                  );
                }
              }
            },
          ),
        ],
      ),
    );
  }
}

extension on Subscription {
  String get displayCategory => category
      .split('_')
      .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '')
      .join(' ');
}
