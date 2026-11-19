/// Base JSON envelope used by all API responses.
class ApiResponse<T> {
  final T data;
  final Map<String, dynamic>? raw;

  const ApiResponse({required this.data, this.raw});

  factory ApiResponse.fromJson(Map<String, dynamic> json, T Function(dynamic) fromJson) {
    return ApiResponse<T>(
      data: fromJson(json),
      raw: json,
    );
  }
}

/// Standard error envelope per CONTRACTS §2.3.
class ApiError {
  final String code;
  final String message;
  final Map<String, dynamic>? details;

  ApiError({
    required this.code,
    required this.message,
    this.details,
  });

  factory ApiError.fromJson(Map<String, dynamic> json) {
    final error = json['error'] ?? {};
    return ApiError(
      code: error['code'] ?? 'UNKNOWN_ERROR',
      message: error['message'] ?? 'An error occurred.',
      details: error['details'] != null
          ? Map<String, dynamic>.from(error['details'] as Map)
          : null,
    );
  }

  @override
  String toString() => 'ApiError($code: $message)';
}
