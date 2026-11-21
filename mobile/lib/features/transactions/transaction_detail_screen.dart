import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/features/transactions/transaction_form_sheet.dart';

/// Transaction detail with edit and delete actions.
class TransactionDetailScreen extends StatefulWidget {
  const TransactionDetailScreen({super.key, required this.transactionId});

  final String transactionId;

  @override
  State<TransactionDetailScreen> createState() => _TransactionDetailScreenState();
}

class _TransactionDetailScreenState extends State<TransactionDetailScreen> {
  final FinanceRepository _repo = AppRepository.instance;

  Future<Transaction?> _loadTransaction() async {
    final list = await _repo.getTransactions();
    return list.where((t) => t.id == widget.transactionId).firstOrNull;
  }

  Future<void> _edit() async {
    try {
      final txn = await _loadTransaction();
      if (txn == null) return;
      if (!mounted) return;
      final saved = await showTransactionFormSheet(context, transaction: txn);
      if (saved == true && mounted) setState(() {});
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not load transaction: $e'),
            backgroundColor: AppTheme.danger,
          ),
        );
      }
    }
  }

  Future<void> _delete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete transaction?'),
        content: const Text('This removes the record from your account.'),
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
      await _repo.deleteTransaction(widget.transactionId);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Transaction deleted')),
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
        title: const Text('Transaction details'),
        actions: [
          IconButton(
            onPressed: _edit,
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit',
          ),
          IconButton(
            onPressed: _delete,
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Delete',
          ),
        ],
      ),
      body: FutureBuilder<Transaction?>(
        future: _loadTransaction(),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingState();
          if (snap.hasError) {
            return ErrorState(
              exception: AppException(code: 'ERR', message: snap.error.toString()),
              onRetry: () => setState(() {}),
            );
          }
          final txn = snap.data;
          if (txn == null) {
            return const EmptyState(
              icon: Icons.error_outline,
              title: 'Transaction not found',
              message: 'It may have been deleted.',
            );
          }
          return ListView(
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
                            child: Icon(
                              txn.isCredit ? Icons.arrow_downward : Icons.arrow_upward,
                              color: txn.isCredit ? AppTheme.success : AppTheme.primary,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              txn.displayMerchant,
                              style: Theme.of(context)
                                  .textTheme
                                  .headlineSmall
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      _row(context, 'Amount', '${txn.isCredit ? '+' : '-'}${txn.amount.toInr()}'),
                      _row(context, 'Type', txn.transactionType.toUpperCase()),
                      _row(context, 'Category', txn.displayCategory),
                      _row(context, 'Payment method', txn.paymentMethod ?? '—'),
                      if (txn.paymentApp != null) _row(context, 'Payment app', txn.paymentApp!),
                      if (txn.gateway != null) _row(context, 'Gateway', txn.gateway!),
                      _row(context, 'Date', txn.transactionDate),
                      _row(context, 'Source', txn.source ?? '—'),
                      if (txn.confidence != null)
                        _row(context, 'Confidence', '${(txn.confidence! * 100).toStringAsFixed(0)}%'),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
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
            width: 120,
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
