import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/data/models/auth_user.dart';
import 'package:dueswise/data/models/dashboard_summary.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Dashboard: balance, safe-to-spend, upcoming dues, recent transactions, nudges.
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  DashboardSummary? _summary;
  List<Transaction> _recent = [];
  AuthUser? _user;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final summary = await _repo.getDashboardSummary();
      final txns = await _repo.getTransactions();
      AuthUser? user;
      try {
        user = await _repo.getCurrentUser();
      } catch (_) {
        // Greeting is optional; financial data still loads.
      }
      if (mounted) {
        setState(() {
          _summary = summary;
          _recent = txns.take(5).toList();
          _user = user;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : () => setState(() => _load()),
            tooltip: 'Refresh',
          ),
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () => context.push(AppRoutes.settings),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const LoadingState(message: 'Loading dashboard…');
    if (_error != null) {
      return ErrorState(
        exception: AppException(code: 'LOAD_ERROR', message: _error!),
        onRetry: _load,
      );
    }
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: _load,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: _buildChildren(),
          ),
        ),
      ),
    );
  }

  List<Widget> _buildChildren() {
    final children = <Widget>[
      Text(
        _user == null || _user!.name.isEmpty ? 'Hello!' : 'Hello, ${_user!.name}',
        style: const TextStyle(fontSize: 16, color: AppTheme.onSurfaceVariant),
      ),
      const SizedBox(height: 4),
      Text(
        _user?.isDemo == true ? 'Demo dashboard' : 'Your dashboard',
        style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w800, color: AppTheme.primary),
      ),
      const SizedBox(height: 20),
      _buildBalanceCard(),
      const SizedBox(height: 20),
    ];

    if (_summary!.nextDue != null) {
      children.add(
        Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: AppTheme.warningContainer,
              child: const Icon(Icons.payment, color: AppTheme.warning, size: 20),
            ),
            title: Text(_summary!.nextDue!.title, style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text('Due ${_summary!.nextDue!.dueDate}'),
            trailing: Text(_summary!.nextDue!.amount.toInrWhole(), style: const TextStyle(fontWeight: FontWeight.w700)),
            onTap: () => context.push('${AppRoutes.dueDetail}${_summary!.nextDue!.id}'),
          ),
        ),
      );
      children.add(const SizedBox(height: 20));
    }

    children.addAll([
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text('Recent transactions', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
          TextButton(
            onPressed: () => context.push(AppRoutes.transactions),
            child: const Text('View all'),
          ),
        ],
      ),
      const SizedBox(height: 8),
    ]);

    if (_recent.isEmpty) {
      children.add(const EmptyState(
        icon: Icons.receipt_long_outlined,
        title: 'No transactions yet',
        message: 'Import or add a transaction to get started.',
      ));
    } else {
      children.addAll(_recent.map((t) => Card(
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
          subtitle: Text('${t.transactionDate} • ${t.displayCategory}'),
          trailing: Text(
            '${t.isCredit ? '+' : '-'}${t.amount.toInrWhole()}',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: t.isCredit ? AppTheme.success : AppTheme.primary,
            ),
          ),
          onTap: () => context.push('${AppRoutes.transactionDetail}${t.id}'),
        ),
      )));
    }

    return children;
  }

  Widget _buildBalanceCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Available balance', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppTheme.onSurfaceVariant)),
                Text(
                  _summary!.availableBalance.toInr(),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700, color: AppTheme.onSurface),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Safe to spend', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppTheme.safeToSpend)),
                Text(
                  _summary!.safeToSpend.toInr(),
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w700, color: AppTheme.safeToSpend),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              _summary!.explanation,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: _statChip('Safe to spend', _summary!.safeToSpend.toInrWhole(), AppTheme.safeToSpend),
                ),
                Expanded(
                  child: _statChip('Upcoming dues', _summary!.upcomingDuesTotal.toInrWhole(), AppTheme.warning),
                ),
                Expanded(
                  child: _statChip('Safety reserve', _summary!.safetyReserve.toInrWhole(), AppTheme.info),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statChip(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.onSurfaceVariant)),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(fontWeight: FontWeight.w700, color: color, fontSize: 16)),
      ],
    );
  }
}
