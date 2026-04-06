"""Medical Prior Authorization OpenEnv - Task scenarios, clinical guidelines, and formulary."""

CLINICAL_GUIDELINES = {
    "GL-KNEE-MRI-001": {
        "id": "GL-KNEE-MRI-001",
        "title": "MRI of the Knee for Suspected Ligament Injury",
        "name": "Knee MRI for ACL Injury",
        "procedure_codes": ["73721", "73722"],
        "diagnosis_codes": ["S83.511A", "S83.512A", "M23.611", "M23.612"],
        "criteria": [
            "documented_knee_instability OR positive_lachman_test",
            "failed_conservative_treatment_4_plus_weeks OR acute_traumatic_injury",
        ],
        "required_documents": ["clinical_notes", "physical_exam_report"],
        "auto_approve_if_criteria_met": True,
        "step_therapy_required": False,
        "notes": "Approval is straightforward when clinical exam documents ACL injury with positive Lachman test.",
    },
    "GL-BIOLOGIC-001": {
        "id": "GL-BIOLOGIC-001",
        "title": "Adalimumab (Humira) for Crohn's Disease",
        "name": "Biologic Therapy - Humira/Adalimumab for Crohn's Disease",
        "procedure_codes": ["J0135"],
        "diagnosis_codes": ["K50.00", "K50.10", "K50.80", "K50.90"],
        "criteria": [
            "documented_failure_of_2_plus_conventional_therapies",
            "conventional_therapies_include_corticosteroids_and_immunomodulators",
            "moderate_to_severe_disease_activity_CDAI_greater_than_220",
            "no_active_untreated_infections_TB_screening_required",
        ],
        "required_documents": ["clinical_notes", "prior_treatment_records", "tb_screening_results", "step_therapy_documentation"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": True,
        "notes": "Requires documented failure of 2 conventional therapies before biologic approval.",
    },
    "GL-SPINE-FUSION-001": {
        "id": "GL-SPINE-FUSION-001",
        "title": "Lumbar Spinal Fusion for Degenerative Disc Disease",
        "name": "Spinal Fusion Surgery",
        "procedure_codes": ["22612", "22630", "22633"],
        "diagnosis_codes": ["M51.16", "M51.17", "M47.816", "M47.817", "M54.5"],
        "criteria": [
            "failed_conservative_treatment_6_plus_months",
            "documented_structural_instability_on_imaging",
            "psychological_evaluation_completed_if_chronic_pain_over_12_months",
            "no_active_contraindications_uncontrolled_diabetes_HbA1c_over_8_active_smoking_BMI_over_40",
            "concordant_findings_between_imaging_and_clinical_symptoms",
        ],
        "required_documents": ["clinical_notes", "imaging_reports", "physical_therapy_records", "pain_management_records", "psychological_evaluation"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": True,
        "notes": "Complex case. Multiple criteria must be met. Contraindications in clinical notes must be identified.",
    },
    "GL-SPINE-FUSION-002": {
        "id": "GL-SPINE-FUSION-002",
        "title": "Lumbar Spinal Fusion — Alternative Criteria (Network B)",
        "name": "Spinal Fusion - Alternative Criteria",
        "procedure_codes": ["22612", "22630", "22633"],
        "diagnosis_codes": ["M51.16", "M51.17", "M47.816", "M47.817", "M54.5"],
        "criteria": [
            "failed_conservative_treatment_3_plus_months",
            "neurological_deficit_present",
            "no_contraindication_to_general_anesthesia",
            "BMI_less_than_35",
        ],
        "required_documents": ["clinical_notes", "imaging_reports", "physical_therapy_records"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": False,
        "notes": "Network B has shorter conservative treatment requirement but stricter BMI cutoff (35 vs 40).",
    },
    "GL-CHEST-XRAY-001": {
        "id": "GL-CHEST-XRAY-001",
        "title": "Chest X-Ray for Persistent Cough",
        "name": "Chest X-Ray for Persistent Cough",
        "procedure_codes": ["71046"],
        "diagnosis_codes": ["R05.9"],
        "criteria": [
            "cough_persisting_greater_than_3_weeks",
            "failed_empiric_treatment",
        ],
        "required_documents": ["clinical_notes", "medication_history"],
        "auto_approve_if_criteria_met": True,
        "step_therapy_required": False,
        "notes": "Simple approval when cough duration and failed empiric treatment are documented.",
    },
    "GL-PT-EVAL-001": {
        "id": "GL-PT-EVAL-001",
        "title": "Physical Therapy Evaluation - Shoulder",
        "name": "Physical Therapy Evaluation - Shoulder",
        "procedure_codes": ["97161"],
        "diagnosis_codes": ["M75.111"],
        "criteria": [
            "documented_rotator_cuff_pathology",
            "pain_limiting_daily_activities",
        ],
        "required_documents": ["clinical_notes", "mri_report", "orthopedic_referral"],
        "auto_approve_if_criteria_met": True,
        "step_therapy_required": False,
        "notes": "Clear approval with MRI-confirmed pathology and functional limitation.",
    },
    "GL-GLP1-001": {
        "id": "GL-GLP1-001",
        "title": "GLP-1 Agonist for Type 2 Diabetes with Obesity",
        "name": "GLP-1 Agonist for Type 2 Diabetes with Obesity",
        "procedure_codes": ["J3490"],
        "diagnosis_codes": ["E11.65", "E66.01"],
        "criteria": [
            "BMI_greater_than_30_or_27_with_comorbidity",
            "documented_failure_of_lifestyle_modification_6_months",
            "documented_failure_of_metformin_or_contraindication",
            "HbA1c_greater_than_7",
        ],
        "required_documents": ["clinical_notes", "endocrinology_notes", "dietitian_records", "lab_results"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": True,
        "notes": "Requires complete lifestyle modification records and metformin trial/intolerance documentation.",
    },
    "GL-SLEEP-001": {
        "id": "GL-SLEEP-001",
        "title": "Polysomnography for Suspected OSA",
        "name": "Polysomnography for Suspected OSA",
        "procedure_codes": ["95810"],
        "diagnosis_codes": ["G47.33"],
        "criteria": [
            "epworth_sleepiness_scale_greater_than_10",
            "documented_snoring_or_witnessed_apneas",
            "failed_home_sleep_test_or_complex_comorbidities",
        ],
        "required_documents": ["clinical_notes", "sleep_medicine_referral", "failed_hsat_report"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": False,
        "notes": "Approve despite failed prior home test when valid clinical justification exists.",
    },
    "GL-CARDIAC-CATH-001": {
        "id": "GL-CARDIAC-CATH-001",
        "title": "Cardiac Catheterization for Acute Coronary Syndrome",
        "name": "Cardiac Catheterization for Acute Coronary Syndrome",
        "procedure_codes": ["93458"],
        "diagnosis_codes": ["I25.10", "I20.0"],
        "criteria": [
            "positive_stress_test_or_troponin_elevation",
            "refractory_angina_despite_medical_therapy",
            "no_active_bleeding",
            "eGFR_greater_than_30",
        ],
        "required_documents": ["clinical_notes", "stress_test_report", "lab_results", "cardiology_notes"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": False,
        "notes": "Must verify no active bleeding and adequate renal function before approval.",
    },
    "GL-CARDIAC-CATH-002": {
        "id": "GL-CARDIAC-CATH-002",
        "title": "Cardiac Catheterization - Elective Criteria",
        "name": "Cardiac Catheterization - Elective Criteria",
        "procedure_codes": ["93458"],
        "diagnosis_codes": ["I25.10"],
        "criteria": [
            "documented_ischemia_on_noninvasive_testing",
            "failed_optimal_medical_therapy_3_months",
            "LVEF_assessment_completed",
        ],
        "required_documents": ["clinical_notes", "stress_test_report", "echocardiogram_report"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": False,
        "notes": "Elective pathway requires documented ischemia and failed optimal medical therapy.",
    },
    "GL-GENE-THERAPY-001": {
        "id": "GL-GENE-THERAPY-001",
        "title": "Gene Therapy - Zolgensma for SMA",
        "name": "Gene Therapy - Zolgensma for SMA",
        "procedure_codes": ["J3399"],
        "diagnosis_codes": ["G12.0", "G12.1"],
        "criteria": [
            "confirmed_SMN1_gene_deletion_or_mutation",
            "age_less_than_2_years",
            "no_advanced_respiratory_failure",
            "anti_AAV9_antibody_titer_below_threshold",
            "no_active_hepatic_disease",
        ],
        "required_documents": ["clinical_notes", "genetic_testing_report", "hepatology_consult", "aav9_antibody_results", "pulmonary_function"],
        "auto_approve_if_criteria_met": False,
        "step_therapy_required": False,
        "notes": "High-stakes $2.1M gene therapy. Must verify hepatic function and AAV9 antibody titer.",
    },
}


FORMULARY = {
    "adalimumab": {
        "brand_name": "Humira",
        "generic_name": "adalimumab",
        "tier": 4,
        "requires_pa": True,
        "step_therapy": ["mesalamine", "azathioprine"],
        "status": "covered_with_pa",
        "alternatives": ["infliximab", "vedolizumab"],
    },
    "infliximab": {
        "brand_name": "Remicade",
        "generic_name": "infliximab",
        "tier": 4,
        "requires_pa": True,
        "step_therapy": ["mesalamine", "azathioprine"],
        "status": "covered_with_pa",
        "alternatives": ["adalimumab", "vedolizumab"],
    },
    "mesalamine": {
        "brand_name": "Asacol",
        "generic_name": "mesalamine",
        "tier": 2,
        "requires_pa": False,
        "step_therapy": [],
        "status": "covered",
        "alternatives": [],
    },
    "semaglutide": {
        "brand_name": "Ozempic",
        "generic_name": "semaglutide",
        "tier": 4,
        "requires_pa": True,
        "step_therapy": ["metformin", "glipizide"],
        "status": "covered_with_pa",
        "alternatives": ["liraglutide", "tirzepatide"],
    },
    "onasemnogene": {
        "brand_name": "Zolgensma",
        "generic_name": "onasemnogene abeparvovec",
        "tier": 5,
        "requires_pa": True,
        "step_therapy": [],
        "status": "covered_with_pa",
        "alternatives": ["nusinersen", "risdiplam"],
    },
}


TASKS = {
    # ── EASY ──────────────────────────────────────────────
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
            "key_findings": [
                "positive Lachman test",
                "ACL disruption",
                "completed 6 weeks PT with persistent instability",
            ],
        },
        "patient_history": {
            "history": "No prior orthopedic PA requests. Hypertension managed medically.",
            "prior_auths": [
                {"request_id": "PA-2023-044", "procedure": "99213", "decision": "approve", "date": "2023-08-15"},
            ],
        },
    },
    "easy_chest_xray": {
        "request": {
            "request_id": "PA-2024-004",
            "patient": {"age": 62, "gender": "F", "plan_id": "HMO-100"},
            "diagnosis": ["R05.9"],
            "procedure": "71046",
            "clinical_notes": (
                "62-year-old female presents with persistent productive cough for five weeks. "
                "Initially treated empirically with a 10-day course of amoxicillin-clavulanate "
                "for suspected community-acquired pneumonia with no improvement. A subsequent "
                "trial of inhaled corticosteroids and albuterol for possible reactive airway "
                "disease also failed to resolve symptoms. Patient is a never-smoker with no "
                "occupational exposures. Vital signs are stable, oxygen saturation 97% on room "
                "air. Auscultation reveals diminished breath sounds at the right base. Given "
                "the duration of symptoms and failure of empiric therapy, a two-view chest "
                "X-ray is requested to evaluate for underlying pathology including mass, "
                "effusion, or chronic infection."
            ),
            "prior_treatments": ["antibiotics_10_days", "inhaled_corticosteroids"],
            "attachments": ["pcp_notes", "medication_history"],
        },
        "ground_truth": {
            "decision": "approve",
            "required_criteria": ["GL-CHEST-XRAY-001"],
            "required_missing_fields": [],
            "denial_reason_code": None,
            "key_findings": [
                "cough persisting 5 weeks (>3 week threshold)",
                "failed empiric antibiotics",
                "failed inhaled corticosteroids",
            ],
        },
        "patient_history": {
            "history": "No prior PA requests. Chronic conditions: hypertension, osteoarthritis.",
            "prior_auths": [],
        },
    },
    "easy_pt_eval": {
        "request": {
            "request_id": "PA-2024-005",
            "patient": {"age": 55, "gender": "M", "plan_id": "PPO-750"},
            "diagnosis": ["M75.111"],
            "procedure": "97161",
            "clinical_notes": (
                "55-year-old male presents with right shoulder pain for three months following "
                "a fall onto an outstretched hand. MRI demonstrates a partial-thickness tear of "
                "the supraspinatus tendon with mild subacromial bursitis. Patient reports "
                "significant difficulty with overhead activities, dressing, and sleep disruption "
                "due to pain. Range of motion is limited: forward flexion 120 degrees, abduction "
                "100 degrees with painful arc between 60-120 degrees. Neer and Hawkins "
                "impingement signs are positive. Conservative management with NSAIDs and home "
                "exercises has provided minimal relief. Requesting physical therapy evaluation "
                "and treatment plan for rotator cuff rehabilitation."
            ),
            "prior_treatments": ["nsaid_therapy", "home_exercises"],
            "attachments": ["mri_report", "orthopedic_referral"],
        },
        "ground_truth": {
            "decision": "approve",
            "required_criteria": ["GL-PT-EVAL-001"],
            "required_missing_fields": [],
            "denial_reason_code": None,
            "key_findings": [
                "MRI-confirmed partial-thickness supraspinatus tear",
                "functional limitation in daily activities",
                "positive Neer and Hawkins impingement signs",
            ],
        },
        "patient_history": {
            "history": "Prior shoulder MRI approved. Chronic conditions: rotator cuff tear, hypertension.",
            "prior_auths": [
                {"request_id": "PA-2023-200", "procedure": "73221", "decision": "approve", "date": "2023-11-01"},
            ],
        },
    },
    # ── MEDIUM ────────────────────────────────────────────
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
            "key_findings": [
                "mesalamine failed (8 months inadequate response)",
                "prednisone dependent (flares below 15mg)",
                "CDAI 285 — moderate-to-severe",
                "step therapy documentation missing",
                "prior biologic records not obtained",
            ],
            "post_info_decision": "approve",
            "post_info_rationale": (
                "After receiving step therapy documentation confirming prior conventional therapy "
                "failures and biologic records from outside facility, criteria GL-BIOLOGIC-001 "
                "are met. Approve."
            ),
        },
        "patient_history": {
            "history": (
                "Diagnosed with Crohn's disease 3 years ago. Multiple ER visits for flares. "
                "Failed mesalamine, prednisone-dependent. Prior biologic trial at outside facility — records pending."
            ),
            "prior_auths": [
                {"request_id": "PA-2023-112", "procedure": "43239", "decision": "approve", "date": "2023-05-20"},
                {"request_id": "PA-2024-001", "procedure": "J0135", "decision": "pending", "date": "2024-01-10"},
            ],
        },
        "supplemental_info": {
            "step_therapy_documentation": (
                "Step therapy documentation received: "
                "1) Mesalamine 4.8g/day for 8 months — documented inadequate response (CDAI remained >280). "
                "2) Azathioprine 150mg/day for 6 weeks — discontinued due to severe leukopenia (WBC 2.1). "
                "Per policy, adverse event requiring discontinuation qualifies as therapeutic failure. "
                "Two conventional therapy failures confirmed."
            ),
            "prior_biologic_records": (
                "Prior treatment records from outside facility confirm: infliximab trial from "
                "January 2023 to April 2023, discontinued due to infusion reactions. "
                "Documented in electronic medical records with provider attestation."
            ),
        },
    },
    "medium_ozempic": {
        "request": {
            "request_id": "PA-2024-006",
            "patient": {"age": 48, "gender": "M", "plan_id": "PPO-500"},
            "diagnosis": ["E11.65", "E66.01"],
            "procedure": "J3490",
            "clinical_notes": (
                "48-year-old male with type 2 diabetes mellitus and morbid obesity (BMI 36.2) "
                "presenting for authorization of semaglutide (Ozempic) 1mg weekly injection. "
                "Patient was diagnosed with T2DM two years ago. HbA1c is currently 8.4% despite "
                "lifestyle modifications including a structured diet program supervised by a "
                "registered dietitian for the past eight months and a progressive exercise "
                "regimen. Patient was started on metformin 1000mg BID one year ago but developed "
                "severe GI intolerance (persistent diarrhea, nausea) requiring discontinuation "
                "after three months. He was then trialed on glipizide 10mg BID for six months "
                "with HbA1c only decreasing from 9.1% to 8.4%. Comorbidities include "
                "hypertension controlled on lisinopril and hyperlipidemia on atorvastatin. "
                "Patient reports the dietitian records from months 1-4 of the lifestyle program "
                "are at a previous provider's office and have not yet been transferred."
            ),
            "prior_treatments": ["lifestyle_modification_8_months", "metformin_discontinued", "glipizide_6_months"],
            "attachments": ["endocrinology_notes", "lab_results", "partial_dietitian_records"],
        },
        "ground_truth": {
            "decision": "request_info",
            "required_criteria": ["GL-GLP1-001"],
            "required_missing_fields": [
                "complete_lifestyle_modification_records",
                "metformin_intolerance_documentation",
            ],
            "denial_reason_code": None,
            "key_findings": [
                "BMI 36.2 meets threshold",
                "HbA1c 8.4% > 7% threshold",
                "metformin discontinued for GI intolerance — documentation incomplete",
                "lifestyle modification records months 1-4 missing",
                "glipizide trial showed partial response",
            ],
            "post_info_decision": "approve",
            "post_info_rationale": (
                "After receiving complete dietitian records and metformin intolerance documentation, "
                "all GL-GLP1-001 criteria are met. BMI >30, HbA1c >7, documented lifestyle modification "
                "failure, and documented metformin intolerance. Approve."
            ),
        },
        "patient_history": {
            "history": (
                "T2DM diagnosed 2 years ago. Morbid obesity (BMI 36.2). "
                "Failed metformin (GI intolerance), partial response to glipizide. "
                "Hypertension and hyperlipidemia managed medically."
            ),
            "prior_auths": [
                {"request_id": "PA-2023-044", "procedure": "99213", "decision": "approve", "date": "2023-08-15"},
            ],
        },
        "supplemental_info": {
            "complete_lifestyle_modification_records": (
                "Dietitian records received covering full 8-month program: "
                "Months 1-4 (previous provider): structured 1500-calorie diet with weekly weigh-ins. "
                "Patient lost 4 lbs in 4 months — inadequate response. "
                "Months 5-8 (current provider): continued diet program with exercise regimen added. "
                "Total weight loss 6 lbs over 8 months. HbA1c unchanged. Lifestyle modification failure documented."
            ),
            "metformin_intolerance_documentation": (
                "Metformin intolerance documentation: Patient started metformin 500mg BID, titrated to 1000mg BID. "
                "Developed persistent diarrhea (6-8 episodes/day) and nausea within 2 weeks of full dose. "
                "Extended-release formulation attempted — symptoms persisted. "
                "Discontinued after 3 months per gastroenterology recommendation. "
                "Documented as true intolerance, not non-compliance."
            ),
        },
    },
    "medium_sleep_study": {
        "request": {
            "request_id": "PA-2024-007",
            "patient": {"age": 41, "gender": "F", "plan_id": "HMO-250"},
            "diagnosis": ["G47.33"],
            "procedure": "95810",
            "clinical_notes": (
                "41-year-old female referred for in-lab polysomnography for suspected "
                "obstructive sleep apnea. Patient reports excessive daytime sleepiness with "
                "Epworth Sleepiness Scale score of 15, loud snoring confirmed by bed partner, "
                "and witnessed apneic episodes approximately 3-4 times per night. BMI is 33.5. "
                "Patient has comorbid atrial fibrillation on anticoagulation and moderate COPD "
                "on tiotropium. A home sleep apnea test was attempted two weeks ago but was "
                "technically inadequate — the nasal cannula dislodged during the night and the "
                "oximetry signal was lost for over 60% of the recording, rendering the study "
                "uninterpretable. Given the complex cardiopulmonary comorbidities and failed "
                "home study, in-laboratory attended polysomnography is requested for definitive "
                "diagnosis and CPAP titration."
            ),
            "prior_treatments": ["home_sleep_test_failed"],
            "attachments": ["sleep_medicine_referral", "failed_hsat_report", "pulmonology_notes"],
        },
        "ground_truth": {
            "decision": "approve",
            "required_criteria": ["GL-SLEEP-001"],
            "required_missing_fields": [],
            "denial_reason_code": None,
            "key_findings": [
                "ESS score 15 (>10 threshold)",
                "witnessed apneic episodes",
                "failed home sleep test (technically inadequate)",
                "complex comorbidities (AFib, COPD) justify in-lab study",
            ],
        },
        "patient_history": {
            "history": (
                "Atrial fibrillation on anticoagulation. Moderate COPD on tiotropium. "
                "Failed home sleep apnea test. No prior sleep-related PA requests."
            ),
            "prior_auths": [
                {"request_id": "PA-2023-112", "procedure": "43239", "decision": "approve", "date": "2023-05-20"},
            ],
        },
    },
    # ── HARD ──────────────────────────────────────────────
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
                "active L5 nerve root compromise bilaterally.\n\n"
                "Comorbidities: Type 2 diabetes mellitus — last HbA1c 8.4% (drawn 2024-03-01), "
                "up from 7.9% six months ago. Patient reports difficulty with medication "
                "compliance. Endocrinologist consulted but no formal glycemic optimization plan "
                "documented. The patient's current BMI is 38, and he has been counseled on "
                "weight management with a target of BMI below 35 prior to elective surgery.\n\n"
                "Additional note from primary care (2024-03-05): Patient's diabetes remains "
                "suboptimally controlled. Recommended referral to diabetes education program. "
                "HbA1c target for surgical clearance per institutional protocol is <8.0%. "
                "Current level of 8.4% represents a surgical risk factor. Primary care did not "
                "provide surgical clearance pending glycemic improvement.\n\n"
                "Given the failure of prolonged conservative measures, documented structural "
                "instability, and progressive neurological deficits, the treating spine surgeon "
                "recommends L4-L5 posterior lumbar interbody fusion with pedicle screw "
                "instrumentation. The surgical team has reviewed the case and believes the "
                "patient meets criteria for intervention. Pre-operative cardiac clearance has "
                "been obtained. Anesthesiology has evaluated the patient and notes no "
                "contraindication to general anesthesia aside from standard obesity-related "
                "precautions. Pain management program completed December 2023. Psychological "
                "evaluation completed 2024-02-20 — patient cleared for surgery. The procedure "
                "is planned as an inpatient surgery with an anticipated three-to-four day "
                "hospital stay."
            ),
            "prior_treatments": [
                "physical_therapy_8_months",
                "epidural_injections_x3",
                "nsaid_therapy",
                "gabapentin",
                "pain_management_program",
            ],
            "attachments": [
                "spine_imaging",
                "neurology_consult",
                "pain_management_records",
                "psychological_evaluation",
            ],
        },
        "ground_truth": {
            "decision": "deny",
            "required_criteria": ["GL-SPINE-FUSION-001", "GL-SPINE-FUSION-002"],
            "required_missing_fields": [],
            "denial_reason_code": "CONTRAINDICATION_ACTIVE",
            "contraindication": {
                "type": "uncontrolled_diabetes",
                "detail": "HbA1c 8.4% > 8.0% threshold",
                "location_hint": "buried in comorbidities paragraph and primary care note",
            },
            "key_findings": [
                "HbA1c 8.4% exceeds 8.0% threshold — uncontrolled diabetes",
                "primary care did not provide surgical clearance",
                "GL-SPINE-FUSION-001 requires no uncontrolled diabetes (HbA1c <= 8.0)",
                "GL-SPINE-FUSION-002 has stricter BMI cutoff (35) — patient BMI 38 fails",
                "conservative treatment met (8 months PT + pain management)",
                "psychological evaluation completed",
                "imaging concordant with symptoms",
            ],
            "alternative_denial_codes": [
                "CRITERIA_NOT_MET",
                "MEDICAL_NECESSITY_NOT_ESTABLISHED",
                "SAFETY_CONCERN",
            ],
            "conflicting_guideline": {
                "primary": "GL-SPINE-FUSION-001",
                "secondary": "GL-SPINE-FUSION-002",
                "conflict": "GL-SPINE-FUSION-001 allows BMI<40 but requires HbA1c<=8.0; GL-SPINE-FUSION-002 requires BMI<35 but shorter conservative treatment. Patient fails both.",
            },
        },
        "patient_history": {
            "history": (
                "Chronic low back pain 5+ years. Multiple conservative treatment attempts. "
                "Type 2 diabetes since 2018, historically borderline controlled. "
                "Three prior epidural injection PAs approved. No prior spinal surgeries."
            ),
            "prior_auths": [
                {"request_id": "PA-2023-078", "procedure": "62322", "decision": "approve", "date": "2023-03-10"},
                {"request_id": "PA-2023-091", "procedure": "62322", "decision": "approve", "date": "2023-06-22"},
                {"request_id": "PA-2023-105", "procedure": "62322", "decision": "approve", "date": "2023-09-04"},
            ],
        },
    },
    "hard_cardiac_cath": {
        "request": {
            "request_id": "PA-2024-008",
            "patient": {"age": 67, "gender": "M", "plan_id": "PPO-1000"},
            "diagnosis": ["I25.10", "I20.0"],
            "procedure": "93458",
            "clinical_notes": (
                "67-year-old male with known coronary artery disease and chronic stable angina "
                "presenting with worsening exertional chest pain over the past four months "
                "despite maximal medical therapy. Current medications include aspirin 81mg, "
                "atorvastatin 80mg, metoprolol succinate 200mg, amlodipine 10mg, and "
                "isosorbide mononitrate 60mg daily. Patient reports angina now occurring with "
                "minimal exertion (walking one block) and occasionally at rest, representing "
                "CCS Class III-IV symptoms.\n\n"
                "Nuclear stress test performed three weeks ago demonstrates a large area of "
                "reversible perfusion defect in the LAD territory involving the anterior wall "
                "and apex, with an estimated 18% ischemic myocardium. LVEF on gated images is "
                "45%. Echocardiogram confirms LVEF 44% with anterior wall hypokinesis.\n\n"
                "Laboratory data: troponin I negative x2, BNP 340 pg/mL, creatinine 2.8 mg/dL "
                "(eGFR 22 mL/min), hemoglobin 9.2 g/dL. Patient has stage 4 CKD and is "
                "followed by nephrology. He was hospitalized two weeks ago for a GI bleed from "
                "a duodenal ulcer requiring transfusion of 3 units pRBC; EGD showed a visible "
                "vessel that was clipped. He was restarted on aspirin five days ago. The "
                "interventional cardiologist recommends diagnostic catheterization with possible "
                "PCI. Nephrology has been consulted regarding contrast risk and recommends "
                "pre-hydration protocol."
            ),
            "prior_treatments": [
                "maximal_medical_therapy_4_months",
                "nuclear_stress_test",
                "echocardiogram",
            ],
            "attachments": [
                "cardiology_notes",
                "stress_test_report",
                "nephrology_consult",
                "gi_discharge_summary",
            ],
        },
        "ground_truth": {
            "decision": "deny",
            "required_criteria": ["GL-CARDIAC-CATH-001", "GL-CARDIAC-CATH-002"],
            "required_missing_fields": [],
            "denial_reason_code": "CONTRAINDICATION_ACTIVE_BLEEDING_AND_RENAL",
            "contraindication": "recent_gi_bleed_and_eGFR_below_30",
            "key_findings": [
                "eGFR 22 mL/min — below 30 threshold (stage 4 CKD)",
                "recent GI bleed 2 weeks ago requiring transfusion",
                "aspirin restarted only 5 days ago after GI bleed",
                "positive stress test with 18% ischemic myocardium",
                "LVEF 44-45% with anterior wall hypokinesis",
                "GL-CARDIAC-CATH-001 requires no active bleeding AND eGFR >30",
            ],
            "alternative_denial_codes": [
                "SAFETY_CONCERN",
                "CONTRAINDICATION_RENAL",
                "CONTRAINDICATION_BLEEDING_RISK",
            ],
        },
        "patient_history": {
            "history": (
                "Known CAD with chronic stable angina. Stage 4 CKD followed by nephrology. "
                "Recent GI bleed from duodenal ulcer. Three prior epidural injection PAs."
            ),
            "prior_auths": [
                {"request_id": "PA-2023-078", "procedure": "62322", "decision": "approve", "date": "2023-03-10"},
                {"request_id": "PA-2023-091", "procedure": "62322", "decision": "approve", "date": "2023-06-22"},
                {"request_id": "PA-2023-105", "procedure": "62322", "decision": "approve", "date": "2023-09-04"},
            ],
        },
    },
    "hard_gene_therapy": {
        "request": {
            "request_id": "PA-2024-009",
            "patient": {"age": 1, "gender": "F", "plan_id": "PPO-2000"},
            "diagnosis": ["G12.1"],
            "procedure": "J3399",
            "clinical_notes": (
                "14-month-old female with genetically confirmed spinal muscular atrophy (SMA) "
                "type 2, presenting for authorization of onasemnogene abeparvovec (Zolgensma). "
                "Genetic testing confirms homozygous deletion of SMN1 gene with 3 copies of "
                "SMN2. Patient was diagnosed at 8 months of age when parents noted failure to "
                "achieve independent sitting. Current motor function assessment shows ability "
                "to sit with support but no independent sitting or standing. CHOP-INTEND score "
                "is 38.\n\n"
                "The child was started on nusinersen (Spinraza) at 9 months and has received "
                "the four loading doses plus one maintenance dose with modest improvement in "
                "motor function (CHOP-INTEND improved from 32 to 38). The treating neurologist "
                "recommends switching to Zolgensma for potentially superior efficacy as a "
                "one-time gene therapy.\n\n"
                "Recent labs: ALT 85 U/L (elevated, normal <45), AST 72 U/L (elevated), "
                "total bilirubin 0.8 mg/dL. Hepatology consultation notes that the transaminase "
                "elevation is likely related to nusinersen but recommends monitoring. Anti-AAV9 "
                "antibody titer was drawn and resulted at 1:25 (threshold for treatment is "
                "<1:50, so patient qualifies). Pulmonary function: patient is not ventilator "
                "dependent, no history of respiratory failure, currently on nighttime BiPAP "
                "initiated prophylactically.\n\n"
                "The family has been counseled extensively about the $2.1M cost, the hepatotoxicity "
                "risk requiring prednisolone pre-treatment and liver monitoring, and the fact "
                "that this is an irreversible one-time treatment. The neurology team notes the "
                "patient is approaching the age cutoff and requests expedited review."
            ),
            "prior_treatments": [
                "nusinersen_5_doses",
                "physical_therapy_ongoing",
                "nighttime_bipap",
            ],
            "attachments": [
                "genetic_testing_report",
                "neurology_assessment",
                "hepatology_consult",
                "aav9_antibody_results",
                "pulmonary_function",
            ],
        },
        "ground_truth": {
            "decision": "deny",
            "required_criteria": ["GL-GENE-THERAPY-001"],
            "required_missing_fields": [],
            "denial_reason_code": "CONTRAINDICATION_HEPATIC_DISEASE",
            "contraindication": "elevated_transaminases_active_hepatic_concern",
            "key_findings": [
                "ALT 85 U/L (normal <45) — nearly 2x upper limit",
                "AST 72 U/L — elevated",
                "GL-GENE-THERAPY-001 requires no active hepatic disease",
                "hepatology notes transaminase elevation, recommends monitoring",
                "anti-AAV9 titer 1:25 qualifies (<1:50 threshold)",
                "age 14 months — within 2-year cutoff",
                "SMN1 deletion confirmed",
            ],
            "alternative_denial_codes": [
                "SAFETY_CONCERN",
                "CONTRAINDICATION_HEPATOTOXICITY_RISK",
            ],
        },
        "patient_history": {
            "history": (
                "SMA type 2 diagnosed at 8 months. On nusinersen since 9 months (5 doses). "
                "Modest motor improvement. Nighttime BiPAP prophylactic."
            ),
            "prior_auths": [
                {"request_id": "PA-2024-050", "procedure": "J2326", "decision": "approve", "date": "2024-02-15"},
                {"request_id": "PA-2024-051", "procedure": "J2326", "decision": "approve", "date": "2024-03-01"},
            ],
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
        "chronic_conditions": ["lumbar_spondylosis", "chronic_low_back_pain", "hypertension", "obesity", "type_2_diabetes"],
    },
    "HMO-100": {
        "prior_authorizations": [],
        "chronic_conditions": ["hypertension", "osteoarthritis"],
    },
    "PPO-750": {
        "prior_authorizations": [
            {"request_id": "PA-2023-200", "procedure": "73221", "decision": "approve", "date": "2023-11-01"},
        ],
        "chronic_conditions": ["rotator_cuff_tear", "hypertension"],
    },
    "PPO-2000": {
        "prior_authorizations": [
            {"request_id": "PA-2024-050", "procedure": "J2326", "decision": "approve", "date": "2024-02-15"},
            {"request_id": "PA-2024-051", "procedure": "J2326", "decision": "approve", "date": "2024-03-01"},
        ],
        "chronic_conditions": ["spinal_muscular_atrophy"],
    },
}
