/// Core errors used by repositories and services.

class AppException implements Exception {
  final String code;
  final String message;
  final Map<String, dynamic>? details;

  AppException({
    required this.code,
    required this.message,
    this.details,
  });

  factory AppException.fromJson(Map<String, dynamic> json) {
    return AppException(
      code: json['error']?['code'] ?? 'UNKNOWN_ERROR',
      message: json['error']?['message'] ?? 'An unexpected error occurred.',
      details: json['error']?['details'] != null
          ? Map<String, dynamic>.from(json['error']['details'] as Map)
          : null,
    );
  }

  @override
  String toString() => 'AppException($code: $message)';
}

class NetworkException extends AppException {
  NetworkException({String message = 'Network request failed.'})
      : super(code: 'NETWORK_ERROR', message: message);
}

class ValidationException extends AppException {
  ValidationException({String message = 'Validation failed.'})
      : super(code: 'VALIDATION_ERROR', message: message);
}

class NotFoundException extends AppException {
  NotFoundException({String message = 'Resource not found.'})
      : super(code: 'NOT_FOUND', message: message);
}
