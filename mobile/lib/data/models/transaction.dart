/// Standard transaction per CONTRACTS §7.1 / BLUEPRINT §7.1.
import 'package:dueswise/core/utils/money.dart';

class Transaction {
  final String id;
  final int amountPaise;
  final String currency;
  final String transactionType; // debit | credit
  final String? merchantRaw;
  final String? merchantNormalized;
  final String? category;
  final String? paymentMethod;
  final String? paymentApp;
  final String? gateway;
  final String transactionDate;
  final String? source;
  final double? confidence;

  Transaction({
    required this.id,
    required this.amountPaise,
    required this.currency,
    required this.transactionType,
    this.merchantRaw,
    this.merchantNormalized,
    this.category,
    this.paymentMethod,
    this.paymentApp,
    this.gateway,
    required this.transactionDate,
    this.source,
    this.confidence,
  });

  Money get amount => Money(amountPaise);
  bool get isDebit => transactionType == 'debit';
  bool get isCredit => transactionType == 'credit';

  /// Display merchant: normalized name, falling back to raw.
  String get displayMerchant =>
      merchantNormalized?.isNotEmpty == true
          ? merchantNormalized!
          : (merchantRaw?.isNotEmpty == true ? merchantRaw! : 'Unknown');

  String get displayCategory => category?.isNotEmpty == true
      ? category!
          .split('_')
          .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '')
      .join(' ')
      : 'Other';

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'] as String? ?? '',
      amountPaise: int.tryParse(json['amount_paise']?.toString() ?? '') ?? 0,
      currency: json['currency'] as String? ?? 'INR',
      transactionType: json['transaction_type'] as String? ?? 'debit',
      merchantRaw: json['merchant_raw'] as String?,
      merchantNormalized: json['merchant_normalized'] as String?,
      category: json['category'] as String?,
      paymentMethod: json['payment_method'] as String?,
      paymentApp: json['payment_app'] as String?,
      gateway: json['gateway'] as String?,
      transactionDate: json['transaction_date'] as String? ?? '',
      source: json['source'] as String?,
      confidence: json['confidence'] is num
          ? (json['confidence'] as num).toDouble()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'amount_paise': amountPaise,
      'currency': currency,
      'transaction_type': transactionType,
      if (merchantRaw != null) 'merchant_raw': merchantRaw,
      if (merchantNormalized != null) 'merchant_normalized': merchantNormalized,
      if (category != null) 'category': category,
      if (paymentMethod != null) 'payment_method': paymentMethod,
      if (paymentApp != null) 'payment_app': paymentApp,
      if (gateway != null) 'gateway': gateway,
      'transaction_date': transactionDate,
      if (source != null) 'source': source,
      if (confidence != null) 'confidence': confidence,
    };
  }
}

class IngestedTransaction {
  final String status;
  final Transaction transaction;
  final Map<String, dynamic> processing;

  IngestedTransaction({
    required this.status,
    required this.transaction,
    required this.processing,
  });

  factory IngestedTransaction.fromJson(Map<String, dynamic> json) {
    return IngestedTransaction(
      status: json['status'] as String? ?? 'processed',
      transaction: Transaction.fromJson(
        Map<String, dynamic>.from(json['transaction'] as Map),
      ),
      processing: Map<String, dynamic>.from(json['processing'] as Map? ?? {}),
    );
  }
}
