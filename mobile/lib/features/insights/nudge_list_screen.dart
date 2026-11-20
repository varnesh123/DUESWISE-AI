import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/nudge.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Nudge / AI insights list with read/unread state.
class NudgeListScreen extends StatefulWidget {
  const NudgeListScreen({super.key});

  @override
  State<NudgeListScreen> createState() => _NudgeListScreenState();
}

class _NudgeListScreenState extends State<NudgeListScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  List<Nudge> _nudges = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final nudges = await _repo.getNudges();
      if (mounted) setState(() { _nudges = nudges; _loading = false; _error = null; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString(); });
    }
  }

  Color _priorityColor(String p) {
    switch (p) {
      case 'high':
        return AppTheme.danger;
      case 'medium':
        return AppTheme.warning;
      default:
        return AppTheme.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Insights & nudges')),
      body: _loading
          ? const LoadingState(message: 'Loading nudges…')
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : _nudges.isEmpty
              ? const EmptyState(icon: Icons.lightbulb_outline, title: 'No nudges', message: 'Insights appear when relevant.')
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _nudges.length,
                  itemBuilder: (context, i) {
                    final n = _nudges[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      color: n.read ? null : AppTheme.primaryContainer.withOpacity(0.08),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: _priorityColor(n.priority).withOpacity(0.15),
                          child: Icon(Icons.lightbulb, color: _priorityColor(n.priority)),
                        ),
                        title: Text(n.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(n.message),
                            const SizedBox(height: 4),
                            Text('${n.priority.toUpperCase()} priority • ${n.createdAt}', style: const TextStyle(fontSize: 11, color: AppTheme.onSurfaceVariant)),
                          ],
                        ),
                        trailing: Icon(n.read ? Icons.check_circle : Icons.radio_button_unchecked, color: n.read ? AppTheme.success : AppTheme.onSurfaceVariant),
                        onTap: () => _markRead(n),
                      ),
                    );
                  },
                ),
    );
  }

  Future<void> _markRead(Nudge n) async {
    if (n.read) return;
    try {
      await _repo.markNudgeRead(n.id);
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not mark as read: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }
}
