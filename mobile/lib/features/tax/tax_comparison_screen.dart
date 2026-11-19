import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/tax_comparison.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Old vs new tax regime comparison (deterministic mock; never a real engine).
class TaxComparisonScreen extends StatefulWidget {
  const TaxComparisonScreen({super.key});

  @override
  State<TaxComparisonScreen> createState() => _TaxComparisonScreenState();
}

class _TaxComparisonScreenState extends State<TaxComparisonScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  final _income = TextEditingController(text: '600000');
  final _deductions = TextEditingController(text: '50000');
  bool _loading = false;
  TaxComparison? _result;
  String? _error;

  @override
  void dispose() {
    _income.dispose();
    _deductions.dispose();
    super.dispose();
  }

  Future<void> _compare() async {
    final income = int.tryParse(_income.text) ?? 0;
    final deductions = int.tryParse(_deductions.text) ?? 0;
    if (income <= 0) {
      setState(() => _error = 'Enter a valid annual income.');
      return;
    }
    setState(() { _loading = true; _error = null; _result = null; });
    try {
      final result = await _repo.compareTax(TaxComparisonRequest(
        financialYear: '2026-27',
        annualIncomePaise: income * 100,
        deductionsPaise: deductions * 100,
      ));
      if (mounted) setState(() { _result = result; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Tax comparison')),
      body: SafeArea(
        child: Column(
          children: [
            // Input form
            Container(
              color: AppTheme.surface,
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Enter your details', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _income,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Annual income (₹)', hintText: 'e.g. 720000'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _deductions,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Deductions (₹)', hintText: 'e.g. 50000'),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: FilledButton(
                      onPressed: _loading ? null : _compare,
                      child: _loading ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Compare regimes'),
                    ),
                  ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(_error!, style: const TextStyle(color: AppTheme.danger, fontSize: 13)),
                    ),
                ],
              ),
            ),
            const Divider(height: 1),
            // Result
            Expanded(
              child: _loading
                  ? const LoadingState()
                  : _result == null
                      ? const EmptyState(icon: Icons.compare_arrows, title: 'No comparison yet', message: 'Enter income and deductions to compare.')
                      : SingleChildScrollView(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Tax year: ${_result!.taxYear}', style: const TextStyle(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 16),
                              _regimeCard('Old regime', _result!.oldRegime, AppTheme.info),
                              const SizedBox(height: 12),
                              _regimeCard('New regime', _result!.newRegime, AppTheme.primary),
                              const SizedBox(height: 16),
                              Card(
                                color: AppTheme.primaryContainer.withOpacity(0.15),
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          const Text('Recommended', style: TextStyle(fontWeight: FontWeight.w600)),
                                          Text(
                                            _result!.recommendedLowerTaxRegime.toUpperCase(),
                                            style: const TextStyle(fontWeight: FontWeight.w700, color: AppTheme.primary),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          const Text('Estimated difference', style: TextStyle(fontWeight: FontWeight.w600)),
                                          Text(
                                            _result!.estimatedDifference.toInr(),
                                            style: const TextStyle(fontWeight: FontWeight.w700, color: AppTheme.primary),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(height: 12),
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppTheme.warningContainer,
                                  borderRadius: BorderRadius.all(Radius.circular(10)),
                                ),
                                child: Text(
                                  _result!.disclaimer,
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.warning),
                                ),
                              ),
                            ],
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _regimeCard(String title, TaxRegimeResult r, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.all(Radius.circular(6))),
                  child: Text('₹${r.totalTax.toInrWhole().replaceAll('₹', '')}', style: TextStyle(fontWeight: FontWeight.w700, color: color, fontSize: 12)),
                ),
              ],
            ),
            const SizedBox(height: 10),
            _regimeRow('Taxable income', r.taxableIncome.toInrWhole()),
            _regimeRow('Income tax', r.incomeTax.toInrWhole()),
            _regimeRow('Cess', r.cess.toInrWhole()),
            _regimeRow('Total tax', r.totalTax.toInrWhole(), bold: true),
          ],
        ),
      ),
    );
  }

  Widget _regimeRow(String label, String value, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: AppTheme.onSurfaceVariant, fontSize: 13)),
          Text(value, style: TextStyle(fontWeight: bold ? FontWeight.w700 : FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }
}
