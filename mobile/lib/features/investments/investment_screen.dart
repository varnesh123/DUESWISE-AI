import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/investment_summary.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Simulated educational investment / SIP section (never real trading).
class InvestmentScreen extends StatefulWidget {
  const InvestmentScreen({super.key});

  @override
  State<InvestmentScreen> createState() => _InvestmentScreenState();
}

class _InvestmentScreenState extends State<InvestmentScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  List<InvestmentSummary> _investments = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final inv = await _repo.getInvestmentSummary();
    if (mounted) setState(() { _investments = inv; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Investments & SIP')),
      body: _loading
          ? const LoadingState(message: 'Loading investments…')
          : _investments.isEmpty
              ? const EmptyState(icon: Icons.show_chart_outlined, title: 'No investments', message: '')
              : Column(
                  children: [
                    Container(
                      color: AppTheme.surface,
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Simulated portfolio', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 4),
                          Text('Educational only — no real money is invested.', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.onSurfaceVariant)),
                        ],
                      ),
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _investments.length,
                        itemBuilder: (context, i) {
                          final inv = _investments[i];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: AppTheme.primaryContainer,
                                child: const Icon(Icons.savings, color: AppTheme.primary),
                              ),
                              title: Text(inv.label, style: const TextStyle(fontWeight: FontWeight.w600)),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${inv.assetClass} • ${inv.returnPercent.toStringAsFixed(1)}% return', style: const TextStyle(fontSize: 12)),
                                  Text(inv.note, style: const TextStyle(fontSize: 11, color: AppTheme.onSurfaceVariant, fontStyle: FontStyle.italic)),
                                ],
                              ),
                              trailing: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text(inv.currentValue.toInrWhole(), style: const TextStyle(fontWeight: FontWeight.w700)),
                                  Text(
                                    '${inv.isGain ? '+' : ''}${inv.gainLoss.toInrWhole()}',
                                    style: TextStyle(fontSize: 12, color: inv.isGain ? AppTheme.success : AppTheme.danger, fontWeight: FontWeight.w600),
                                  ),
                                ],
                              ),
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
