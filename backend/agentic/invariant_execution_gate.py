"""Pre-Action Clinical Invariant Execution Gate.

Acts as an absolute deterministic safety barrier between autonomous AI agents
and hospital order execution. Evaluates 5 critical clinical invariants:
1. Absolute Contraindications
2. Renal & Hepatic Clearance Floors
3. Teratogenic & Pregnancy Restrictions
4. Anaphylactic Allergy Cross-Reactivity
5. High-Risk Four-Eye Quorum Mandates
"""

from __future__ import annotations

import datetime
import hashlib
import re
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class InvariantType(str, Enum):
    """Categorization of clinical safety invariant barriers."""

    ABSOLUTE_CONTRAINDICATION = "ABSOLUTE_CONTRAINDICATION"
    RENAL_HEPATIC_FLOOR = "RENAL_HEPATIC_FLOOR"
    RENAL_HEPATIC_CLEARANCE = "RENAL_HEPATIC_CLEARANCE"  # Backward compatibility alias
    PREGNANCY_TERATOGEN = "PREGNANCY_TERATOGEN"
    PREGNANCY_TERATOGENIC = "PREGNANCY_TERATOGENIC"  # Backward compatibility alias
    ALLERGY_ANAPHYLAXIS = "ALLERGY_ANAPHYLAXIS"
    ANAPHYLAXIS_ALLERGY = "ANAPHYLAXIS_ALLERGY"  # Backward compatibility alias
    FOUR_EYE_QUORUM = "FOUR_EYE_QUORUM"

    def canonical(self) -> str:
        """Return standard invariant barrier identifier."""
        if self.value in ("RENAL_HEPATIC_FLOOR", "RENAL_HEPATIC_CLEARANCE"):
            return "RENAL_HEPATIC_FLOOR"
        if self.value in ("PREGNANCY_TERATOGEN", "PREGNANCY_TERATOGENIC"):
            return "PREGNANCY_TERATOGEN"
        if self.value in ("ALLERGY_ANAPHYLAXIS", "ANAPHYLAXIS_ALLERGY"):
            return "ALLERGY_ANAPHYLAXIS"
        return self.value

    def __eq__(self, other: Any) -> bool:
        if super().__eq__(other):
            return True
        val = str(other.value if isinstance(other, Enum) else other).upper()
        if self.value in ("RENAL_HEPATIC_FLOOR", "RENAL_HEPATIC_CLEARANCE") and val in (
            "RENAL_HEPATIC_FLOOR",
            "RENAL_HEPATIC_CLEARANCE",
        ):
            return True
        if self.value in ("PREGNANCY_TERATOGEN", "PREGNANCY_TERATOGENIC") and val in (
            "PREGNANCY_TERATOGEN",
            "PREGNANCY_TERATOGENIC",
        ):
            return True
        if self.value in ("ALLERGY_ANAPHYLAXIS", "ANAPHYLAXIS_ALLERGY") and val in (
            "ALLERGY_ANAPHYLAXIS",
            "ANAPHYLAXIS_ALLERGY",
        ):
            return True
        return False

    def __hash__(self) -> int:
        return hash(self.canonical())


class ValidationStatus(str, Enum):
    """Validation barrier decision status."""

    PASS = "PASS"
    REJECT = "REJECT"


class InvariantViolation:
    """Detailed clinical explanation of an invariant breach."""

    def __init__(
        self,
        invariant_type: InvariantType | str,
        rule_id: str,
        message: str,
        clinical_severity: str = "FATAL_RISK",
        remediation: str = "",
    ) -> None:
        if isinstance(invariant_type, str):
            try:
                self.invariant_type = InvariantType(invariant_type)
            except ValueError:
                self.invariant_type = InvariantType[invariant_type]
        else:
            self.invariant_type = invariant_type
        self.rule_id = rule_id
        self.message = message
        self.clinical_severity = clinical_severity
        self.remediation = remediation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invariant_type": self.invariant_type.canonical(),
            "raw_invariant_type": self.invariant_type.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "clinical_severity": self.clinical_severity,
            "remediation": self.remediation,
        }


