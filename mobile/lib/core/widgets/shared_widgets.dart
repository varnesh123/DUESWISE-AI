/// DuesWise design system — Material 3.
///
/// Centralises colours, typography, shapes and reusable component helpers so
/// every screen shares a consistent fintech visual identity.

import 'package:flutter/material.dart';

import 'package:dueswise/core/utils/money.dart';
import 'package:dueswise/core/errors/app_exception.dart';
import 'package:dueswise/data/models/scam_alert.dart';

class AppTheme {
  AppTheme._();

  // Primary brand: deep trust blue.
  static const Color primary = Color(0xFF0F4C81);
  static const Color primaryContainer = Color(0xFFE3F2FD);
  static const Color onPrimary = Color(0xFFFFFFFF);

  // Safe-to-spend accent (green) — clearly distinct from balance.
  static const Color safeToSpend = Color(0xFF0E7C49);
  static const Color safeToSpendContainer = Color(0xFFE7F6EE);

  // Warning / attention (amber) for dues & high-priority nudges.
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningContainer = Color(0xFFFBF3DB);

  // Danger (red) for critical scam / overdue.
  static const Color danger = Color(0xFFDC2626);
  static const Color dangerContainer = Color(0xFFFEF2F2);

  // Surface / background.
  static const Color background = Color(0xFFF7F9FC);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color onBackground = Color(0xFF111827);
  static const Color onSurface = Color(0xFF1F2937);
  static const Color onSurfaceVariant = Color(0xFF6B7280);
  static const Color outline = Color(0xFFE5E7EB);

  static const Color success = Color(0xFF10B981);
  static const Color info = Color(0xFF3B82F6);

  static ThemeData light() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.light(
        primary: primary,
        onPrimary: onPrimary,
        primaryContainer: primaryContainer,
        secondary: warning,
        secondaryContainer: warningContainer,
        surface: surface,
        onSurface: onSurface,
        onSurfaceVariant: onSurfaceVariant,
        outline: outline,
        error: danger,
        errorContainer: dangerContainer,
        surfaceContainerHighest: Color(0xFFE4E7EB),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: onBackground),
        displayMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: onBackground),
        headlineLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: onBackground),
        headlineMedium: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: onBackground),
        headlineSmall: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: onSurface),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: onSurface),
        titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: onSurface),
        titleSmall: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: onSurfaceVariant),
        bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, color: onSurface),
        bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, color: onSurface),
        bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, color: onSurfaceVariant),
        labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: onSurface),
        labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: onSurfaceVariant),
        labelSmall: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: onSurfaceVariant),
      ),
      cardTheme: const CardThemeData(
        elevation: 0,
        color: surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(16))),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: onPrimary,
          elevation: 0,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
          padding: const EdgeInsets.symmetric(vertical: 14),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: onPrimary,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primary,
          minimumSize: const Size(double.infinity, 52),
          side: const BorderSide(color: primary),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
          borderSide: const BorderSide(color: outline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
          borderSide: const BorderSide(color: outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
          borderSide: const BorderSide(color: primary, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
          borderSide: const BorderSide(color: danger),
        ),
        labelStyle: const TextStyle(color: onSurfaceVariant, fontSize: 14),
        hintStyle: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 14),
      ),
      dividerTheme: const DividerThemeData(color: Color(0xFFF1F3F5), space: 1, thickness: 1),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: primary,
        foregroundColor: onPrimary,
        elevation: 2,
      ),
    );
  }
}

/// Reusable large currency display.
class CurrencyDisplay extends StatelessWidget {
  final Money amount;
  final TextStyle? style;
  final bool showLabel;
  final String? label;

  const CurrencyDisplay({
    super.key,
    required this.amount,
    this.style,
    this.showLabel = false,
    this.label,
  });

  @override
  Widget build(BuildContext context) {
    final text = amount.toInr();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (showLabel && label != null)
          Text(label!, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppTheme.onSurfaceVariant)),
        Text(
          text,
          style: style ?? Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.w700),
        ),
      ],
    );
  }
}

/// Reusable pill-shaped category chip.
class CategoryChip extends StatelessWidget {
  final String category;
  final bool selected;
  final VoidCallback? onTap;

  const CategoryChip({
    super.key,
    required this.category,
    this.selected = false,
    this.onTap,
  });

  String get display => category
      .split('_')
      .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '')
      .join(' ');

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text(display),
      selected: selected,
      onSelected: onTap != null ? (_) => onTap!() : null,
      backgroundColor: AppTheme.surface,
      selectedColor: AppTheme.primaryContainer,
      checkmarkColor: AppTheme.primary,
      labelStyle: TextStyle(
        color: selected ? AppTheme.primary : AppTheme.onSurfaceVariant,
        fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
        fontSize: 13,
      ),
      side: BorderSide(color: selected ? AppTheme.primary : AppTheme.outline),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(20))),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
    );
  }
}

/// Reusable risk badge for scam alerts.
class RiskBadge extends StatelessWidget {
  final ScamAlert alert;
  final double size;

  const RiskBadge({super.key, required this.alert, this.size = 28});

  Color _color() {
    switch (alert.riskLevel) {
      case 'critical':
      case 'high':
        return AppTheme.danger;
      case 'medium':
        return AppTheme.warning;
      default:
        return AppTheme.success;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _color();
    final label = alert.riskLevel.toUpperCase();
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        shape: BoxShape.circle,
        border: Border.all(color: color, width: 2),
      ),
      child: Center(
        child: Text(
          label.isNotEmpty ? label[0] : '?',
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w700,
            fontSize: size * 0.45,
          ),
        ),
      ),
    );
  }
}

/// Reusable empty state.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: AppTheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
            if (action != null) ...[
              const SizedBox(height: 20),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}

/// Reusable error state.
class ErrorState extends StatelessWidget {
  final AppException exception;
  final VoidCallback onRetry;

  const ErrorState({super.key, required this.exception, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 64, color: AppTheme.danger),
            const SizedBox(height: 16),
            Text(
              'Something went wrong',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              exception.message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}

/// Reusable loading state.
class LoadingState extends StatelessWidget {
  final String? message;

  const LoadingState({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(message!, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.onSurfaceVariant)),
          ],
        ],
      ),
    );
  }
}
