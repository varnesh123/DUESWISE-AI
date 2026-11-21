import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/due.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/features/dues/due_form_sheet.dart';

/// Due detail with edit, delete, and mark-as-paid actions.
class DueDetailScreen extends StatefulWidget {
  final String dueId;
  const DueDetailScreen({super.key, required this.dueId});

  @override
  State<DueDetailScreen> createState() => _DueDetailScreenState();
}

class _DueDetailScreenState extends State<DueDetailScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  Due? _due;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final d = await _repo.getDue(widget.dueId);
      if (mounted) setState(() { _due = d; _loading = false; _error = null; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString(); });
    }
  }

  Future<void> _edit() async {
    final due = _due;
    if (due == null) return;
    final saved = await showDueFormSheet(context, due: due);
    if (saved == true) await _load();
  }

  Future<void> _delete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete due?'),
        content: const Text('This removes the due from your account.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            style: FilledButton.styleFrom(backgroundColor: AppTheme.danger),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _repo.deleteDue(widget.dueId);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Due deleted')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not delete: $e'),
            backgroundColor: AppTheme.danger,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Due details'),
        actions: [
          IconButton(
            onPressed: _due == null ? null : _edit,
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit',
          ),
          IconButton(
            onPressed: _due == null ? null : _delete,
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Delete',
          ),
        ],
      ),
      body: _loading
          ? const LoadingState()
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : _due == null
              ? const EmptyState(
                  icon: Icons.error_outline,
                  title: 'Due not found',
                  message: '',
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  backgroundColor: AppTheme.primaryContainer,
                                  child: const Icon(Icons.payment, color: AppTheme.primary),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    _due!.title,
                                    style: Theme.of(context)
                                        .textTheme
                                        .headlineSmall
                                        ?.copyWith(fontWeight: FontWeight.w700),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            _row(context, 'Amount', _due!.amount.toInr()),
                            _row(context, 'Due date', _due!.dueDate),
                            _row(context, 'Frequency', _due!.frequency),
                            _row(context, 'Type', _due!.dueType.toUpperCase()),
                            _row(context, 'Status', _due!.status.toUpperCase()),
                            _row(context, 'Mandatory', _due!.isMandatory ? 'Yes' : 'No'),
                            if (_due!.confidence != null)
                              _row(
                                context,
                                'Confidence',
                                '${(_due!.confidence! * 100).toStringAsFixed(0)}%',
                              ),
                            const SizedBox(height: 20),
                            if (!_due!.isPaid)
                              SizedBox(
                                width: double.infinity,
                                height: 52,
                                child: FilledButton(
                                  onPressed: () async {
                                    try {
                                      await _repo.markDuePaid(widget.dueId);
                                      if (mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text('Marked as paid')),
                                        );
                                        Navigator.pop(context);
                                      }
                                    } catch (e) {
                                      if (mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(
                                            content: Text('Could not mark as paid: $e'),
                                            backgroundColor: AppTheme.danger,
                                          ),
                                        );
                                      }
                                    }
                                  },
                                  child: const Text('Mark as paid'),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _row(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: TextStyle(color: AppTheme.onSurfaceVariant, fontSize: 13),
            ),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}