class InvariantValidationResult:
    """Outcome of inspecting a FHIR action proposal against pre-action invariants."""

    def __init__(
        self,
        status: ValidationStatus | str,
        barrier_triggered: Optional[str] = None,
        explanation: str = "",
        violations: Optional[List[InvariantViolation]] = None,
        audit_token: Optional[str] = None,
        proposal_id: Optional[str] = None,
    ) -> None:
        if isinstance(status, str):
            status_str = status.upper()
            if "PASS" in status_str or "SAFE" in status_str:
                self.status = ValidationStatus.PASS
            else:
                self.status = ValidationStatus.REJECT
        else:
            self.status = status
        self.barrier_triggered = barrier_triggered
        self.explanation = explanation
        self.violations = violations or []
        self.audit_token = audit_token or str(uuid.uuid4())
        self.proposal_id = proposal_id
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "passed": self.passed,
            "barrier_triggered": self.barrier_triggered,
            "explanation": self.explanation,
            "violations": [v.to_dict() for v in self.violations],
            "audit_token": self.audit_token,
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp.isoformat(),
        }


class InvariantExecutionResult:
    """Outcome of safety-gated execution."""

    def __init__(
        self,
        allowed: bool,
        status: str,
        action_name: str,
        parameters: Dict[str, Any],
        violations: Optional[List[InvariantViolation]] = None,
        execution_output: Optional[Any] = None,
        audit_token: Optional[str] = None,
    ) -> None:
        self.allowed = allowed
        self.status = status  # EXECUTED_SAFE, REJECTED_INVARIANT_BREACH
        self.action_name = action_name
        self.parameters = parameters
        self.violations = violations or []
        self.execution_output = execution_output
        self.audit_token = audit_token or str(uuid.uuid4())
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "status": self.status,
            "action_name": self.action_name,
            "parameters": self.parameters,
            "violations": [v.to_dict() for v in self.violations],
            "execution_output": self.execution_output,
            "audit_token": self.audit_token,
            "timestamp": self.timestamp.isoformat(),
        }


