import 'package:flutter/material.dart';

import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/transaction.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

const List<String> transactionPaymentMethods = [
  'upi',
  'card',
  'net_banking',
  'cash',
  'other',
];

/// Open the create/edit form. Returns true when a record was saved.
Future<bool?> showTransactionFormSheet(
  BuildContext context, {
  Transaction? transaction,
}) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (_) => TransactionFormSheet(transaction: transaction),
  );
}

class TransactionFormSheet extends StatefulWidget {
  const TransactionFormSheet({super.key, this.transaction});

  final Transaction? transaction;

  @override
  State<TransactionFormSheet> createState() => _TransactionFormSheetState();
}

class _TransactionFormSheetState extends State<TransactionFormSheet> {
  final _formKey = GlobalKey<FormState>();
  final FinanceRepository _repo = AppRepository.instance;

  late final TextEditingController _merchant;
  late final TextEditingController _amount;
  late final TextEditingController _description;
  late String _type;
  late String _category;
  late String _paymentMethod;
  late String _date;
  bool _saving = false;
  String? _error;

  bool get _editing => widget.transaction != null;

  @override
  void initState() {
    super.initState();
    final txn = widget.transaction;
    _merchant = TextEditingController(text: txn?.displayMerchant ?? '');
    _amount = TextEditingController(
      text: txn == null
          ? ''
          : '${txn.amountPaise ~/ 100}.${(txn.amountPaise % 100).toString().padLeft(2, '0')}',
    );
    _description = TextEditingController();
    _type = txn?.transactionType == 'credit' ? 'credit' : 'debit';
    _category = AppConstants.categories.contains(txn?.category)
        ? txn!.category!
        : 'other';
    _paymentMethod = transactionPaymentMethods.contains(txn?.paymentMethod)
        ? txn!.paymentMethod!
        : 'upi';
    _date = txn?.transactionDate ??
        DateTime.now().toIso8601String().split('T').first;
  }

  @override
  void dispose() {
    _merchant.dispose();
    _amount.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final parsed = DateTime.tryParse(_date) ?? DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: parsed,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() => _date = picked.toIso8601String().split('T').first);
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    final paise = parseRupeesToPaise(_amount.text);
    if (paise == null) {
      setState(() => _error = 'Enter a valid amount');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final txn = widget.transaction;
      if (txn == null) {
        await _repo.createTransaction(
          amountPaise: paise,
          transactionType: _type,
          merchant: _merchant.text.trim(),
          category: _category,
          paymentMethod: _paymentMethod,
          transactionDate: _date,
          description: _description.text.trim(),
        );
      } else {
        await _repo.updateTransaction(
          txn.id,
          amountPaise: paise,
          transactionType: _type,
          merchant: _merchant.text.trim(),
          category: _category,
          paymentMethod: _paymentMethod,
          transactionDate: _date,
          description: _description.text.trim(),
        );
      }
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _saving = false;
          _error = e is AppException ? e.message : 'Could not save the transaction.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      _editing ? 'Edit transaction' : 'Add a transaction',
                      style: Theme.of(context)
                          .textTheme
                          .titleLarge
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                    tooltip: 'Close',
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _merchant,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Merchant or description',
                  hintText: 'Grocery store',
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Enter a merchant' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _amount,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Amount (₹)',
                  hintText: '899.00',
                ),
                validator: (v) =>
                    parseRupeesToPaise(v ?? '') == null ? 'Enter a valid amount' : null,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _type,
                      decoration: const InputDecoration(labelText: 'Type'),
                      items: const [
                        DropdownMenuItem(value: 'debit', child: Text('Debit')),
                        DropdownMenuItem(value: 'credit', child: Text('Credit')),
                      ],
                      onChanged: (v) => setState(() => _type = v ?? _type),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _category,
                      decoration: const InputDecoration(labelText: 'Category'),
                      items: AppConstants.categories
                          .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                          .toList(),
                      onChanged: (v) => setState(() => _category = v ?? _category),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _paymentMethod,
                decoration: const InputDecoration(labelText: 'Payment method'),
                items: transactionPaymentMethods
                    .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                    .toList(),
                onChanged: (v) =>
                    setState(() => _paymentMethod = v ?? _paymentMethod),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _pickDate,
                icon: const Icon(Icons.calendar_today_outlined),
                label: Text('Date: $_date'),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _description,
                decoration: const InputDecoration(
                  labelText: 'Note (optional)',
                  hintText: 'Monthly groceries',
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(_error!, style: const TextStyle(color: AppTheme.danger)),
              ],
              const SizedBox(height: 16),
              SizedBox(
                height: 50,
                child: FilledButton(
                  onPressed: _saving ? null : _save,
                  child: _saving
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(_editing ? 'Save changes' : 'Add transaction'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
