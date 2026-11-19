/// Low-level HTTP client for the DuesWise financial backend.
///
/// Adds the bearer auth header to every request, applies a request timeout,
/// and translates HTTP/status errors into [AppException] instances so the
/// repository layer stays free of networking concerns.
///
/// Flutter must call only the main backend (`:8000`). It must never call
/// the independent AI service (`:8001`) directly.
library dueswise.data.live.api_client;

import 'dart:convert';

import 'package:http/http.dart' as http;

import 'package:dueswise/core/errors/app_exception.dart';

/// Default request timeout for backend calls.
const Duration _defaultTimeout = Duration(seconds: 10);

/// Base API path per CONTRACTS.md §7.
const String _apiPath = '/api/v1';

/// HTTP client wrapper that authenticates requests and normalises errors.
class ApiClient {
  ApiClient({
    http.Client? client,
    required String baseUrl,
  }) : _client = client ?? http.Client(),
       _baseUrl = baseUrl;

  final http.Client _client;
  final String _baseUrl;

  String? _accessToken;

  /// Set the bearer token (for example after login or from storage).
  void setAccessToken(String? token) {
    _accessToken = token;
  }

  /// Persist the access token after a successful login/register.
  Future<void> persistToken(String? token, Future<void> Function(String?)? write) async {
    _accessToken = token;
    if (write != null) {
      await write(token);
    }
  }

  /// Clear the stored token (logout).
  Future<void> clearToken(Future<void> Function(String?)? write) async {
    _accessToken = null;
    if (write != null) {
      await write(null);
    }
  }

  Map<String, String> _headers({bool includeAuth = true}) {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (includeAuth && _accessToken != null && _accessToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    return headers;
  }

  Uri _url(String path) {
    final p = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$_baseUrl$_apiPath$p');
  }

  /// Execute a request and return the decoded JSON body, or throw.
  Future<Map<String, dynamic>?> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool includeAuth = true,
  }) async {
    final uri = _url(path);
    final headers = _headers(includeAuth: includeAuth);

    final request = http.Request(method, uri)
      ..headers.addAll(headers);
    if (body != null) {
      request.body = jsonEncode(body);
    }

    http.StreamedResponse response;
    try {
      response = await _client.send(request).timeout(_defaultTimeout);
    } on http.ClientException {
      throw NetworkException();
    } catch (_) {
      throw NetworkException();
    }

    final responseBody = await response.stream.bytesToString();
    final status = response.statusCode;

    if (status == 401) {
      throw UnauthorizedException();
    }

    dynamic decoded;
    if (responseBody.isNotEmpty) {
      try {
        decoded = jsonDecode(responseBody);
      } catch (_) {
        decoded = null;
      }
    }

    if (status >= 200 && status < 300) {
      return decoded is Map ? Map<String, dynamic>.from(decoded) : null;
    }

    final errorMap = decoded is Map ? Map<String, dynamic>.from(decoded) : <String, dynamic>{};
    final errorObj = errorMap['error'] is Map
        ? Map<String, dynamic>.from(errorMap['error'] as Map)
        : <String, dynamic>{};
    final code = errorObj['code'] as String? ?? 'SERVER_ERROR';
    final message = errorObj['message'] as String? ?? 'Request failed.';
    final details = errorObj['details'] is Map
        ? Map<String, dynamic>.from(errorObj['details'] as Map)
        : null;

    throw AppException(code: code, message: message, details: details);
  }

  Future<Map<String, dynamic>?> get(String path, {bool includeAuth = true}) =>
      _request('GET', path, includeAuth: includeAuth);

  Future<Map<String, dynamic>?> post(
    String path, {
    Map<String, dynamic>? body,
    bool includeAuth = true,
  }) =>
      _request('POST', path, body: body, includeAuth: includeAuth);

  Future<Map<String, dynamic>?> patch(
    String path, {
    Map<String, dynamic>? body,
    bool includeAuth = true,
  }) =>
      _request('PATCH', path, body: body, includeAuth: includeAuth);

  void dispose() {
    _client.close();
  }
}

/// Thrown when the backend is unreachable or a request times out.
class NetworkException extends AppException {
  NetworkException({String message = 'Network request failed.'})
      : super(code: 'NETWORK_ERROR', message: message);
}

/// Thrown when the backend returns HTTP 401 Unauthorized.
class UnauthorizedException extends AppException {
  UnauthorizedException({String message = 'Unauthorized. Please log in again.'})
      : super(code: 'UNAUTHORIZED', message: message);
}

/// Thrown when the backend returns a not-found response.
class NotFoundException extends AppException {
  NotFoundException({String message = 'Resource not found.'})
      : super(code: 'NOT_FOUND', message: message);
}