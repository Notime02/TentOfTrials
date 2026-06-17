use serde_json::{json, Value};

use super::validate::{
    validate_email, validate_hex_string, validate_instrument_id, validate_phone, validate_price,
    validate_quantity, validate_symbol, validate_timestamp, validate_uuid, EmailValidator,
    EnumValidator, FieldValidator, MessageValidator, NumericRangeValidator, RegexValidator,
    RequiredValidator, Severity, StringLengthValidator, ValidationResult,
};

fn error_codes(result: &ValidationResult) -> Vec<&str> {
    result
        .errors
        .iter()
        .map(|error| error.code.as_str())
        .collect()
}

fn has_error(result: &ValidationResult, field: &str, code: &str) -> bool {
    result
        .errors
        .iter()
        .any(|error| error.field == field && error.code == code)
}

// ---------------------------------------------------------------------------
// Schema stage
// ---------------------------------------------------------------------------

#[test]
fn schema_stage_unknown_message_reports_schema_mismatch() {
    let validator = MessageValidator::new();

    let result = validator.validate(9000, 3, br#"{"kind":"event"}"#);

    assert!(!result.valid);
    assert!(has_error(&result, "_schema", "schema_mismatch"));
}

#[test]
fn schema_stage_malformed_payload_still_reports_schema_error() {
    let validator = MessageValidator::new();

    let result = validator.validate(9000, 3, b"not-json");

    assert!(!result.valid);
    assert_eq!(result.errors.len(), 1);
    assert!(has_error(&result, "_schema", "schema_mismatch"));
}

// ---------------------------------------------------------------------------
// Field stage
// ---------------------------------------------------------------------------

#[test]
fn field_stage_required_validator_accepts_present_values() {
    let value = Some("session-123");

    let result = RequiredValidator.validate(&value, "session_id");

    assert!(result.valid);
    assert!(!result.has_errors());
}

#[test]
fn field_stage_required_validator_rejects_missing_values() {
    let value: Option<&str> = None;

    let result = RequiredValidator.validate(&value, "session_id");

    assert!(!result.valid);
    assert!(has_error(&result, "session_id", "required"));
}

#[test]
fn field_stage_string_length_reports_min_and_max_violations() {
    let validator = StringLengthValidator {
        min: Some(3),
        max: Some(5),
    };

    let too_short = validator.validate(&"ab".to_string(), "symbol");
    let too_long = validator.validate(&"abcdef".to_string(), "symbol");

    assert!(has_error(&too_short, "symbol", "min_length"));
    assert!(has_error(&too_long, "symbol", "max_length"));
}

#[test]
fn field_stage_numeric_range_reports_lower_and_upper_bounds() {
    let validator = NumericRangeValidator {
        min: Some(10.0),
        max: Some(20.0),
    };

    let below = validator.validate(&9.99, "amount");
    let above = validator.validate(&20.01, "amount");

    assert!(has_error(&below, "amount", "min_value"));
    assert!(has_error(&above, "amount", "max_value"));
}

#[test]
fn field_stage_regex_validator_accepts_and_rejects_patterns() {
    let validator = RegexValidator {
        pattern: r"^[A-Z]{3}/[A-Z]{3}$",
    };

    assert!(validator.validate(&"BTC/USD".to_string(), "symbol").valid);
    assert!(has_error(
        &validator.validate(&"btc-usd".to_string(), "symbol"),
        "symbol",
        "pattern_mismatch"
    ));
}

#[test]
fn field_stage_enum_validator_keeps_allowed_values_explicit() {
    let validator = EnumValidator {
        variants: &["market", "limit", "stop", "stop_limit"],
    };

    assert!(validator.validate(&"limit".to_string(), "type").valid);
    assert!(has_error(
        &validator.validate(&"iceberg".to_string(), "type"),
        "type",
        "invalid_value"
    ));
}

#[test]
fn field_stage_email_validator_uses_the_same_public_helper_boundary() {
    assert!(
        EmailValidator
            .validate(&"ops@example.com".to_string(), "email")
            .valid
    );
    assert!(has_error(
        &EmailValidator.validate(&"ops.example.com".to_string(), "email"),
        "email",
        "invalid_email"
    ));
}

#[test]
fn field_stage_registered_validator_runs_for_matching_json_message_type() {
    let mut validator = MessageValidator::new();
    validator.register_field_validator(
        42,
        Box::new(
            |value: &Value| match value.get("kind").and_then(Value::as_str) {
                Some("event") => ValidationResult::valid(),
                _ => ValidationResult::error("kind", "invalid_kind", "kind must be event"),
            },
        ),
    );

    let result = validator.validate(42, 3, br#"{"kind":"command"}"#);

    assert!(has_error(&result, "_schema", "schema_mismatch"));
    assert!(has_error(&result, "kind", "invalid_kind"));
}

// ---------------------------------------------------------------------------
// Business stage
// ---------------------------------------------------------------------------

#[test]
fn business_stage_valid_limit_order_payload_passes() {
    let payload = json!({
        "side": "buy",
        "type": "limit",
        "quantity": 12.5,
        "price": 101.25,
        "time_in_force": "gtc"
    });

    let result = MessageValidator::validate_order_payload(&payload);

    assert!(result.valid);
    assert!(result.errors.is_empty());
}

#[test]
fn business_stage_missing_required_order_fields_are_reported_together() {
    let payload = json!({});

    let result = MessageValidator::validate_order_payload(&payload);

    assert!(!result.valid);
    assert!(has_error(&result, "side", "required"));
    assert!(has_error(&result, "type", "required"));
    assert!(has_error(&result, "quantity", "required"));
    assert!(has_error(&result, "price", "required"));
}

#[test]
fn business_stage_order_type_mismatches_are_not_silent() {
    let payload = json!({
        "side": "hold",
        "type": "iceberg",
        "quantity": "10",
        "price": 10.0
    });

    let result = MessageValidator::validate_order_payload(&payload);

    assert!(has_error(&result, "side", "invalid_side"));
    assert!(has_error(&result, "type", "invalid_type"));
    assert!(has_error(&result, "quantity", "required"));
}

#[test]
fn business_stage_order_range_violations_are_explicit() {
    let payload = json!({
        "side": "sell",
        "type": "limit",
        "quantity": 1_000_001.0,
        "price": -1.0
    });

    let result = MessageValidator::validate_order_payload(&payload);

    assert!(has_error(&result, "quantity", "max_exceeded"));
    assert!(has_error(&result, "price", "invalid_price"));
}

#[test]
fn business_stage_market_orders_do_not_require_price() {
    let payload = json!({
        "side": "buy",
        "type": "market",
        "quantity": 1.0
    });

    let result = MessageValidator::validate_order_payload(&payload);

    assert!(result.valid);
}

#[test]
fn business_stage_invalid_time_in_force_is_rejected() {
    let payload = json!({
        "side": "sell",
        "type": "limit",
        "quantity": 1.0,
        "price": 10.0,
        "time_in_force": "weekend"
    });

    let result = MessageValidator::validate_order_payload(&payload);

    assert!(has_error(&result, "time_in_force", "invalid_tif"));
}

#[test]
fn business_stage_account_payload_accepts_supported_currency_and_amount() {
    let payload = json!({
        "amount": 100.0,
        "currency": "USDC"
    });

    let result = MessageValidator::validate_account_payload(&payload);

    assert!(result.valid);
}

#[test]
fn business_stage_account_payload_rejects_amount_and_currency_edges() {
    let payload = json!({
        "amount": 1_000_000_001.0,
        "currency": "DOGE"
    });

    let result = MessageValidator::validate_account_payload(&payload);

    assert!(has_error(&result, "amount", "max_exceeded"));
    assert!(has_error(&result, "currency", "invalid_currency"));
}

#[test]
fn business_stage_documents_rust_java_rule_drift() {
    let rust_rules = include_str!("validate.rs");
    let java_rules = include_str!("../../../compliance/ComplianceAuditor.java");

    assert!(rust_rules.contains("Quantity exceeds maximum allowed"));
    assert!(rust_rules.contains("Unsupported currency"));
    assert!(java_rules.contains("POSITION_LIMIT"));
    assert!(java_rules.contains("Position limit: not enforced"));
    assert!(java_rules.contains("DAY_TRADING"));
    assert!(java_rules.contains("Day trading: not restricted"));
}

// ---------------------------------------------------------------------------
// Integrity stage
// ---------------------------------------------------------------------------

#[test]
fn integrity_stage_custom_validator_reports_checksum_failure() {
    let mut validator = MessageValidator::new();
    validator.register_custom_validator(Box::new(|_message_type, payload| {
        let value: Value = serde_json::from_slice(payload).unwrap_or(Value::Null);
        if value.get("checksum").and_then(Value::as_str) == Some("expected") {
            ValidationResult::valid()
        } else {
            ValidationResult::error("checksum", "checksum_mismatch", "checksum does not match")
        }
    }));

    let result = validator.validate(77, 3, br#"{"checksum":"tampered"}"#);

    assert!(has_error(&result, "_schema", "schema_mismatch"));
    assert!(has_error(&result, "checksum", "checksum_mismatch"));
}

#[test]
fn integrity_stage_custom_validator_can_accept_matching_checksum() {
    let mut validator = MessageValidator::new();
    validator.register_custom_validator(Box::new(|_message_type, payload| {
        let value: Value = serde_json::from_slice(payload).unwrap_or(Value::Null);
        if value.get("checksum").and_then(Value::as_str) == Some("expected") {
            ValidationResult::valid()
        } else {
            ValidationResult::error("checksum", "checksum_mismatch", "checksum does not match")
        }
    }));

    let result = validator.validate(77, 3, br#"{"checksum":"expected"}"#);
    let codes = error_codes(&result);

    assert!(codes.contains(&"schema_mismatch"));
    assert!(!codes.contains(&"checksum_mismatch"));
}

// ---------------------------------------------------------------------------
// ValidationResult helpers and convenience functions
// ---------------------------------------------------------------------------

#[test]
fn validation_result_helpers_preserve_errors_warnings_and_severity() {
    let mut result = ValidationResult::valid();
    result.add_warning("near limit");
    result.add_error("amount", "invalid_amount", "Amount must be positive");

    assert!(!result.valid);
    assert!(result.has_errors());
    assert!(result.has_warnings());
    assert_eq!(result.errors[0].severity, Severity::Error);
    assert_eq!(result.warnings, vec!["near limit"]);
}

#[test]
fn validation_result_combine_accumulates_multiple_stage_results() {
    let mut result = ValidationResult::error("side", "invalid_side", "bad side");
    let mut other = ValidationResult::valid();
    other.add_warning("field will be normalized");
    other.add_error("quantity", "invalid_quantity", "bad quantity");

    result.combine(other);

    assert!(!result.valid);
    assert_eq!(result.errors.len(), 2);
    assert_eq!(result.warnings.len(), 1);
}

#[test]
fn convenience_email_phone_uuid_and_hex_boundaries_are_checked() {
    assert!(validate_email("person@example.com"));
    assert!(!validate_email("person.example.com"));
    assert!(validate_phone("+1 (555) 010-1234"));
    assert!(!validate_phone("12345"));
    assert!(validate_uuid("550e8400-e29b-41d4-a716-446655440000"));
    assert!(!validate_uuid("550E8400-E29B-41D4-A716-446655440000"));
    assert!(validate_hex_string("deadbeef", 4));
    assert!(!validate_hex_string("deadbee", 4));
}

#[test]
fn convenience_timestamp_symbol_and_instrument_boundaries_are_checked() {
    assert!(validate_timestamp(946684800000));
    assert!(validate_timestamp(4102444800000));
    assert!(!validate_timestamp(946684799999));
    assert!(validate_symbol("BTC/USD"));
    assert!(!validate_symbol("btc/usd"));
    assert!(validate_instrument_id("btcusdt"));
    assert!(!validate_instrument_id("BTCUSDT"));
}

#[test]
fn convenience_price_and_quantity_boundaries_are_checked() {
    assert!(validate_price(1.123456789));
    assert!(!validate_price(0.0));
    assert!(!validate_price(1_000_000_000.0));
    assert!(!validate_price(1.1234567899));
    assert!(validate_quantity(99_999_999.999));
    assert!(!validate_quantity(0.0));
    assert!(!validate_quantity(100_000_000.0));
}
