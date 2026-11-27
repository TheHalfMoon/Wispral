//! Wispral Core deterministic policy verdict lattice.
//!
//! Adapted from `TheHalfMoon/Sentrdel` (`f5747319a50831ef7cee983d253c0ca5503c9a64`,
//! Apache-2.0):
//! - Monotone narrowing order: `ALLOW < ASK < DENY`;
//! - `DENY` is strictly absorbing;
//! - An empty layer sequence or any `UNDECIDABLE` layer (without `DENY`) yields
//!   candidate `UNDECIDABLE`;
//! - `UNDECIDABLE` is never an enforced decision: it resolves to `ASK` only when
//!   `human_present == true` (Sentrdel default) and to `DENY` when unattended;
//! - Kernel floor violations unconditionally force `DENY`;
//! - Non-`read` enforced `ALLOW` requires at least one deterministic `rule_id`;
//!   model confidence or retrieved evidence alone never confers `ALLOW`.

pub mod bounded_json;

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CandidateDecision {
    Allow,
    Ask,
    Deny,
    Undecidable,
}

impl CandidateDecision {
    /// Strictness rank for decided layers (`ALLOW = 0 < ASK = 1 < DENY = 2`).
    pub fn rank(self) -> Option<u8> {
        match self {
            Self::Allow => Some(0),
            Self::Ask => Some(1),
            Self::Deny => Some(2),
            Self::Undecidable => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EnforcedDecision {
    Allow = 0,
    Ask = 1,
    Deny = 2,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum UndecidableResolution {
    Ask,
    Deny,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LayerSource {
    Base,
    Product,
    Tenant,
    Repository,
    User,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PolicyLayer {
    pub source: LayerSource,
    pub decision: CandidateDecision,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActionClass {
    Read,
    ReversibleWrite,
    IrreversibleWrite,
    Money,
    CredentialUse,
    Publication,
    TextDelivery,
    VoiceRender,
    FileExport,
}

impl ActionClass {
    pub fn is_high_risk_confirmation_class(self) -> bool {
        matches!(
            self,
            Self::Money | Self::CredentialUse | Self::IrreversibleWrite | Self::Publication
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum PolicyError {
    #[error("later policy layer ({later:?}) widens earlier decision ({earlier:?})")]
    LayerWidening {
        earlier: CandidateDecision,
        later: CandidateDecision,
    },
    #[error("unattended policy evaluation cannot resolve UNDECIDABLE to ASK")]
    UnattendedUndecidableAsk,
    #[error("enforced ALLOW requires at least one deterministic rule_id for {action_class:?}")]
    MissingRuleId { action_class: ActionClass },
    #[error("high-risk confirmation on {action_class:?} requires human_present = true")]
    UnattendedHighRiskConfirmation { action_class: ActionClass },
    #[error("voice_render ALLOW requires either stock_voice_catalog_id or active consent_record")]
    VoiceRenderMissingAuthority,
    #[error("text_delivery ALLOW requires verified target_binding evidence")]
    TextDeliveryMissingTargetBinding,
}

/// Validates that `later` does not widen `earlier` (`ALLOW < ASK < DENY`).
pub fn validate_narrowing(
    earlier: CandidateDecision,
    later: CandidateDecision,
) -> Result<(), PolicyError> {
    if let (Some(e), Some(l)) = (earlier.rank(), later.rank()) {
        if l < e {
            return Err(PolicyError::LayerWidening { earlier, later });
        }
    }
    Ok(())
}

/// Validates monotone narrowing across an ordered slice of policy layers and returns
/// the composed [`CandidateDecision`].
pub fn compose_layers(layers: &[PolicyLayer]) -> Result<CandidateDecision, PolicyError> {
    let mut prev_decided: Option<CandidateDecision> = None;
    for layer in layers {
        if layer.decision.rank().is_some() {
            if let Some(earlier) = prev_decided {
                validate_narrowing(earlier, layer.decision)?;
            }
            prev_decided = Some(layer.decision);
        }
    }
    Ok(compose_unvalidated(
        &layers.iter().map(|l| l.decision).collect::<Vec<_>>(),
    ))
}

/// Pure Sentrdel verdict composition without layer-order check:
/// - Any `DENY` absorbs to `DENY`;
/// - Empty or any `UNDECIDABLE` (without `DENY`) yields `UNDECIDABLE`;
/// - Otherwise the maximum rank (`ASK` if any `ASK`, else `ALLOW`).
pub fn compose_unvalidated(decisions: &[CandidateDecision]) -> CandidateDecision {
    if decisions.contains(&CandidateDecision::Deny) {
        return CandidateDecision::Deny;
    }
    if decisions.is_empty() || decisions.contains(&CandidateDecision::Undecidable) {
        return CandidateDecision::Undecidable;
    }
    if decisions.contains(&CandidateDecision::Ask) {
        CandidateDecision::Ask
    } else {
        CandidateDecision::Allow
    }
}

#[derive(Debug, Clone)]
pub struct EnforcementInputs<'a> {
    pub action_class: ActionClass,
    pub layers: &'a [PolicyLayer],
    pub kernel_floor_ids: &'a [String],
    pub rule_ids: &'a [String],
    pub human_present: bool,
    pub undecidable_resolution: UndecidableResolution,
    pub has_valid_confirmation: bool,
    pub has_stock_voice_catalog: bool,
    pub has_consent_evidence: bool,
    pub has_target_binding: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedVerdict {
    pub candidate_decision: CandidateDecision,
    pub enforced_decision: EnforcedDecision,
    pub undecidable_resolution: Option<UndecidableResolution>,
}

/// Evaluates layers, kernel floor invariants, human-presence rules, confirmation,
/// and action-specific authority gates (`voice_render`, `text_delivery`).
pub fn evaluate_verdict(inputs: &EnforcementInputs<'_>) -> Result<ResolvedVerdict, PolicyError> {
    let candidate = compose_layers(inputs.layers)?;

    if !inputs.kernel_floor_ids.is_empty() {
        let resolution =
            (candidate == CandidateDecision::Undecidable).then_some(if inputs.human_present {
                inputs.undecidable_resolution
            } else {
                UndecidableResolution::Deny
            });
        return Ok(ResolvedVerdict {
            candidate_decision: candidate,
            enforced_decision: EnforcedDecision::Deny,
            undecidable_resolution: resolution,
        });
    }

    if inputs.has_valid_confirmation
        && inputs.action_class.is_high_risk_confirmation_class()
        && !inputs.human_present
    {
        return Err(PolicyError::UnattendedHighRiskConfirmation {
            action_class: inputs.action_class,
        });
    }

    let (enforced, used_resolution) = match candidate {
        CandidateDecision::Deny => (EnforcedDecision::Deny, None),
        CandidateDecision::Undecidable => {
            if !inputs.human_present && inputs.undecidable_resolution == UndecidableResolution::Ask
            {
                return Err(PolicyError::UnattendedUndecidableAsk);
            }
            let res = if inputs.human_present {
                inputs.undecidable_resolution
            } else {
                UndecidableResolution::Deny
            };
            let enf = match res {
                UndecidableResolution::Ask => EnforcedDecision::Ask,
                UndecidableResolution::Deny => EnforcedDecision::Deny,
            };
            (enf, Some(res))
        }
        CandidateDecision::Ask => {
            if inputs.has_valid_confirmation {
                (EnforcedDecision::Allow, None)
            } else {
                (EnforcedDecision::Ask, None)
            }
        }
        CandidateDecision::Allow => (EnforcedDecision::Allow, None),
    };

    if enforced == EnforcedDecision::Allow {
        if inputs.action_class != ActionClass::Read && inputs.rule_ids.is_empty() {
            return Err(PolicyError::MissingRuleId {
                action_class: inputs.action_class,
            });
        }
        if inputs.action_class == ActionClass::VoiceRender
            && !inputs.has_stock_voice_catalog
            && !inputs.has_consent_evidence
        {
            return Err(PolicyError::VoiceRenderMissingAuthority);
        }
        if inputs.action_class == ActionClass::TextDelivery && !inputs.has_target_binding {
            return Err(PolicyError::TextDeliveryMissingTargetBinding);
        }
    }

    Ok(ResolvedVerdict {
        candidate_decision: candidate,
        enforced_decision: enforced,
        undecidable_resolution: used_resolution,
    })
}

#[cfg(test)]
mod tests {
    use super::bounded_json::{preflight, PreflightError, PreflightLimits};
    use super::*;

    #[test]
    fn exhaustive_4_to_n_lattice_invariants_hold_up_to_length_4() {
        let all = [
            CandidateDecision::Allow,
            CandidateDecision::Ask,
            CandidateDecision::Deny,
            CandidateDecision::Undecidable,
        ];
        // n = 0
        assert_eq!(compose_unvalidated(&[]), CandidateDecision::Undecidable);

        let mut checked = 1usize;
        for len in 1..=4 {
            let total = 4usize.pow(len as u32);
            for mask in 0..total {
                let mut seq = Vec::with_capacity(len);
                let mut x = mask;
                for _ in 0..len {
                    seq.push(all[x % 4]);
                    x /= 4;
                }
                let out = compose_unvalidated(&seq);
                // Deny absorbs everything
                if seq.contains(&CandidateDecision::Deny) {
                    assert_eq!(out, CandidateDecision::Deny);
                } else if seq.contains(&CandidateDecision::Undecidable) {
                    assert_eq!(out, CandidateDecision::Undecidable);
                } else if seq.contains(&CandidateDecision::Ask) {
                    assert_eq!(out, CandidateDecision::Ask);
                } else {
                    assert_eq!(out, CandidateDecision::Allow);
                }
                // Associativity / commutativity of pure composition
                let mut rev = seq.clone();
                rev.reverse();
                assert_eq!(out, compose_unvalidated(&rev));
                checked += 1;
            }
        }
        assert_eq!(checked, 1 + 4 + 16 + 64 + 256);
    }

    #[test]
    fn layer_widening_is_rejected_and_narrowing_is_accepted() {
        let valid = [
            PolicyLayer {
                source: LayerSource::Base,
                decision: CandidateDecision::Allow,
            },
            PolicyLayer {
                source: LayerSource::Tenant,
                decision: CandidateDecision::Ask,
            },
            PolicyLayer {
                source: LayerSource::User,
                decision: CandidateDecision::Deny,
            },
        ];
        assert_eq!(compose_layers(&valid).unwrap(), CandidateDecision::Deny);

        let widened = [
            PolicyLayer {
                source: LayerSource::Base,
                decision: CandidateDecision::Deny,
            },
            PolicyLayer {
                source: LayerSource::Tenant,
                decision: CandidateDecision::Ask,
            },
        ];
        assert!(matches!(
            compose_layers(&widened),
            Err(PolicyError::LayerWidening { .. })
        ));
    }

    #[test]
    fn unattended_undecidable_resolves_to_deny_and_forbids_ask() {
        let base = EnforcementInputs {
            action_class: ActionClass::Money,
            layers: &[],
            kernel_floor_ids: &[],
            rule_ids: &["refund_cap".into()],
            human_present: false,
            undecidable_resolution: UndecidableResolution::Ask,
            has_valid_confirmation: false,
            has_stock_voice_catalog: false,
            has_consent_evidence: false,
            has_target_binding: false,
        };
        assert_eq!(
            evaluate_verdict(&base).unwrap_err(),
            PolicyError::UnattendedUndecidableAsk
        );

        let deny_cfg = EnforcementInputs {
            undecidable_resolution: UndecidableResolution::Deny,
            ..base
        };
        let resolved = evaluate_verdict(&deny_cfg).unwrap();
        assert_eq!(resolved.candidate_decision, CandidateDecision::Undecidable);
        assert_eq!(resolved.enforced_decision, EnforcedDecision::Deny);
    }

    #[test]
    fn bounded_json_preflight_rejects_oversize_deep_wide_and_malformed_frames() {
        let limits = PreflightLimits {
            max_total_bytes: 256,
            max_depth: 4,
            max_nodes: 16,
            max_string_bytes: 32,
            max_object_keys: 4,
        };
        assert!(preflight(br#"{"a":1,"b":[true,false,"ok"]}"#, limits).is_ok());
        assert!(matches!(
            preflight(b"[[[[[1]]]]]", limits),
            Err(PreflightError::DepthExceeded { .. })
        ));
        assert!(matches!(
            preflight(br#"{"a":1,"b":2,"c":3,"d":4,"e":5}"#, limits),
            Err(PreflightError::ObjectTooWide { .. })
        ));
        assert!(matches!(
            preflight(br#"{"s":"01234567890123456789012345678901234"}"#, limits),
            Err(PreflightError::StringTooLong { .. })
        ));
        assert!(matches!(
            preflight(br#"{"a":1} trailing"#, limits),
            Err(PreflightError::MalformedJson)
        ));
    }
}
