/// Money handling.
///
/// All monetary values are stored and transported as integer paise.
/// Conversion to rupees for display happens only in the presentation layer.
/// No floating-point arithmetic is used for financial values.

/// Parse a user-entered rupee amount (for example "1,200.50" or "₹899")
/// into integer paise. Returns null when the input is not a valid amount.
///
/// Parsing is done with string operations so no floating-point value ever
/// touches a monetary amount.
int? parseRupeesToPaise(String input) {
  var text = input.trim().replaceAll(RegExp(r'[₹,\s]'), '');
  if (text.isEmpty) return null;
  if (text.startsWith('-')) return null;
  final parts = text.split('.');
  if (parts.length > 2) return null;
  final rupees = int.tryParse(parts.isEmpty ? '' : parts[0]);
  if (rupees == null || rupees < 0) return null;
  var paise = 0;
  if (parts.length == 2) {
    final fraction = (parts[1] + '00').substring(0, 2);
    paise = int.tryParse(fraction) ?? -1;
    if (paise < 0 || paise > 99) return null;
  }
  return rupees * 100 + paise;
}

class Money {
  final int paise;

  const Money(this.paise);

  factory Money.zero() => const Money(0);

  bool get isZero => paise == 0;
  bool get isNegative => paise < 0;
  bool get isPositive => paise > 0;

  /// Rupee component (whole rupees), truncating paise.
  int get rupees => paise ~/ 100;

  /// Remaining paise after whole rupees (0-99).
  int get paiseRemainder => paise.remainder(100).abs();

  Money operator +(Money other) => Money(paise + other.paise);
  Money operator -(Money other) => Money(paise - other.paise);
  Money operator -() => Money(-paise);

  /// Format as Indian rupees with Indian digit grouping, e.g. ₹12,000.00.
  String toInr({bool showSymbol = true, int fractionDigits = 2}) {
    final abs = paise.abs();
    final rupees = abs ~/ 100;
    final cents = abs % 100;
    final formatted = _indianGrouping(rupees);
    final sign = paise < 0 ? '-' : '';
    final symbol = showSymbol ? '₹' : '';
    if (fractionDigits == 0) {
      return '$sign$symbol$formatted';
    }
    return '$sign$symbol$formatted.${cents.toString().padLeft(2, '0')}';
  }

  /// Format without decimals for whole-rupee display, e.g. ₹12,000.
  String toInrWhole({bool showSymbol = true}) {
    final abs = paise.abs();
    final rupees = abs ~/ 100;
    final formatted = _indianGrouping(rupees);
    final sign = paise < 0 ? '-' : '';
    final symbol = showSymbol ? '₹' : '';
    return '$sign$symbol$formatted';
  }

  String _indianGrouping(int n) {
    final s = n.toString();
    if (s.length <= 3) return s;
    final head = s.substring(0, s.length - 3);
    final tail = s.substring(s.length - 3);
    final groups = <String>[];
    var h = head;
    while (h.length > 2) {
      groups.insert(0, h.substring(h.length - 2));
      h = h.substring(0, h.length - 2);
    }
    if (h.isNotEmpty) groups.insert(0, h);
    return [groups.join(','), tail].join(',');
  }

  @override
  String toString() => toInr();

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Money && paise == other.paise;

  @override
  int get hashCode => paise.hashCode;
}

extension MoneyDisplay on int {
  /// Interpret this integer as paise and format as INR.
  String asInr({bool showSymbol = true, int fractionDigits = 2}) =>
      Money(this).toInr(showSymbol: showSymbol, fractionDigits: fractionDigits);

  String asInrWhole({bool showSymbol = true}) => Money(this).toInrWhole(showSymbol: showSymbol);
}

/// Safe-to-spend display helper: distinguishes from total balance.
class SafeToSpendDisplay {
  final Money availableBalance;
  final Money safeToSpend;
  final Money upcomingDuesTotal;
  final Money safetyReserve;

  const SafeToSpendDisplay({
    required this.availableBalance,
    required this.safeToSpend,
    required this.upcomingDuesTotal,
    required this.safetyReserve,
  });

  /// How the safe-to-spend was derived (deterministic, backend-owned).
  String get explanation =>
      'Available balance minus upcoming mandatory dues, essential expenses and reserve.';

  bool get isLow => safeToSpend.paise * 5 < availableBalance.paise;
}
