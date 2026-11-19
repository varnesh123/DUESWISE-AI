/// Authentication result (mock in Phase 5; live in Phase 6).
import 'package:flutter/material.dart';

class AuthResult {
  final String accessToken;
  final String tokenType;
  final int expiresInMinutes;
  final String userId;
  final String? refreshToken;

  AuthResult({
    required this.accessToken,
    this.tokenType = 'Bearer',
    required this.expiresInMinutes,
    required this.userId,
    this.refreshToken,
  });

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    return AuthResult(
      accessToken: json['access_token'] as String? ?? '',
      tokenType: json['token_type'] as String? ?? 'Bearer',
      expiresInMinutes: int.tryParse(json['expires_in_minutes']?.toString() ?? '') ?? 30,
      userId: json['user_id'] as String? ?? '',
      refreshToken: json['refresh_token'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'token_type': tokenType,
      'expires_in_minutes': expiresInMinutes,
      'user_id': userId,
      if (refreshToken != null) 'refresh_token': refreshToken,
    };
  }
}

/// Synthetic demo personas (BLUEPRINT §14).
enum DemoPersona { salaried, youngProfessional, shopkeeper }

extension DemoPersonaExt on DemoPersona {
  String get label {
    switch (this) {
      case DemoPersona.salaried:
        return 'Salaried Employee';
      case DemoPersona.youngProfessional:
        return 'Young Professional';
      case DemoPersona.shopkeeper:
        return 'Small Shopkeeper';
    }
  }

  String get subtitle {
    switch (this) {
      case DemoPersona.salaried:
        return '₹60,000/month salary • EMI • Rent';
      case DemoPersona.youngProfessional:
        return '₹45,000/month • OTT & music subscriptions';
      case DemoPersona.shopkeeper:
        return '₹40,000 opening • Daily UPI receipts';
    }
  }

  Color get color {
    switch (this) {
      case DemoPersona.salaried:
        return const Color(0xFF2563EB); // blue
      case DemoPersona.youngProfessional:
        return const Color(0xFF7C3AED); // violet
      case DemoPersona.shopkeeper:
        return const Color(0xFF059669); // emerald
    }
  }
}
