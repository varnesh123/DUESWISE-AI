import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/features/transactions/transaction_form_sheet.dart';

/// Transaction list with search + category filter.
class TransactionListScreen extends StatefulWidget {
  const TransactionListScreen({super.key});

  @override
  State<TransactionListScreen> createState() => _TransactionListScreenState();
}

class _TransactionListScreenState extends State<TransactionListScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  List<Transaction> _transactions = [];
  List<Transaction> _filtered = [];
  String? _categoryFilter;
  String _query = '';
  String _sort = 'date_desc';
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final txns = await _repo.getTransactions();
      if (mounted) {
        setState(() {
          _transactions = txns;
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
    var result = _transactions;
    if (_categoryFilter != null && _categoryFilter!.isNotEmpty) {
      result = result.where((t) => t.category == _categoryFilter).toList();
    }
    if (_query.isNotEmpty) {
      final q = _query.toLowerCase();
      result = result.where((t) => t.displayMerchant.toLowerCase().contains(q) || (t.category ?? '').toLowerCase().contains(q)).toList();
    }
    switch (_sort) {
      case 'date_asc':
        result = [...result]
          ..sort((a, b) => a.transactionDate.compareTo(b.transactionDate));
        break;
      case 'amount_desc':
        result = [...result]
          ..sort((a, b) => b.amountPaise.compareTo(a.amountPaise));
        break;
      case 'amount_asc':
        result = [...result]
          ..sort((a, b) => a.amountPaise.compareTo(b.amountPaise));
        break;
      default:
        result = [...result]
          ..sort((a, b) => b.transactionDate.compareTo(a.transactionDate));
    }
    setState(() => _filtered = result);
  }

  Future<void> _addTransaction() async {
    final saved = await showTransactionFormSheet(context);
    if (saved == true) await _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Transactions'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort),
            tooltip: 'Sort transactions',
            initialValue: _sort,
            onSelected: (value) => setState(() {
              _sort = value;
              _applyFilters();
            }),
            itemBuilder: (context) => const [
              PopupMenuItem(value: 'date_desc', child: Text('Newest first')),
              PopupMenuItem(value: 'date_asc', child: Text('Oldest first')),
              PopupMenuItem(value: 'amount_desc', child: Text('Amount: high to low')),
              PopupMenuItem(value: 'amount_asc', child: Text('Amount: low to high')),
            ],
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loading ? null : _addTransaction,
        icon: const Icon(Icons.add),
        label: const Text('Add'),
      ),
      body: _loading
          ? const LoadingState(message: 'Loading transactions…')
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : Column(
              children: [
                // Filter bar
                Container(
                  padding: const EdgeInsets.all(12),
                  color: AppTheme.surface,
                  child: Column(
                    children: [
                      TextField(
                        decoration: const InputDecoration(
                          labelText: 'Search merchant or category',
                          prefixIcon: Icon(Icons.search),
                          isDense: true,
                        ),
                        onChanged: (v) => setState(() { _query = v; _applyFilters(); }),
                      ),
                      const SizedBox(height: 10),
                      SizedBox(
                        height: 36,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: AppConstants.categories.length,
                          itemBuilder: (context, i) {
                            final cat = AppConstants.categories[i];
                            return Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: CategoryChip(
                                category: cat,
                                selected: _categoryFilter == cat,
                                onTap: () => setState(() {
                                  _categoryFilter = _categoryFilter == cat ? null : cat;
                                  _applyFilters();
                                }),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
                // List
                Expanded(
                  child: _filtered.isEmpty
                      ? EmptyState(
                          icon: Icons.receipt_long_outlined,
                          title: _transactions.isEmpty
                              ? 'No transactions yet'
                              : 'No matching transactions',
                          message: _transactions.isEmpty
                              ? 'Add your first transaction with the + button.'
                              : 'Try a different search, category, or sort.',
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _filtered.length,
                          itemBuilder: (context, i) {
                            final t = _filtered[i];
                            return Card(
                              margin: const EdgeInsets.only(bottom: 8),
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: AppTheme.primaryContainer,
                                  child: Icon(
                                    t.isCredit ? Icons.arrow_downward : Icons.arrow_upward,
                                    color: t.isCredit ? AppTheme.success : AppTheme.primary,
                                  ),
                                ),
                                title: Text(t.displayMerchant, style: const TextStyle(fontWeight: FontWeight.w600)),
                                subtitle: Text('${t.transactionDate} • ${t.source ?? 'sms'} • ${t.displayCategory}'),
                                trailing: Text(
                                  '${t.isCredit ? '+' : '-'}${t.amount.toInrWhole()}',
                                  style: TextStyle(fontWeight: FontWeight.w700, color: t.isCredit ? AppTheme.success : AppTheme.primary),
                                ),
                                onTap: () => context.push('${AppRoutes.transactionDetail}${t.id}'),
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
