import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';
import 'package:dueswise/core/errors/app_exception.dart';

/// Transaction detail screen.
class TransactionDetailScreen extends StatelessWidget {
  final String transactionId;
  TransactionDetailScreen({super.key, required this.transactionId});

  final FinanceRepository _repo = AppRepository.instance;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Transaction details')),
      body: FutureBuilder<Transaction?>(
        future: _repo.getTransactions().then(
              (list) => list.where((t) => t.id == transactionId).firstOrNull,
        ),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingState();
          if (snap.hasError) {
            return ErrorState(
              exception: AppException(code: 'ERR', message: snap.error.toString()),
              onRetry: () {},
            );
          }
          final txn = snap.data;
          if (txn == null) {
            return const EmptyState(
              icon: Icons.error_outline,
              title: 'Transaction not found',
              message: '',
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
