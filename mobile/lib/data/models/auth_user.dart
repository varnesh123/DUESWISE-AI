/// Authenticated account details returned by `/auth/me` and auth responses.
class AuthUser {
  final String id;
  final String name;
  final String? email;
  final String persona;
  final String currency;
  final bool isDemo;

  const AuthUser({
    required this.id,
    required this.name,
    this.email,
    this.persona = 'individual',
    this.currency = 'INR',
    this.isDemo = false,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      email: json['email']?.toString(),
      persona: json['persona']?.toString() ?? 'individual',
      currency: json['currency']?.toString() ?? 'INR',
      isDemo: json['is_demo'] as bool? ?? false,
    );
  }

  String get accountLabel => isDemo ? 'Demo account' : 'Personal account';
}
