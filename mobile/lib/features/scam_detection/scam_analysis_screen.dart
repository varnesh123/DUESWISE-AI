import 'package:flutter/material.dart';
import 'package:dueswise/app/repository_provider.dart';
import 'package:dueswise/core/widgets/shared_widgets.dart';
import 'package:dueswise/data/models/scam_alert.dart';
import 'package:dueswise/data/repositories/finance_repository.dart';

/// Scam detection interface — user enters a sample message; mock analysis runs.
class ScamAnalysisScreen extends StatefulWidget {
  const ScamAnalysisScreen({super.key});

  @override
  State<ScamAnalysisScreen> createState() => _ScamAnalysisScreenState();
}

class _ScamAnalysisScreenState extends State<ScamAnalysisScreen> {
  final FinanceRepository _repo = AppRepository.instance;
  final _message = TextEditingController();
  bool _analyzing = false;
  ScamExplanation? _result;
  String? _error;

  static const List<Map<String, String>> samples = [
    {'label': 'UPI PIN request', 'text': 'Your account will be blocked. Share your UPI PIN at http://secure-bank.example to verify.'},
    {'label': 'Suspicious link', 'text': 'Click here bit.ly/3xyz to claim your reward. Urgent action required.'},
    {'label': 'Safe transaction', 'text': 'Your payment of ₹500 to Swiggy was successful. Thank you.'},
  ];

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  Future<void> _analyze() async {
    if (_message.text.trim().isEmpty) return;
    setState(() { _analyzing = true; _error = null; _result = null; });
    try {
      final explanation = await _repo.analyzeScam(ScamAnalysisRequest(message: _message.text.trim()));
      if (mounted) setState(() { _result = explanation; _analyzing = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _analyzing = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(title: const Text('Scam detection')),
      body: SafeArea(
        child: Column(
          children: [
            // Sample chips
            SizedBox(
              height: 40,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: samples.length,
                itemBuilder: (context, i) {
                  final s = samples[i];
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ActionChip(
                      label: Text(s['label']!, style: const TextStyle(fontSize: 12)),
                      onPressed: () => _message.text = s['text']!,
                    ),
                  );
                },
              ),
            ),
            const Divider(height: 1),
            // Message input
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    TextField(
                      controller: _message,
                      maxLines: 6,
                      decoration: const InputDecoration(
                        labelText: 'Paste or type a message to check',
                        hintText: 'e.g. Your account will be blocked. Share your UPI PIN.',
                        alignLabelWithHint: true,
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: FilledButton(
                        onPressed: _analyzing ? null : _analyze,
                        child: _analyzing ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Analyze message'),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppTheme.warningContainer,
                        borderRadius: BorderRadius.all(Radius.circular(12)),
                      ),
                      child: Text(
                        'Demo mode — no SMS is intercepted. You explicitly enter a sample message.',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.warning),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // Result
            if (_result != null)
              Container(
                color: AppTheme.surface,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Analysis result', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        const RiskBadgePlaceholder(),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(_result!.summary, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                              const SizedBox(height: 6),
                              Text(
                                'Reasons: ${_result!.reasons.join(', ')}',
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.onSurfaceVariant),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            const Icon(Icons.shield_outlined, color: AppTheme.info),
                            const SizedBox(width: 12),
                            Expanded(child: Text(_result!.safeAction, style: const TextStyle(fontSize: 14))),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            if (_error != null)
              Container(
                color: AppTheme.dangerContainer,
                padding: const EdgeInsets.all(16),
                child: Text(_error!, style: const TextStyle(color: AppTheme.danger)),
              ),
          ],
        ),
      ),
    );
  }
}

class RiskBadgePlaceholder extends StatelessWidget {
  const RiskBadgePlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      backgroundColor: AppTheme.danger.withOpacity(0.15),
      child: const Icon(Icons.warning, color: AppTheme.danger, size: 20),
    );
  }
}