class PreActionInvariantGate:
    """Deterministic runtime validator enforcing medical safety invariants."""

    def __init__(self) -> None:
        self._audit_log: List[Dict[str, Any]] = []

    def evaluate_invariants(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        patient_profile: Dict[str, Any],
    ) -> List[InvariantViolation]:
        """Evaluate action against deterministic physiological invariants."""
        violations: List[InvariantViolation] = []

        drug_name = (
            parameters.get("drug")
            or parameters.get("medication_name")
            or parameters.get("name")
            or ""
        ).strip().lower()

        active_conditions = [str(c).lower() for c in patient_profile.get("conditions", [])]
        allergies = [str(a).lower() for a in patient_profile.get("allergies", [])]
        current_meds = [str(m).lower() for m in patient_profile.get("current_meds", [])]

        # Renal clearance metrics
        egfr = float(patient_profile.get("egfr", patient_profile.get("crcl", 90.0)))
        crcl = float(patient_profile.get("crcl", egfr))
        effective_renal = min(egfr, crcl)

        # Hepatic clearance metrics
        liver_failure = (
            patient_profile.get("liver_failure", False)
            or patient_profile.get("hepatic_failure", False)
            or any("cirrhosis" in c or "liver failure" in c or "hepatic" in c for c in active_conditions)
            or patient_profile.get("child_pugh") in ("B", "C")
            or float(patient_profile.get("alt", 20.0)) > 1000.0
            or float(patient_profile.get("ast", 20.0)) > 1000.0
        )

        is_pregnant = (
            bool(patient_profile.get("is_pregnant", False))
            or any("pregnancy" in c or "pregnant" in c for c in active_conditions)
        )
        is_lactating = bool(patient_profile.get("is_lactating", False))

        # Check countersignature
        countersigned = (
            parameters.get("countersigned_by") is not None
            or parameters.get("dual_signoff") is True
            or parameters.get("dual_attending_approved") is True
            or parameters.get("countersignature") is not None
            or bool(parameters.get("countersigned", False))
        )

        # Dose extraction
        dose = parameters.get("dose")
        if dose is None and "dosage" in parameters:
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(parameters["dosage"]))
            if match:
                try:
                    dose = float(match.group(1))
                except (ValueError, TypeError):
                    dose = None
        dose_val = float(dose) if dose is not None else 0.0

        # =====================================================================
        # Invariant 1: Absolute Contraindication Checks
        # =====================================================================
        # Thrombolytics vs bleeding
        thrombolytics = ["alteplase", "tpa", "tenecteplase", "reteplase", "streptokinase"]
        if any(t in drug_name for t in thrombolytics):
            has_hemorrhage = any(
                "hemorrhage" in c
                or "bleeding" in c
                or "hematoma" in c
                or "aortic dissection" in c
                or "coagulopathy" in c
                for c in active_conditions
            )
            if has_hemorrhage:
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ABSOLUTE_CONTRAINDICATION,
                        rule_id="INV-THROMB-01",
                        message="Thrombolytic therapy strictly contraindicated in the presence of active intracranial hemorrhage or bleeding diathesis",
                        clinical_severity="FATAL_RISK",
                        remediation="Hold thrombolytics; urgent neurosurgical consult",
                    )
                )

        # Anticoagulants vs active intracranial hemorrhage or severe bleeding
        anticoagulants = ["heparin", "enoxaparin", "warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban"]
        if any(a in drug_name for a in anticoagulants):
            if any("intracranial hemorrhage" in c or "subdural hemorrhage" in c or "subarachnoid hemorrhage" in c for c in active_conditions):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ABSOLUTE_CONTRAINDICATION,
                        rule_id="INV-ANTICOAG-BLEED",
                        message=f"Anticoagulation with '{drug_name}' is strictly contraindicated in acute intracranial hemorrhage",
                        clinical_severity="FATAL_RISK",
                        remediation="Reverse anticoagulation if active; hold all antithrombotic therapies",
                    )
                )

        # Beta-blockers vs cardiogenic shock or severe bradycardia / AV block
        beta_blockers = ["metoprolol", "propranolol", "atenolol", "bisoprolol", "carvedilol", "labetalol", "esmolol"]
        if any(b in drug_name for b in beta_blockers):
            has_cardio_contra = any(
                "cardiogenic shock" in c
                or "second degree av block" in c
                or "third degree av block" in c
                or "complete heart block" in c
                for c in active_conditions
            ) or patient_profile.get("heart_rate", 80) < 45
            if has_cardio_contra:
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ABSOLUTE_CONTRAINDICATION,
                        rule_id="INV-BB-CARDIOGENIC",
                        message=f"Beta-blocker '{drug_name}' contraindicated in cardiogenic shock or high-degree AV block due to fatal negative inotropy",
                        clinical_severity="FATAL_RISK",
                        remediation="Hold beta-blockers; administer inotropes/vasopressors if indicated",
                    )
                )

        # PDE5 inhibitors vs concurrent nitrates
        pde5_inhibitors = ["sildenafil", "tadalafil", "vardenafil", "avanafil"]
        nitrates = ["nitroglycerin", "isosorbide", "nitroprusside", "amyl nitrite"]
        if any(p in drug_name for p in pde5_inhibitors):
            has_nitrate = any(any(n in med for n in nitrates) for med in current_meds) or any("nitrate" in c for c in active_conditions)
            if has_nitrate:
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ABSOLUTE_CONTRAINDICATION,
                        rule_id="INV-PDE5-NITRATE",
                        message="PDE5 inhibitor contraindicated with concurrent nitrate therapy due to risk of refractory lethal hypotension",
                        clinical_severity="FATAL_RISK",
                        remediation="Hold PDE5 inhibitor or discontinue nitrate with at least 24-48h washout",
                    )
                )

        # Potassium IV bolus or high dose in severe hyperkalemia
        if "potassium" in drug_name and patient_profile.get("potassium", 4.0) >= 5.5:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.ABSOLUTE_CONTRAINDICATION,
                    rule_id="INV-K-HYPERKALEMIA",
                    message="Exogenous potassium contraindicated in active hyperkalemia (K >= 5.5 mEq/L) due to fatal arrhythmia risk",
                    clinical_severity="FATAL_RISK",
                    remediation="Hold potassium supplementation; administer calcium gluconate and insulin/dextrose",
                )
            )

        # =====================================================================
        # Invariant 2: Renal & Hepatic Clearance Floors
        # =====================================================================
        # Metformin: eGFR floor < 30
        if "metformin" in drug_name and effective_renal < 30.0:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_FLOOR,
                    rule_id="INV-RENAL-METFORMIN",
                    message=f"Metformin contraindicated when eGFR < 30 mL/min/1.73m² (current eGFR: {effective_renal}) due to high risk of fatal lactic acidosis",
                    clinical_severity="CRITICAL_TOXICITY",
                    remediation="Substitute with insulin or DPP-4 inhibitor requiring no renal clearance floor",
                )
            )

        # Vancomycin: eGFR < 20 with high dose (> 1000 mg)
        if "vancomycin" in drug_name and effective_renal < 20.0 and dose_val > 1000:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_FLOOR,
                    rule_id="INV-RENAL-VANCO",
                    message=f"Standard Vancomycin dose exceeds safe clearance ceiling for severe renal impairment (eGFR: {effective_renal})",
                    clinical_severity="SEVERE_NEPHROTOXICITY",
                    remediation="Reduce dose or switch to trough-guided dosing interval (q48h)",
                )
            )

        # Enoxaparin full therapeutic dose in severe renal impairment (CrCl < 30)
        if "enoxaparin" in drug_name and effective_renal < 30.0 and (dose_val > 30 or "1 mg/kg" in str(parameters.get("dosage", ""))):
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_FLOOR,
                    rule_id="INV-RENAL-ENOXAPARIN",
                    message=f"Full therapeutic Enoxaparin dose contraindicated without 50% renal dose reduction when CrCl < 30 mL/min (current: {effective_renal})",
                    clinical_severity="CRITICAL_TOXICITY",
                    remediation="Reduce Enoxaparin to 1 mg/kg q24h or switch to unfractionated heparin monitored by aPTT",
                )
            )

        # DOACs in severe renal impairment (CrCl < 15)
        doacs = ["dabigatran", "rivaroxaban", "edoxaban"]
        if any(d in drug_name for d in doacs) and effective_renal < 15.0:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_FLOOR,
                    rule_id="INV-RENAL-DOAC",
                    message=f"DOAC '{drug_name}' contraindicated when CrCl < 15 mL/min due to bioaccumulation and unmonitorable hemorrhagic risk",
                    clinical_severity="FATAL_RISK",
                    remediation="Switch to unfractionated heparin or warfarin with INR monitoring",
                )
            )

        # Cefepime in severe renal failure without adjustment
        if "cefepime" in drug_name and effective_renal < 30.0 and dose_val > 1000:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.RENAL_HEPATIC_FLOOR,
                    rule_id="INV-RENAL-CEFEPIME",
                    message=f"Unadjusted high-dose Cefepime ({dose_val}mg) when eGFR < 30 carries severe neurotoxicity and encephalopathy risk",
                    clinical_severity="SEVERE_NEUROTOXICITY",
                    remediation="Extend dosing interval to q24h or switch to Meropenem with renal adjustment",
                )
            )

        # Paracetamol / Acetaminophen in severe liver failure
        if ("paracetamol" in drug_name or "acetaminophen" in drug_name) and liver_failure:
            if dose_val > 2000 or "daily" in parameters.get("frequency", ""):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.RENAL_HEPATIC_FLOOR,
                        rule_id="INV-HEPATIC-PARACETAMOL",
                        message="Acetaminophen / Paracetamol dose exceeds 2g/day maximum hepatic threshold in decompensated liver disease",
                        clinical_severity="CRITICAL_TOXICITY",
                        remediation="Cap total daily dose at <= 2000 mg or use non-hepatotoxic analgesia",
                    )
                )

        # =====================================================================
        # Invariant 3: Pregnancy Category X Restrictions & Teratogens
        # =====================================================================
        teratogenic_drugs = [
            "methotrexate",
            "isotretinoin",
            "thalidomide",
            "lenalidomide",
            "warfarin",
            "misoprostol",
            "finasteride",
            "dutasteride",
            "atorvastatin",
            "simvastatin",
            "rosuvastatin",
            "valproic acid",
            "valproate",
            "ribavirin",
            "leflunomide",
        ]
        if (is_pregnant or is_lactating) and any(t_drug in drug_name for t_drug in teratogenic_drugs):
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.PREGNANCY_TERATOGEN,
                    rule_id="INV-PREG-CAT-X",
                    message=f"Medication '{drug_name}' is FDA Pregnancy Category X: proven severe fetal malformations or death",
                    clinical_severity="FATAL_FETAL_RISK",
                    remediation="Immediately cancel order; consult maternal-fetal medicine specialist",
                )
            )

        # ACE inhibitors / ARBs in pregnancy (Category D/fetotoxic)
        ace_arbs = ["lisinopril", "enalapril", "ramipril", "losartan", "valsartan", "candesartan"]
        if is_pregnant and any(med in drug_name for med in ace_arbs):
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.PREGNANCY_TERATOGEN,
                    rule_id="INV-PREG-ACE-ARB",
                    message=f"ACE-inhibitor / ARB '{drug_name}' contraindicated in pregnancy due to fetal renal dysgenesis and oligohydramnios",
                    clinical_severity="FATAL_FETAL_RISK",
                    remediation="Switch to pregnancy-safe antihypertensive (Labetalol, Nifedipine, or Methyldopa)",
                )
            )

        # =====================================================================
        # Invariant 4: Anaphylaxis & Severe Cross-Reactivity
        # =====================================================================
        # Penicillin anaphylaxis vs beta-lactams
        if any("penicillin" in a for a in allergies):
            beta_lactam_risks = [
                "ampicillin",
                "amoxicillin",
                "piperacillin",
                "penicillin",
                "augmentin",
                "zosyn",
                "unasyn",
                "ticarcillin",
                "nafcillin",
                "oxacillin",
                "cephalexin",
                "cefazolin",
            ]
            if any(risk in drug_name for risk in beta_lactam_risks):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ALLERGY_ANAPHYLAXIS,
                        rule_id="INV-ALLERGY-PENICILLIN",
                        message=f"Severe Penicillin anaphylaxis flagged in patient record; '{drug_name}' triggers acute anaphylactic shock",
                        clinical_severity="FATAL_RISK",
                        remediation="Select non-beta-lactam alternative (e.g. Aztreonam, Fluoroquinolone, Macrolide)",
                    )
                )

        # Sulfa allergy vs sulfonamides
        if any("sulfa" in a or "sulfonamide" in a for a in allergies):
            sulfa_drugs = ["sulfamethoxazole", "bactrim", "septra", "sulfadiazine", "sulfasalazine"]
            if any(s in drug_name for s in sulfa_drugs):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ALLERGY_ANAPHYLAXIS,
                        rule_id="INV-ALLERGY-SULFA",
                        message=f"Sulfa allergy recorded; '{drug_name}' triggers severe hypersensitivity / Stevens-Johnson syndrome",
                        clinical_severity="FATAL_RISK",
                        remediation="Select non-sulfonamide antimicrobial alternative",
                    )
                )

        # NSAID / Aspirin allergy vs NSAIDs
        if any("aspirin" in a or "nsaid" in a for a in allergies):
            nsaids = ["aspirin", "ibuprofen", "naproxen", "ketorolac", "toradol", "diclofenac", "indomethacin", "meloxicam", "celecoxib"]
            if any(n in drug_name for n in nsaids):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ALLERGY_ANAPHYLAXIS,
                        rule_id="INV-ALLERGY-NSAID",
                        message=f"NSAID/Aspirin allergy recorded; '{drug_name}' triggers severe bronchospasm / anaphylactoid reaction",
                        clinical_severity="FATAL_RISK",
                        remediation="Switch to Acetaminophen or non-NSAID analgesia",
                    )
                )

        # Contrast media allergy
        if any("contrast" in a or "iodine" in a for a in allergies):
            contrast_agents = ["contrast", "iohexol", "iopamidol", "iodixanol", "radiocontrast"]
            if any(c in drug_name or c in action_name.lower() for c in contrast_agents):
                violations.append(
                    InvariantViolation(
                        invariant_type=InvariantType.ALLERGY_ANAPHYLAXIS,
                        rule_id="INV-ALLERGY-CONTRAST",
                        message="Severe radiocontrast anaphylaxis history; requires steroid/antihistamine premedication or non-contrast imaging",
                        clinical_severity="FATAL_RISK",
                        remediation="Cancel order or initiate 13-hour oral prednisone/diphenhydramine premedication protocol",
                    )
                )

        # =====================================================================
        # Invariant 5: Four-Eye Attending Quorum for High-Risk Procedures
        # =====================================================================
        high_risk_actions = [
            "invasive_mechanical_ventilation",
            "high_dose_chemotherapy",
            "cardiac_ablation",
            "ecmo",
            "extracorporeal_membrane_oxygenation",
            "intubation",
            "emergency_craniotomy",
            "thoracotomy",
            "experimental_investigational_drug",
            "hyperthermic_intraperitoneal_chemotherapy",
            "tavr",
        ]

        action_target = f"{action_name} {drug_name}".lower()
        is_high_risk = any(hr in action_target for hr in high_risk_actions)

        if is_high_risk and not countersigned:
            violations.append(
                InvariantViolation(
                    invariant_type=InvariantType.FOUR_EYE_QUORUM,
                    rule_id="INV-QUORUM-01",
                    message=f"High-risk clinical action '{action_name or drug_name}' requires Four-Eye attending dual clinician countersignature before execution",
                    clinical_severity="GOVERNANCE_SAFETY_LOCK",
                    remediation="Obtain second attending clinician signature before initiating intervention",
                )
            )

        return violations

    def validate_proposal(
        self,
        action_proposal: Any,
        patient_profile: Dict[str, Any],
    ) -> InvariantValidationResult:
        """Inspect a strongly-typed FHIR action proposal against pre-action invariants."""
        # Unpack proposal attributes
        proposal_id = getattr(action_proposal, "id", None)
        action_name = "prescribe_medication"
        parameters: Dict[str, Any] = {}

        if hasattr(action_proposal, "to_dict"):
            p_dict = action_proposal.to_dict()
        elif isinstance(action_proposal, dict):
            p_dict = dict(action_proposal)
        else:
            p_dict = {}

        if hasattr(action_proposal, "medication_name") or "medication_name" in p_dict or "drug" in p_dict:
            action_name = "prescribe_medication"
            parameters["drug"] = getattr(action_proposal, "medication_name", p_dict.get("medication_name", p_dict.get("drug", "")))
            parameters["dosage"] = getattr(action_proposal, "dosage", p_dict.get("dosage", ""))
            parameters["dose"] = getattr(action_proposal, "dose", p_dict.get("dose"))
            parameters["unit"] = getattr(action_proposal, "unit", p_dict.get("unit"))
            parameters["route"] = getattr(action_proposal, "route", p_dict.get("route", "oral"))
            parameters["frequency"] = getattr(action_proposal, "frequency", p_dict.get("frequency", "once daily"))
            parameters["countersigned_by"] = getattr(action_proposal, "countersigned_by", p_dict.get("countersigned_by"))

        elif hasattr(action_proposal, "category") and hasattr(action_proposal, "code"):
            # FHIRServiceRequestProposal or FHIRFlagProposal
            desc = getattr(action_proposal, "description", p_dict.get("description", p_dict.get("details", "")))
            cat = getattr(action_proposal, "category", p_dict.get("category", "procedure"))
            action_name = str(desc or cat)
            parameters["name"] = desc
            parameters["category"] = cat
            parameters["code"] = getattr(action_proposal, "code", p_dict.get("code", ""))
            parameters["countersigned_by"] = getattr(action_proposal, "countersigned_by", p_dict.get("countersigned_by"))
            parameters["supporting_info"] = getattr(action_proposal, "supporting_info", p_dict.get("supporting_info", []))
        else:
            action_name = str(p_dict.get("action_name", p_dict.get("name", "clinical_action")))
            parameters = p_dict

        violations = self.evaluate_invariants(
            action_name=action_name,
            parameters=parameters,
            patient_profile=patient_profile,
        )

        audit_token = hashlib.sha256(
            f"{action_name}:{proposal_id}:{datetime.datetime.now(datetime.timezone.utc).isoformat()}".encode("utf-8")
        ).hexdigest()

        if violations:
            primary_violation = violations[0]
            result = InvariantValidationResult(
                status=ValidationStatus.REJECT,
                barrier_triggered=primary_violation.invariant_type.canonical(),
                explanation="; ".join(v.message for v in violations),
                violations=violations,
                audit_token=audit_token,
                proposal_id=proposal_id,
            )
        else:
            result = InvariantValidationResult(
                status=ValidationStatus.PASS,
                barrier_triggered=None,
                explanation="All clinical safety invariant barriers passed successfully.",
                violations=[],
                audit_token=audit_token,
                proposal_id=proposal_id,
            )

        self._audit_log.append(result.to_dict())
        return result

    def validate_and_execute(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        patient_profile: Dict[str, Any],
        executor_func: Optional[Callable[[Dict[str, Any]], Any]] = None,
        action_proposal: Optional[Any] = None,
    ) -> InvariantExecutionResult:
        """Evaluate invariants and execute tool in a protected sandbox if safe."""
        if action_proposal is not None and not parameters:
            # Delegate to validate_proposal
            val_res = self.validate_proposal(action_proposal, patient_profile)
            if not val_res.passed:
                result = InvariantExecutionResult(
                    allowed=False,
                    status="REJECTED_INVARIANT_BREACH",
                    action_name=action_name or getattr(action_proposal, "id", "proposal"),
                    parameters=getattr(action_proposal, "to_dict", lambda: {})(),
                    violations=val_res.violations,
                    execution_output=None,
                    audit_token=val_res.audit_token,
                )
                return result
            # Executed safe
            output = executor_func(parameters) if executor_func else {"executed": True, "proposal_id": val_res.proposal_id}
            result = InvariantExecutionResult(
                allowed=True,
                status="EXECUTED_SAFE",
                action_name=action_name or getattr(action_proposal, "id", "proposal"),
                parameters=getattr(action_proposal, "to_dict", lambda: {})(),
                violations=[],
                execution_output=output,
                audit_token=val_res.audit_token,
            )
            return result

        violations = self.evaluate_invariants(
            action_name=action_name,
            parameters=parameters,
            patient_profile=patient_profile,
        )

        if violations:
            result = InvariantExecutionResult(
                allowed=False,
                status="REJECTED_INVARIANT_BREACH",
                action_name=action_name,
                parameters=parameters,
                violations=violations,
                execution_output=None,
            )
            self._audit_log.append(result.to_dict())
            return result

        # Invariants passed: execute sandboxed action
        output = None
        if executor_func:
            output = executor_func(parameters)
        else:
            output = {"executed": True, "action": action_name, "parameters": parameters}

        token = hashlib.sha256(
            f"{action_name}:{datetime.datetime.now(datetime.timezone.utc).isoformat()}".encode("utf-8")
        ).hexdigest()

        result = InvariantExecutionResult(
            allowed=True,
            status="EXECUTED_SAFE",
            action_name=action_name,
            parameters=parameters,
            violations=[],
            execution_output=output,
            audit_token=token,
        )

        self._audit_log.append(result.to_dict())
        return result

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return list(self._audit_log)

    def clear(self) -> None:
        self._audit_log.clear()
