import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

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
    setState(() => _filtered = result);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Transactions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.file_upload_outlined),
            onPressed: () => _showIngestDialog(context),
            tooltip: 'Import transaction',
          ),
        ],
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
                      ? const EmptyState(
                          icon: Icons.receipt_long_outlined,
                          title: 'No matching transactions',
                          message: 'Try a different search or category filter.',
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

  Future<void> _showIngestDialog(BuildContext context) async {
    final merchant = TextEditingController();
    final amount = TextEditingController();
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Import transaction (demo)'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: merchant, decoration: const InputDecoration(labelText: 'Merchant', hintText: 'NETFLIX')),
            const SizedBox(height: 12),
            TextField(controller: amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Amount (₹)', hintText: '899')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final a = int.tryParse(amount.text) ?? 0;
              Navigator.pop(context, {'merchant_raw': merchant.text, 'amount_paise': a * 100, 'transaction_type': 'debit', 'category': 'other'});
            },
            child: const Text('Import'),
          ),
        ],
      ),
    );
    if (result != null && mounted) {
      try {
        await _repo.ingestTransaction(result);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Transaction imported')));
        _load();
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Import failed: $e'), backgroundColor: AppTheme.danger));
      }
    }
  }
}
