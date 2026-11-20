import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/business_cashflow.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Small-business cash-flow dashboard (shopkeeper persona).
class CashflowScreen extends StatefulWidget {
  const CashflowScreen({super.key});

  @override
  State<CashflowScreen> createState() => _CashflowScreenState();
}

class _CashflowScreenState extends State<CashflowScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  BusinessCashflow? _cashflow;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final cf = await _repo.getBusinessCashflow();
      if (mounted) setState(() { _cashflow = cf; _loading = false; _error = null; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString(); });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Business cash flow')),
      body: _loading
          ? const LoadingState(message: 'Loading cash flow…')
          : _error != null
              ? ErrorState(
                  exception: AppException(code: 'LOAD_ERROR', message: _error!),
                  onRetry: _load,
                )
              : _cashflow == null
              ? const EmptyState(icon: Icons.business_outlined, title: 'No data', message: '')
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Period: ${_cashflow!.period}', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppTheme.onSurfaceVariant)),
                      const SizedBox(height: 20),
                      // Projected cash balance (prominent)
                      Card(
                        color: AppTheme.primaryContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Projected cash balance', style: TextStyle(fontSize: 14, color: AppTheme.primary)),
                              const SizedBox(height: 4),
                              Text(
                                _cashflow!.projectedCashBalance.toInr(),
                                style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w800, color: AppTheme.primary),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Row(
                        children: [
                          Expanded(child: _flowCard('Sales', _cashflow!.sales, AppTheme.success)),
                          Expanded(child: _flowCard('Expenses', _cashflow!.expenses, AppTheme.danger)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(child: _flowCard('Receivables', _cashflow!.receivables, AppTheme.info)),
                          Expanded(child: _flowCard('Payables', _cashflow!.payables, AppTheme.warning)),
                        ],
                      ),
                      const SizedBox(height: 20),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Working capital gap (receivables − payables)', style: TextStyle(fontSize: 13, color: AppTheme.onSurfaceVariant)),
                              const SizedBox(height: 8),
                              Text(
                                Money(_cashflow!.workingCapitalGapPaise).toInrWhole(),
                                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
                              ),
                              const SizedBox(height: 12),
                              const Text('Net operating flow (sales − expenses)', style: TextStyle(fontSize: 13, color: AppTheme.onSurfaceVariant)),
                              const SizedBox(height: 8),
                              Text(
                                Money(_cashflow!.netOperatingFlowPaise).toInrWhole(),
                                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppTheme.warningContainer,
                          borderRadius: BorderRadius.all(Radius.circular(10)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.info_outline, color: AppTheme.warning, size: 18),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                'Shopkeeper persona — synthetic demo data. Not real business banking.',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.warning),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _flowCard(String title, Money value, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontSize: 13, color: AppTheme.onSurfaceVariant)),
            const SizedBox(height: 4),
            Text(value.toInrWhole(), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18, color: color)),
          ],
        ),
      ),
    );
  }
}
