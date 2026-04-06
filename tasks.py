"""Medical Prior Authorization OpenEnv - Task scenarios and clinical guidelines."""

CLINICAL_GUIDELINES = {
    "GL-KNEE-MRI-001": {
        "name": "Knee MRI for ACL Injury",
        "procedure_codes": ["73721"],
        "diagnosis_codes": ["M23.611"],
        "criteria": [
            "documented_knee_instability OR positive_lachman_test",
            "failed_conservative_treatment_4_plus_weeks",
        ],
        "auto_approve_if_criteria_met": True,
    },
    "GL-BIOLOGIC-001": {
        "name": "Biologic Therapy - Humira/Adalimumab for Crohn's Disease",
        "procedure_codes": ["J0135"],
        "diagnosis_codes": ["K50.10"],
        "criteria": [
            "documented_failure_of_2_plus_conventional_therapies",
            "conventional_therapies_include_corticosteroids_and_immunomodulators",
            "moderate_to_severe_disease_activity_CDAI_greater_than_220",
        ],
        "auto_approve_if_criteria_met": False,
    },
    "GL-SPINE-FUSION-001": {
        "name": "Spinal Fusion Surgery",
        "procedure_codes": ["22612"],
        "diagnosis_codes": ["M47.816", "M54.5"],
        "criteria": [
            "failed_conservative_treatment_6_plus_months",
            "documented_structural_instability_on_imaging",
            "no_active_infection",
            "BMI_less_than_40",
        ],
        "auto_approve_if_criteria_met": False,
    },
    "GL-SPINE-FUSION-002": {
        "name": "Spinal Fusion - Alternative Criteria",
        "procedure_codes": ["22612"],
        "diagnosis_codes": ["M47.816", "M54.5"],
        "criteria": [
            "failed_conservative_treatment_3_plus_months",
            "neurological_deficit_present",
            "no_contraindication_to_general_anesthesia",
        ],
        "auto_approve_if_criteria_met": False,
    },
}

FORMULARY = {
    "adalimumab": {
        "tier": "specialty",
        "requires_pa": True,
        "step_therapy_required": True,
        "alternatives": ["infliximab", "vedolizumab"],
    },
}

