import 'package:flutter/material.dart';

import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/due.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

const List<String> dueTypes = [
  'rent',
  'emi',
  'insurance',
  'utility',
  'credit_card',
  'subscription',
  'other',
];

const List<String> dueFrequencies = [
  'one_time',
  'weekly',
  'monthly',
  'quarterly',
  'yearly',
];

/// Open the create/edit form. Returns true when a record was saved.
Future<bool?> showDueFormSheet(BuildContext context, {Due? due}) {
  return showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (_) => DueFormSheet(due: due),
  );
}

class DueFormSheet extends StatefulWidget {
  const DueFormSheet({super.key, this.due});

  final Due? due;

  @override
  State<DueFormSheet> createState() => _DueFormSheetState();
}

class _DueFormSheetState extends State<DueFormSheet> {
  final _formKey = GlobalKey<FormState>();
  final FinanceRepository _repo = AppRepository.instance;

  late final TextEditingController _title;
  late final TextEditingController _amount;
  late String _dueType;
  late String _frequency;
  late bool _isMandatory;
  late String _dueDate;
  bool _saving = false;
  String? _error;

  bool get _editing => widget.due != null;

  @override
  void initState() {
    super.initState();
    final due = widget.due;
    _title = TextEditingController(text: due?.title ?? '');
    _amount = TextEditingController(
      text: due == null
          ? ''
          : '${due.amountPaise ~/ 100}.${(due.amountPaise % 100).toString().padLeft(2, '0')}',
    );
    _dueType = dueTypes.contains(due?.dueType) ? due!.dueType : 'rent';
    _frequency =
        dueFrequencies.contains(due?.frequency) ? due!.frequency : 'monthly';
    _isMandatory = due?.isMandatory ?? true;
    _dueDate = due?.dueDate ??
        DateTime.now().add(const Duration(days: 7)).toIso8601String().split('T').first;
  }

  @override
  void dispose() {
    _title.dispose();
    _amount.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final parsed = DateTime.tryParse(_dueDate) ?? DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: parsed,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() => _dueDate = picked.toIso8601String().split('T').first);
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
      final due = widget.due;
      if (due == null) {
        await _repo.createDue(
          title: _title.text.trim(),
          dueType: _dueType,
          amountPaise: paise,
          dueDate: _dueDate,
          frequency: _frequency,
          isMandatory: _isMandatory,
        );
      } else {
        await _repo.updateDue(
          due.id,
          title: _title.text.trim(),
          dueType: _dueType,
          amountPaise: paise,
          dueDate: _dueDate,
          frequency: _frequency,
          isMandatory: _isMandatory,
        );
      }
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _saving = false;
          _error = e is AppException ? e.message : 'Could not save the due.';
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
                      _editing ? 'Edit due' : 'Add a due',
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
                controller: _title,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  labelText: 'Title',
                  hintText: 'Home rent',
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Enter a title' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _amount,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Amount (₹)',
                  hintText: '12000.00',
                ),
                validator: (v) =>
                    parseRupeesToPaise(v ?? '') == null ? 'Enter a valid amount' : null,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _dueType,
                      decoration: const InputDecoration(labelText: 'Type'),
                      items: dueTypes
                          .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                          .toList(),
                      onChanged: (v) => setState(() => _dueType = v ?? _dueType),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _frequency,
                      decoration: const InputDecoration(labelText: 'Frequency'),
                      items: dueFrequencies
                          .map((f) => DropdownMenuItem(value: f, child: Text(f)))
                          .toList(),
                      onChanged: (v) =>
                          setState(() => _frequency = v ?? _frequency),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _pickDate,
                icon: const Icon(Icons.calendar_today_outlined),
                label: Text('Due date: $_dueDate'),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Mandatory payment'),
                subtitle: const Text('Counts toward safe-to-spend'),
                value: _isMandatory,
                onChanged: (v) => setState(() => _isMandatory = v),
              ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(
                  _error!,
                  style: const TextStyle(color: AppTheme.danger),
                ),
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
                      : Text(_editing ? 'Save changes' : 'Add due'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
