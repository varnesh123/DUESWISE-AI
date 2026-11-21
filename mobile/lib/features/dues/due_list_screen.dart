import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/due.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/features/dues/due_form_sheet.dart';

/// Upcoming dues list with search, status filter, sort, and add/edit actions.
class DueListScreen extends StatefulWidget {
  const DueListScreen({super.key});

  @override
  State<DueListScreen> createState() => _DueListScreenState();
}

class _DueListScreenState extends State<DueListScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  List<Due> _dues = [];
  List<Due> _filtered = [];
  String _query = '';
  String? _statusFilter;
  String _sort = 'date_asc';
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
      if (mounted) {
        setState(() {
          _dues = dues;
          _applyFilters();
          _loading = false;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString(); });
    }
  }

  void _applyFilters() {
    var result = _dues;
    if (_statusFilter != null) {
      result = result.where((d) => d.status == _statusFilter).toList();
    }
    if (_query.isNotEmpty) {
      final q = _query.toLowerCase();
      result = result
          .where((d) =>
              d.title.toLowerCase().contains(q) ||
              d.dueType.toLowerCase().contains(q))
          .toList();
    }
    switch (_sort) {
      case 'date_desc':
        result = [...result]..sort((a, b) => b.dueDate.compareTo(a.dueDate));
        break;
      case 'amount_desc':
        result = [...result]..sort((a, b) => b.amountPaise.compareTo(a.amountPaise));
        break;
      default:
        result = [...result]..sort((a, b) => a.dueDate.compareTo(b.dueDate));
    }
    _filtered = result;
  }

  Future<void> _addDue() async {
    final saved = await showDueFormSheet(context);
    if (saved == true) await _load();
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
      appBar: AppBar(
        title: const Text('Upcoming dues'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort),
            tooltip: 'Sort dues',
            initialValue: _sort,
            onSelected: (value) => setState(() {
              _sort = value;
              _applyFilters();
            }),
            itemBuilder: (context) => const [
              PopupMenuItem(value: 'date_asc', child: Text('Due soonest')),
              PopupMenuItem(value: 'date_desc', child: Text('Due latest')),
              PopupMenuItem(value: 'amount_desc', child: Text('Amount: high to low')),
            ],
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loading ? null : _addDue,
        icon: const Icon(Icons.add),
        label: const Text('Add'),
      ),
      body: _loading
          ? const LoadingState(message: 'Loading dues…')
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      color: AppTheme.surface,
                      child: Column(
                        children: [
                          TextField(
                            decoration: const InputDecoration(
                              labelText: 'Search dues',
                              prefixIcon: Icon(Icons.search),
                              isDense: true,
                            ),
                            onChanged: (v) => setState(() {
                              _query = v;
                              _applyFilters();
                            }),
                          ),
                          const SizedBox(height: 10),
                          SizedBox(
                            height: 36,
                            child: ListView(
                              scrollDirection: Axis.horizontal,
                              children: [
                                for (final status in <String?>[
                                  null,
                                  'upcoming',
                                  'due',
                                  'overdue',
                                  'paid',
                                ])
                                  Padding(
                                    padding: const EdgeInsets.only(right: 8),
                                    child: ChoiceChip(
                                      label: Text(status == null
                                          ? 'All'
                                          : status[0].toUpperCase() + status.substring(1)),
                                      selected: _statusFilter == status,
                                      onSelected: (_) => setState(() {
                                        _statusFilter = status;
                                        _applyFilters();
                                      }),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: _filtered.isEmpty
                          ? EmptyState(
                              icon: Icons.calendar_today_outlined,
                              title: _dues.isEmpty ? 'No dues yet' : 'No matching dues',
                              message: _dues.isEmpty
                                  ? 'Add rent, EMIs, or bills to see them here.'
                                  : 'Try a different search or status filter.',
                            )
                          : ListView.builder(
                              padding: const EdgeInsets.all(16),
                              itemCount: _filtered.length,
                              itemBuilder: (context, i) {
                                final d = _filtered[i];
                                return Card(
                                  margin: const EdgeInsets.only(bottom: 12),
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: _statusColor(d.status).withValues(alpha: 0.15),
                                      child: Icon(
                                        d.isPaid ? Icons.check_circle : d.isOverdue ? Icons.error : Icons.schedule,
                                        color: _statusColor(d.status),
                                      ),
                                    ),
                                    title: Text(d.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                                    subtitle: Text('${d.dueDate} • ${d.displayCategory} • ${d.frequency}'),
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
                    ),
                  ],
                ),
    );
  }
}
