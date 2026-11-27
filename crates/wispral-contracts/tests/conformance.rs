use std::collections::HashMap;
use std::path::PathBuf;

use serde_json::Value;
use wispral_contracts::{validate_bundle, validate_runtime, validate_sequence, validate_shape};

fn contracts_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("docs")
        .join("engineering")
        .join("contracts")
}

#[test]
fn rust_conformance_matches_python_runner_across_all_148_cases_sequences_and_bundles() {
    let dir = contracts_dir();
    let trusted_raw: Value = serde_json::from_str(
        &std::fs::read_to_string(dir.join("fixtures").join("trusted_keys.json")).unwrap(),
    )
    .unwrap();
    let trusted_keys: HashMap<String, String> = trusted_raw["keys"]
        .as_object()
        .unwrap()
        .iter()
        .map(|(k, v)| (k.clone(), v.as_str().unwrap().to_owned()))
        .collect();

    let fixtures: Value = serde_json::from_str(
        &std::fs::read_to_string(dir.join("fixtures").join("cases.json")).unwrap(),
    )
    .unwrap();

    let cases = fixtures["cases"].as_array().unwrap();
    assert!(cases.len() >= 148, "expected >= 148 contract cases");

    for case in cases {
        let name = case["name"].as_str().unwrap();
        let schema = case["schema"].as_str().unwrap();
        let expect = case["expect"].as_str().unwrap();
        let layer = case.get("layer").and_then(Value::as_str).unwrap_or("shape");
        let instance = &case["instance"];

        let shape_res = validate_shape(schema, instance);
        let full_res = shape_res
            .clone()
            .and_then(|()| validate_runtime(schema, instance, &trusted_keys));

        let actual = if full_res.is_ok() { "valid" } else { "invalid" };
        assert_eq!(
            actual, expect,
            "case `{name}` ({schema}, layer={layer}) expected {expect} but got {actual}: {full_res:?}"
        );
        if expect == "invalid" && layer == "runtime" {
            assert!(
                shape_res.is_ok(),
                "runtime case `{name}` ({schema}) failed at shape layer instead of runtime layer: {shape_res:?}"
            );
        }
    }

    let sequences = fixtures["sequences"].as_array().unwrap();
    for seq in sequences {
        let name = seq["name"].as_str().unwrap();
        let machine = seq["machine"].as_str().unwrap();
        let expect = seq["expect"].as_str().unwrap();
        let states: Vec<String> = seq["states"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_owned())
            .collect();
        let actual = if validate_sequence(machine, &states) {
            "valid"
        } else {
            "invalid"
        };
        assert_eq!(actual, expect, "sequence `{name}` mismatch");
    }

    let bundles = fixtures["bundles"].as_array().unwrap();
    for b in bundles {
        let name = b["name"].as_str().unwrap();
        let expect = b["expect"].as_str().unwrap();
        let intents = b["intents"].as_array().unwrap();
        let verdicts = b["verdicts"].as_array().unwrap();
        let res = validate_bundle(intents, verdicts, &trusted_keys);
        let actual = if res.is_ok() { "valid" } else { "invalid" };
        assert_eq!(
            actual, expect,
            "bundle `{name}` expected {expect} got {actual}: {res:?}"
        );
    }
}
