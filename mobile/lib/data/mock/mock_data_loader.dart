/// Mock data loader: reads bundled JSON fixtures and parses them into models.
/// Used by MockFinanceRepository. Never used by widgets directly.
import 'dart:convert';

import 'package:flutter/services.dart';

import '../models/auth_result.dart';
import '../models/business_cashflow.dart';
import '../models/dashboard_summary.dart';
import '../models/investment_summary.dart';
import '../models/nudge.dart';
import '../models/scam_alert.dart';
import '../models/subscription.dart';
import '../models/tax_comparison.dart';
import '../models/due.dart';
import '../models/transaction.dart';

class MockDataLoader {
  MockDataLoader._();
  static final MockDataLoader instance = MockDataLoader._();

  static const String _dir = 'assets/mock_data';

  Future<Map<String, dynamic>> _load(String file) async {
    final jsonString = await rootBundle.loadString('$_dir/$file.json');
    final decoded = jsonDecode(jsonString) as Map<String, dynamic>;
    return decoded;
  }

  Future<DashboardSummary> loadDashboard(DemoPersona persona) async {
    final file = 'dashboard_persona_${persona.name}';
    final json = await _load(file);
    return DashboardSummary.fromJson(json);
  }

  Future<List<Transaction>> loadTransactions() async {
    final json = await _load('transactions');
    final list = json['transactions'] as List<dynamic>? ?? [];
    return list.map((e) => Transaction.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<List<Due>> loadDues() async {
    final json = await _load('dues');
    final list = json['dues'] as List<dynamic>? ?? [];
    return list.map((e) => Due.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<List<Subscription>> loadSubscriptions() async {
    final json = await _load('subscriptions');
    final list = json['subscriptions'] as List<dynamic>? ?? [];
    return list.map((e) => Subscription.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<List<Nudge>> loadNudges() async {
    final json = await _load('nudges');
    final list = json['nudges'] as List<dynamic>? ?? [];
    return list.map((e) => Nudge.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<List<ScamAlert>> loadScamAlerts() async {
    final json = await _load('scam_alerts');
    final list = json['scam_alerts'] as List<dynamic>? ?? [];
    return list.map((e) => ScamAlert.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<TaxComparison> loadTaxComparison() async {
    final json = await _load('tax_comparison');
    return TaxComparison.fromJson(json);
  }

  Future<BusinessCashflow> loadBusinessCashflow() async {
    final json = await _load('business_cashflow');
    return BusinessCashflow.fromJson(json);
  }

  Future<List<InvestmentSummary>> loadInvestments() async {
    final json = await _load('investments');
    final list = json['investments'] as List<dynamic>? ?? [];
    return list.map((e) => InvestmentSummary.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }
}
