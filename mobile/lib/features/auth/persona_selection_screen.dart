import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/app/router.dart';
import 'package:dueswise/config/app_config.dart';
import 'package:dueswise/core/constants/app_constants.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/auth_result.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Persona / demo account selection (BLUEPRINT §14).
class PersonaSelectionScreen extends StatefulWidget {
  const PersonaSelectionScreen({super.key});

  @override
  State<PersonaSelectionScreen> createState() => _PersonaSelectionScreenState();
}

class _PersonaSelectionScreenState extends State<PersonaSelectionScreen> {
  DemoPersona _selected = DemoPersona.salaried;
  final FinanceRepository _repo = AppRepository.instance;

  @override
  void initState() {
    super.initState();
    _selected = _repo.selectedPersona;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Choose demo persona')),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 16),
            Text(
              'Pick a demo persona',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              'All data is synthetic. Switch personas anytime from Settings.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: DemoPersona.values.length,
                itemBuilder: (context, index) {
                  final persona = DemoPersona.values[index];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: persona.color.withOpacity(0.15),
                        child: Icon(_icon(persona), color: persona.color),
                      ),
                      title: Text(persona.label, style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text(persona.subtitle),
                      trailing: Radio<DemoPersona>(
                        value: persona,
                        groupValue: _selected,
                        onChanged: (p) => setState(() => _selected = p!),
                      ),
                      onTap: () => setState(() => _selected = persona),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: FilledButton(
                onPressed: () async {
                  await _repo.selectPersona(_selected);
                  if (mounted) context.pushReplacementNamed(AppRoutes.dashboard);
                },
                child: const Text('Continue'),
              ),
            ),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.warningContainer,
                borderRadius: BorderRadius.all(Radius.circular(12)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppTheme.warning, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Demo mode — data is synthetic and reset each session.',
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

  IconData _icon(DemoPersona p) {
    switch (p) {
      case DemoPersona.salaried:
        return Icons.work;
      case DemoPersona.youngProfessional:
        return Icons.person;
      case DemoPersona.shopkeeper:
        return Icons.storefront;
    }
  }
}
