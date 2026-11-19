import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/due.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Upcoming dues list with paid/overdue states.
class DueListScreen extends StatefulWidget {
  const DueListScreen({super.key});

  @override
  State<DueListScreen> createState() => _DueListScreenState();
}

class _DueListScreenState extends State<DueListScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  List<Due> _dues = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final dues = await _repo.getDues();
      if (mounted) setState(() { _dues = dues; _loading = false; _error = null; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString(); });
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'overdue':
        return AppTheme.danger;
      case 'due':
        return AppTheme.warning;
      case 'paid':
        return AppTheme.success;
      default:
        return AppTheme.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Upcoming dues')),
      body: _loading
          ? const LoadingState(message: 'Loading dues…')
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : _dues.isEmpty
              ? const EmptyState(icon: Icons.calendar_today_outlined, title: 'No upcoming dues', message: 'All caught up!')
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _dues.length,
                  itemBuilder: (context, i) {
                    final d = _dues[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: _statusColor(d.status).withOpacity(0.15),
                          child: Icon(
                            d.isPaid ? Icons.check_circle : d.isOverdue ? Icons.error : Icons.schedule,
                            color: _statusColor(d.status),
                          ),
                        ),
                        title: Text(d.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Text('${d.dueDate} • ${d.displayCategory}'),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(d.amount.toInrWhole(), style: const TextStyle(fontWeight: FontWeight.w700)),
                            Text(d.status.toUpperCase(), style: TextStyle(fontSize: 10, color: _statusColor(d.status), fontWeight: FontWeight.w600)),
                          ],
                        ),
                        onTap: () => context.push('${AppRoutes.dueDetail}${d.id}'),
                      ),
                    );
                  },
                ),
    );
  }
}