TASKS = {
    "easy_knee_mri": {
        "request": {
            "request_id": "PA-2024-001",
            "patient": {"age": 45, "gender": "M", "plan_id": "PPO-500"},
            "diagnosis": ["M23.611"],
            "procedure": "73721",
            "clinical_notes": (
                "45-year-old male presents with left knee injury sustained during recreational "
                "basketball three days ago. Patient reports hearing a pop followed by immediate "
                "swelling and inability to bear weight. Physical examination reveals significant "
                "joint effusion and a positive Lachman test with no firm endpoint, consistent "
                "with ACL disruption. Anterior drawer test also positive. Valgus stress test "
                "negative, suggesting intact MCL. Patient was placed in a hinged knee brace and "
                "referred to physical therapy six weeks ago. Despite completing a full course of "
                "supervised PT including quadriceps strengthening and range-of-motion exercises, "
                "the patient continues to experience giving-way episodes and functional "
                "instability. NSAID therapy with naproxen provided minimal relief. MRI is "
                "requested to confirm the extent of ligamentous injury and evaluate for "
                "concurrent meniscal pathology prior to surgical planning."
            ),
            "prior_treatments": ["physical_therapy_6_weeks", "nsaid_therapy"],
            "attachments": ["orthopedic_evaluation", "pt_progress_notes", "mri_order"],
        },
        "ground_truth": {
            "decision": "approve",
            "required_criteria": ["GL-KNEE-MRI-001"],
            "required_missing_fields": [],
            "denial_reason_code": None,
        },
    },
    "medium_humira": {
        "request": {
            "request_id": "PA-2024-002",
            "patient": {"age": 32, "gender": "F", "plan_id": "HMO-250"},
            "diagnosis": ["K50.10"],
            "procedure": "J0135",
            "clinical_notes": (
                "32-year-old female with Crohn's disease diagnosed three years ago, presenting "
                "with worsening symptoms despite current therapy. Patient initially trialed "
                "mesalamine for eight months with inadequate response and continued bloody "
                "diarrhea. She was subsequently started on prednisone 40mg with taper, which "
                "provided temporary relief but symptoms flare upon dose reduction below 15mg. "
                "Current CDAI score is 285, indicating moderate-to-severe disease activity. "
                "Recent colonoscopy shows deep ulcerations in the terminal ileum and ascending "
                "colon. Labs reveal elevated CRP at 28 mg/L and ESR 45. Patient mentions a "
                "previous biologic trial at an outside facility but records have not been "
                "obtained. Requesting authorization for adalimumab (Humira) 160mg induction "
                "followed by standard maintenance dosing. Step therapy with immunomodulators "
                "has not been formally documented in available records."
            ),
            "prior_treatments": ["mesalamine", "prednisone"],
            "attachments": ["gi_consultation", "lab_results"],
        },
        "ground_truth": {
            "decision": "request_info",
            "required_criteria": ["GL-BIOLOGIC-001"],
            "required_missing_fields": [
                "step_therapy_documentation",
                "prior_biologic_records",
            ],
            "denial_reason_code": None,
        },
    },
    "hard_spinal_fusion": {
        "request": {
            "request_id": "PA-2024-003",
            "patient": {"age": 58, "gender": "M", "plan_id": "PPO-1000"},
            "diagnosis": ["M47.816", "M54.5"],
            "procedure": "22612",
            "clinical_notes": (
                "58-year-old male with progressive lumbar spondylosis and chronic low back pain "
                "refractory to extensive conservative management over the past eight months. "
                "Patient initially underwent a structured physical therapy program focusing on "
                "core stabilization and lumbar flexibility for the full eight-month period with "
                "only marginal improvement. He received three lumbar epidural steroid injections "
                "at L4-L5 level at six-week intervals, each providing less than two weeks of "
                "partial relief. Concurrent pharmacotherapy included naproxen 500mg BID and "
                "gabapentin titrated to 1800mg daily for radicular symptoms, with limited "
                "efficacy and dose-limiting side effects including dizziness.\n\n"
                "Advanced imaging including MRI and CT myelogram demonstrates moderate-to-severe "
                "central canal stenosis at L4-L5 with bilateral foraminal narrowing. There is "
                "evidence of grade I degenerative spondylolisthesis with dynamic instability "
                "confirmed on flexion-extension radiographs showing 4mm of translation. "
                "Neurology consultation confirms bilateral L5 radiculopathy with diminished "
                "ankle reflexes and mild foot drop on the left. EMG/NCS studies corroborate "
                "active L5 nerve root compromise bilaterally. Patient was recently treated for "
                "MRSA wound infection, completed IV vancomycin course 2 weeks ago, wound "
                "cultures pending final clearance. The patient's current BMI is 38, and he has "
                "been counseled on weight management with a target of BMI below 35 prior to "
                "elective surgery.\n\n"
                "Given the failure of prolonged conservative measures, documented structural "
                "instability, and progressive neurological deficits, the treating spine surgeon "
                "recommends L4-L5 posterior lumbar interbody fusion with pedicle screw "
                "instrumentation. The surgical team has reviewed the case and believes the "
                "patient meets criteria for intervention. Pre-operative cardiac clearance has "
                "been obtained. Anesthesiology has evaluated the patient and notes no "
                "contraindication to general anesthesia aside from standard obesity-related "
                "precautions. The procedure is planned as an inpatient surgery with an "
                "anticipated three-to-four day hospital stay."
            ),
            "prior_treatments": [
                "physical_therapy_8_months",
                "epidural_injections_x3",
                "nsaid_therapy",
                "gabapentin",
            ],
            "attachments": [
                "spine_imaging",
                "neurology_consult",
                "pain_management_records",
            ],
        },
        "ground_truth": {
            "decision": "deny",
            "required_criteria": ["GL-SPINE-FUSION-001", "GL-SPINE-FUSION-002"],
            "required_missing_fields": [],
            "denial_reason_code": "CONTRAINDICATION_ACTIVE_INFECTION",
            "contraindication": "active_infection_mrsa",
        },
    },
}

PATIENT_HISTORIES = {
    "PPO-500": {
        "prior_authorizations": [
            {"request_id": "PA-2023-044", "procedure": "99213", "decision": "approve", "date": "2023-08-15"},
        ],
        "chronic_conditions": ["hypertension"],
    },
    "HMO-250": {
        "prior_authorizations": [
            {"request_id": "PA-2023-112", "procedure": "43239", "decision": "approve", "date": "2023-05-20"},
            {"request_id": "PA-2024-001", "procedure": "J0135", "decision": "pending", "date": "2024-01-10"},
        ],
        "chronic_conditions": ["crohns_disease", "iron_deficiency_anemia"],
    },
    "PPO-1000": {
        "prior_authorizations": [
            {"request_id": "PA-2023-078", "procedure": "62322", "decision": "approve", "date": "2023-03-10"},
            {"request_id": "PA-2023-091", "procedure": "62322", "decision": "approve", "date": "2023-06-22"},
            {"request_id": "PA-2023-105", "procedure": "62322", "decision": "approve", "date": "2023-09-04"},
        ],
        "chronic_conditions": ["lumbar_spondylosis", "chronic_low_back_pain", "hypertension", "obesity"],
    },
}
