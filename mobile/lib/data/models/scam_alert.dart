/// Scam alert per CONTRACTS §4.7 / BLUEPRINT §7.6.
class ScamAlert {
  final String id;
  final int riskScore;
  final String riskLevel; // low, medium, high, critical
  final String verdict; // suspicious, safe, etc.
  final List<String> indicators;
  final String explanation;
  final String status; // new, read, dismissed

  ScamAlert({
    required this.id,
    required this.riskScore,
    required this.riskLevel,
    required this.verdict,
    required this.indicators,
    required this.explanation,
    this.status = 'new',
  });

  bool get isCritical => riskLevel == 'critical';
  bool get isHigh => riskLevel == 'high';
  bool get isMedium => riskLevel == 'medium';
  bool get isLow => riskLevel == 'low';

  factory ScamAlert.fromJson(Map<String, dynamic> json) {
    return ScamAlert(
      id: json['id'] as String? ?? '',
      riskScore: int.tryParse(json['risk_score']?.toString() ?? '') ?? 0,
      riskLevel: json['risk_level'] as String? ?? 'low',
      verdict: json['verdict'] as String? ?? 'safe',
      indicators: (json['indicators'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      explanation: json['explanation'] as String? ?? '',
      status: json['status'] as String? ?? 'new',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'risk_score': riskScore,
      'risk_level': riskLevel,
      'verdict': verdict,
      'indicators': indicators,
      'explanation': explanation,
      'status': status,
    };
  }

  ScamAlert copyWith({String? status}) => ScamAlert(
        id: id,
        riskScore: riskScore,
        riskLevel: riskLevel,
        verdict: verdict,
        indicators: List<String>.from(indicators),
        explanation: explanation,
        status: status ?? this.status,
      );
}

/// Input to the scam analysis endpoint (backend calculates score; AI explains).
class ScamAnalysisRequest {
  final String? message;
  final int? riskScore;
  final String? riskLevel;
  final List<String>? indicators;

  ScamAnalysisRequest({
    this.message,
    this.riskScore,
    this.riskLevel,
    this.indicators,
  });

  Map<String, dynamic> toJson() {
    return {
      if (message != null) 'message': message,
      if (riskScore != null) 'risk_score': riskScore,
      if (riskLevel != null) 'risk_level': riskLevel,
      if (indicators != null) 'indicators': indicators,
    };
  }
}

/// Output of the scam explanation AI service.
class ScamExplanation {
  final String summary;
  final List<String> reasons;
  final String safeAction;

  ScamExplanation({
    required this.summary,
    required this.reasons,
    required this.safeAction,
  });

  factory ScamExplanation.fromJson(Map<String, dynamic> json) {
    return ScamExplanation(
      summary: json['summary'] as String? ?? '',
      reasons: (json['reasons'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      safeAction: json['safe_action'] as String? ?? '',
    );
  }
}
