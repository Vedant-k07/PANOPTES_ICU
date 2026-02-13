"""Clinical Decision Support Service for PANOPTES-ICU

Advanced features:
- Treatment protocol recommendations
- Fluid responsiveness prediction
- Antimicrobial stewardship
- Ventilator/vasopressor weaning assistance
- Nutrition optimization
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Types of clinical protocols"""
    SEPSIS = "SEPSIS"
    ARDS = "ARDS"
    AKI = "AKI"
    SHOCK = "SHOCK"
    DKA = "DKA"
    STROKE = "STROKE"
    MI = "MI"
    TRAUMA = "TRAUMA"


class FluidStatus(Enum):
    """Fluid responsiveness status"""
    RESPONSIVE = "RESPONSIVE"
    NON_RESPONSIVE = "NON_RESPONSIVE"
    UNCERTAIN = "UNCERTAIN"


class ClinicalDecisionService:
    """Comprehensive clinical decision support system"""
    
    def __init__(self):
        self.protocol_database = self._initialize_protocols()
        self.antibiotic_database = self._initialize_antibiotics()
        
    def _initialize_protocols(self) -> Dict:
        """Initialize evidence-based treatment protocols"""
        return {
            ProtocolType.SEPSIS: {
                "name": "Surviving Sepsis Campaign Guidelines",
                "version": "2021",
                "hour_1_bundle": [
                    "Measure lactate level (remeasure if initial >2 mmol/L)",
                    "Obtain blood cultures before antibiotics",
                    "Administer broad-spectrum antibiotics",
                    "Begin 30 mL/kg crystalloid for hypotension or lactate ≥4 mmol/L",
                    "Apply vasopressors if hypotensive during/after fluid resuscitation (target MAP ≥65 mmHg)"
                ],
                "antimicrobials": {
                    "community_acquired": ["Ceftriaxone + Azithromycin", "Piperacillin-Tazobactam"],
                    "healthcare_associated": ["Vancomycin + Piperacillin-Tazobactam", "Meropenem + Vancomycin"],
                    "immunocompromised": ["Meropenem + Vancomycin + Fluconazole"]
                },
                "monitoring": ["Lactate q2-4h", "MAP continuously", "UOP q1h", "CVP if available"]
            },
            ProtocolType.ARDS: {
                "name": "ARDSNet Protocol",
                "version": "2024",
                "ventilator_settings": {
                    "tidal_volume": "4-8 mL/kg PBW",
                    "plateau_pressure": "<30 cmH2O",
                    "peep_fio2_table": "Low PEEP/High FiO2 or High PEEP/Low FiO2",
                    "target_spo2": "88-95%"
                },
                "adjuncts": [
                    "Prone positioning if P/F <150",
                    "Neuromuscular blockade for 48h if P/F <150",
                    "Consider ECMO if refractory"
                ]
            },
            ProtocolType.AKI: {
                "name": "KDIGO AKI Guidelines",
                "version": "2023",
                "stages": {
                    1: "Cr 1.5-1.9x baseline OR ≥0.3 mg/dL increase OR UOP <0.5 mL/kg/h x 6-12h",
                    2: "Cr 2.0-2.9x baseline OR UOP <0.5 mL/kg/h x ≥12h",
                    3: "Cr ≥3.0x baseline OR Cr ≥4.0 mg/dL OR RRT initiation OR UOP <0.3 mL/kg/h x ≥24h"
                },
                "management": [
                    "Discontinue nephrotoxins",
                    "Optimize volume status",
                    "Monitor creatinine and urine output",
                    "Consider RRT if refractory"
                ]
            },
            ProtocolType.SHOCK: {
                "name": "Hemodynamic Management Protocol",
                "version": "2024",
                "types": {
                    "hypovolemic": {
                        "first_line": "Crystalloid bolus 20-30 mL/kg",
                        "second_line": "Blood products if hemorrhagic"
                    },
                    "cardiogenic": {
                        "first_line": "Dobutamine 2-20 mcg/kg/min",
                        "second_line": "Milrinone or mechanical support"
                    },
                    "distributive": {
                        "first_line": "Norepinephrine 0.1-2 mcg/kg/min",
                        "second_line": "Vasopressin 0.03-0.04 U/min"
                    },
                    "obstructive": {
                        "treatment": "Address underlying cause (PE, tamponade, tension PTX)"
                    }
                }
            }
        }
    
    def _initialize_antibiotics(self) -> Dict:
        """Initialize antibiotic stewardship database"""
        return {
            "gram_positive": {
                "MSSA": ["Nafcillin", "Cefazolin", "Oxacillin"],
                "MRSA": ["Vancomycin", "Daptomycin", "Linezolid"],
                "Strep_pneumoniae": ["Penicillin G", "Ceftriaxone", "Levofloxacin"],
                "Enterococcus": ["Ampicillin", "Vancomycin"]
            },
            "gram_negative": {
                "E_coli": ["Ceftriaxone", "Ciprofloxacin", "Piperacillin-Tazobactam"],
                "Klebsiella": ["Ceftriaxone", "Meropenem", "Piperacillin-Tazobactam"],
                "Pseudomonas": ["Piperacillin-Tazobactam", "Cefepime", "Meropenem", "Ciprofloxacin"],
                "Acinetobacter": ["Meropenem", "Ampicillin-Sulbactam", "Colistin"]
            },
            "anaerobes": {
                "Bacteroides": ["Metronidazole", "Piperacillin-Tazobactam", "Meropenem"],
                "Clostridium": ["Metronidazole", "Vancomycin (oral for C. diff)"]
            },
            "atypicals": {
                "Legionella": ["Azithromycin", "Levofloxacin"],
                "Mycoplasma": ["Azithromycin", "Doxycycline"]
            },
            "dose_adjustments": {
                "renal": {
                    "Vancomycin": "Adjust by CrCl, target trough 15-20 mcg/mL",
                    "Meropenem": "CrCl 26-50: 1g q12h, CrCl 10-25: 500mg q12h",
                    "Piperacillin-Tazobactam": "CrCl 20-40: 2.25g q6h, CrCl <20: 2.25g q8h"
                },
                "hepatic": {
                    "Metronidazole": "Reduce dose by 50% in severe hepatic impairment"
                }
            }
        }
    
    def get_treatment_protocol(
        self,
        patient_id: str,
        condition: str,
        clinical_data: Dict
    ) -> Dict:
        """Get evidence-based treatment protocol recommendations
        
        Args:
            patient_id: Patient identifier
            condition: Clinical condition (sepsis, ards, aki, shock)
            clinical_data: Current clinical parameters
            
        Returns:
            Comprehensive treatment protocol
        """
        try:
            protocol_type = ProtocolType[condition.upper()]
            protocol = self.protocol_database.get(protocol_type, {})
            
            # Customize based on clinical data
            recommendations = self._customize_protocol(protocol_type, protocol, clinical_data)
            
            return {
                "patient_id": patient_id,
                "condition": condition,
                "protocol_name": protocol.get("name", "Standard Protocol"),
                "protocol_version": protocol.get("version", "2024"),
                "immediate_actions": recommendations.get("immediate", []),
                "medications": recommendations.get("medications", []),
                "monitoring": recommendations.get("monitoring", []),
                "targets": recommendations.get("targets", {}),
                "contraindications": recommendations.get("contraindications", []),
                "escalation_criteria": recommendations.get("escalation", []),
                "timestamp": datetime.now().isoformat()
            }
        except KeyError:
            return {
                "patient_id": patient_id,
                "error": f"Unknown condition: {condition}",
                "available_protocols": [p.value for p in ProtocolType]
            }
    
    def _customize_protocol(
        self,
        protocol_type: ProtocolType,
        base_protocol: Dict,
        clinical_data: Dict
    ) -> Dict:
        """Customize protocol based on patient-specific data"""
        recommendations = {
            "immediate": [],
            "medications": [],
            "monitoring": [],
            "targets": {},
            "contraindications": [],
            "escalation": []
        }
        
        if protocol_type == ProtocolType.SEPSIS:
            # Hour-1 bundle
            recommendations["immediate"] = base_protocol.get("hour_1_bundle", [])
            
            # Determine antimicrobial choice
            if clinical_data.get("healthcare_associated", False):
                recommendations["medications"] = base_protocol.get("antimicrobials", {}).get("healthcare_associated", [])
            elif clinical_data.get("immunocompromised", False):
                recommendations["medications"] = base_protocol.get("antimicrobials", {}).get("immunocompromised", [])
            else:
                recommendations["medications"] = base_protocol.get("antimicrobials", {}).get("community_acquired", [])
            
            recommendations["monitoring"] = base_protocol.get("monitoring", [])
            recommendations["targets"] = {
                "MAP": "≥65 mmHg",
                "lactate_clearance": ">10% in 2-4 hours",
                "urine_output": "≥0.5 mL/kg/h",
                "cvp": "8-12 mmHg (if measured)"
            }
            recommendations["escalation"] = [
                "Refractory hypotension despite adequate fluid and vasopressors",
                "Lactate >4 mmol/L not improving",
                "Multi-organ failure progression"
            ]
            
        elif protocol_type == ProtocolType.ARDS:
            vent_settings = base_protocol.get("ventilator_settings", {})
            pf_ratio = clinical_data.get("pf_ratio", 200)
            
            recommendations["immediate"] = [
                f"Set Vt to {vent_settings.get('tidal_volume', '6 mL/kg PBW')}",
                f"Maintain Pplat {vent_settings.get('plateau_pressure', '<30 cmH2O')}",
                f"Target SpO2 {vent_settings.get('target_spo2', '88-95%')}"
            ]
            
            if pf_ratio < 150:
                recommendations["immediate"].extend(base_protocol.get("adjuncts", []))
            
            recommendations["targets"] = {
                "pH": "7.30-7.45",
                "Pplat": "<30 cmH2O",
                "driving_pressure": "<15 cmH2O",
                "SpO2": "88-95%"
            }
            
        elif protocol_type == ProtocolType.SHOCK:
            shock_type = clinical_data.get("shock_type", "distributive")
            shock_protocols = base_protocol.get("types", {})
            
            if shock_type in shock_protocols:
                specific = shock_protocols[shock_type]
                recommendations["medications"] = [
                    f"First-line: {specific.get('first_line', 'Crystalloid')}",
                    f"Second-line: {specific.get('second_line', 'Vasopressor')}"
                ]
            
            recommendations["monitoring"] = [
                "Continuous arterial BP monitoring",
                "CVP or SVV monitoring",
                "Lactate q2h",
                "ScvO2 if available"
            ]
            recommendations["targets"] = {
                "MAP": "≥65 mmHg",
                "ScvO2": "≥70%",
                "lactate": "<2 mmol/L",
                "urine_output": "≥0.5 mL/kg/h"
            }
        
        return recommendations
    
    def predict_fluid_responsiveness(
        self,
        patient_id: str,
        hemodynamic_data: Dict
    ) -> Dict:
        """Predict fluid responsiveness using dynamic parameters
        
        Args:
            patient_id: Patient identifier
            hemodynamic_data: Contains SVV, PPV, PLR results, etc.
            
        Returns:
            Fluid responsiveness prediction with confidence
        """
        # Extract parameters
        svv = hemodynamic_data.get("stroke_volume_variation")  # %
        ppv = hemodynamic_data.get("pulse_pressure_variation")  # %
        plr_response = hemodynamic_data.get("passive_leg_raise_response")  # % CO increase
        ivc_collapsibility = hemodynamic_data.get("ivc_collapsibility")  # %
        cvp = hemodynamic_data.get("cvp")  # mmHg
        mechanical_ventilation = hemodynamic_data.get("mechanical_ventilation", False)
        tidal_volume = hemodynamic_data.get("tidal_volume_ml_kg", 6)
        
        predictors = []
        confidence_scores = []
        
        # SVV analysis (best if Vt ≥8 mL/kg, MV, sinus rhythm)
        if svv is not None and mechanical_ventilation and tidal_volume >= 8:
            if svv > 13:
                predictors.append(("SVV", FluidStatus.RESPONSIVE, 0.85))
            elif svv < 9:
                predictors.append(("SVV", FluidStatus.NON_RESPONSIVE, 0.80))
            else:
                predictors.append(("SVV", FluidStatus.UNCERTAIN, 0.50))
        
        # PPV analysis
        if ppv is not None and mechanical_ventilation:
            if ppv > 13:
                predictors.append(("PPV", FluidStatus.RESPONSIVE, 0.87))
            elif ppv < 9:
                predictors.append(("PPV", FluidStatus.NON_RESPONSIVE, 0.82))
            else:
                predictors.append(("PPV", FluidStatus.UNCERTAIN, 0.50))
        
        # Passive Leg Raise (most reliable, works in spontaneous breathing)
        if plr_response is not None:
            if plr_response >= 10:
                predictors.append(("PLR", FluidStatus.RESPONSIVE, 0.90))
            elif plr_response < 5:
                predictors.append(("PLR", FluidStatus.NON_RESPONSIVE, 0.85))
            else:
                predictors.append(("PLR", FluidStatus.UNCERTAIN, 0.60))
        
        # IVC collapsibility (spontaneous breathing)
        if ivc_collapsibility is not None and not mechanical_ventilation:
            if ivc_collapsibility > 50:
                predictors.append(("IVC", FluidStatus.RESPONSIVE, 0.75))
            elif ivc_collapsibility < 20:
                predictors.append(("IVC", FluidStatus.NON_RESPONSIVE, 0.70))
            else:
                predictors.append(("IVC", FluidStatus.UNCERTAIN, 0.50))
        
        # Aggregate prediction
        if not predictors:
            return {
                "patient_id": patient_id,
                "prediction": "INSUFFICIENT_DATA",
                "confidence": 0.0,
                "recommendation": "Obtain dynamic hemodynamic parameters (SVV, PPV, or PLR)",
                "data_provided": hemodynamic_data,
                "timestamp": datetime.now().isoformat()
            }
        
        # Weighted voting
        responsive_score = sum(p[2] for p in predictors if p[1] == FluidStatus.RESPONSIVE)
        non_responsive_score = sum(p[2] for p in predictors if p[1] == FluidStatus.NON_RESPONSIVE)
        
        if responsive_score > non_responsive_score:
            prediction = FluidStatus.RESPONSIVE
            confidence = responsive_score / (responsive_score + non_responsive_score + 0.1)
            recommendation = "Patient likely fluid responsive - consider crystalloid bolus 250-500 mL with reassessment"
        elif non_responsive_score > responsive_score:
            prediction = FluidStatus.NON_RESPONSIVE
            confidence = non_responsive_score / (responsive_score + non_responsive_score + 0.1)
            recommendation = "Patient unlikely to respond to fluids - consider vasopressor support or inotropes"
        else:
            prediction = FluidStatus.UNCERTAIN
            confidence = 0.5
            recommendation = "Uncertain fluid responsiveness - consider passive leg raise test or fluid challenge with close monitoring"
        
        return {
            "patient_id": patient_id,
            "prediction": prediction.value,
            "confidence": round(float(confidence), 2),
            "individual_predictors": [
                {"parameter": p[0], "status": p[1].value, "confidence": round(p[2], 2)}
                for p in predictors
            ],
            "recommendation": recommendation,
            "fluid_strategy": self._get_fluid_strategy(prediction, hemodynamic_data),
            "caveats": self._get_fluid_caveats(hemodynamic_data),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fluid_strategy(self, prediction: FluidStatus, data: Dict) -> Dict:
        """Get specific fluid strategy based on prediction"""
        if prediction == FluidStatus.RESPONSIVE:
            return {
                "action": "Administer fluid bolus",
                "volume": "250-500 mL crystalloid",
                "rate": "Over 15-30 minutes",
                "reassess": "After each bolus",
                "target": "MAP ≥65, improved perfusion markers"
            }
        elif prediction == FluidStatus.NON_RESPONSIVE:
            return {
                "action": "Consider vasopressor/inotrope",
                "first_choice": "Norepinephrine 0.05-0.1 mcg/kg/min",
                "alternative": "Dobutamine if cardiac dysfunction suspected",
                "caution": "Avoid excessive fluid administration",
                "target": "MAP ≥65, adequate tissue perfusion"
            }
        else:
            return {
                "action": "Perform diagnostic test",
                "recommended_test": "Passive leg raise with CO monitoring",
                "alternative": "Mini fluid challenge (100-200 mL) with SVV monitoring",
                "reassess": "After diagnostic maneuver"
            }
    
    def _get_fluid_caveats(self, data: Dict) -> List[str]:
        """Get caveats for fluid responsiveness assessment"""
        caveats = []
        
        if not data.get("mechanical_ventilation"):
            caveats.append("SVV/PPV less reliable in spontaneous breathing")
        
        if data.get("tidal_volume_ml_kg", 6) < 8:
            caveats.append("Low tidal volume may reduce SVV/PPV accuracy")
        
        if data.get("arrhythmia"):
            caveats.append("Arrhythmias affect SVV/PPV reliability")
        
        if data.get("intra_abdominal_hypertension"):
            caveats.append("IAH affects IVC assessment")
        
        if data.get("right_heart_failure"):
            caveats.append("RV dysfunction may cause false-negative SVV/PPV")
        
        return caveats if caveats else ["No significant caveats"]
    
    def get_antimicrobial_recommendation(
        self,
        patient_id: str,
        infection_data: Dict
    ) -> Dict:
        """Get antimicrobial stewardship recommendations
        
        Args:
            patient_id: Patient identifier
            infection_data: Contains site, suspected organisms, cultures, allergies
            
        Returns:
            Antimicrobial recommendations with de-escalation guidance
        """
        site = infection_data.get("infection_site", "unknown")
        suspected_organisms = infection_data.get("suspected_organisms", [])
        culture_results = infection_data.get("culture_results", {})
        allergies = infection_data.get("allergies", [])
        renal_function = infection_data.get("creatinine_clearance")
        current_antibiotics = infection_data.get("current_antibiotics", [])
        days_on_antibiotics = infection_data.get("days_on_antibiotics", 0)
        
        recommendations = {
            "patient_id": patient_id,
            "infection_site": site,
            "timestamp": datetime.now().isoformat()
        }
        
        # Empiric therapy based on site
        empiric_regimens = self._get_empiric_regimen(site, infection_data)
        recommendations["empiric_therapy"] = empiric_regimens
        
        # Culture-directed therapy
        if culture_results:
            directed_therapy = self._get_directed_therapy(culture_results, allergies)
            recommendations["culture_directed"] = directed_therapy
            recommendations["de_escalation_opportunity"] = self._assess_de_escalation(
                current_antibiotics, directed_therapy, days_on_antibiotics
            )
        
        # Dose adjustments
        if renal_function:
            recommendations["dose_adjustments"] = self._get_dose_adjustments(
                empiric_regimens.get("primary", []), renal_function
            )
        
        # Duration guidance
        recommendations["duration_guidance"] = self._get_duration_guidance(site, infection_data)
        
        # Monitoring
        recommendations["monitoring"] = [
            "Daily clinical assessment for response",
            "Follow-up cultures if not improving",
            "Monitor inflammatory markers (CRP, procalcitonin)",
            "Assess for drug toxicity (renal function, liver enzymes)"
        ]
        
        return recommendations
    
    def _get_empiric_regimen(self, site: str, data: Dict) -> Dict:
        """Get empiric antibiotic regimen based on infection site"""
        regimens = {
            "pneumonia_cap": {
                "primary": ["Ceftriaxone 1g IV q24h", "Azithromycin 500mg IV q24h"],
                "severe": ["Ceftriaxone + Azithromycin + Consider Vancomycin if MRSA risk"],
                "duration": "5-7 days minimum"
            },
            "pneumonia_hap": {
                "primary": ["Piperacillin-Tazobactam 4.5g IV q6h", "Vancomycin 15-20mg/kg q8-12h"],
                "alternative": ["Meropenem 1g IV q8h + Vancomycin"],
                "duration": "7-8 days if improving"
            },
            "uti_complicated": {
                "primary": ["Ceftriaxone 1g IV q24h"],
                "alternative": ["Ciprofloxacin 400mg IV q12h"],
                "severe": ["Piperacillin-Tazobactam if septic"],
                "duration": "7-14 days depending on response"
            },
            "intra_abdominal": {
                "primary": ["Piperacillin-Tazobactam 4.5g IV q6h"],
                "alternative": ["Meropenem 1g IV q8h", "Ceftriaxone + Metronidazole"],
                "duration": "4-7 days if source controlled"
            },
            "skin_soft_tissue": {
                "cellulitis": ["Cefazolin 2g IV q8h"],
                "mrsa_risk": ["Vancomycin 15-20mg/kg q8-12h"],
                "necrotizing": ["Vancomycin + Piperacillin-Tazobactam + Clindamycin"],
                "duration": "5-14 days depending on severity"
            },
            "bacteremia_primary": {
                "primary": ["Vancomycin 15-20mg/kg q8-12h", "Piperacillin-Tazobactam 4.5g IV q6h"],
                "duration": "14 days minimum, longer if endocarditis"
            },
            "meningitis": {
                "primary": ["Ceftriaxone 2g IV q12h", "Vancomycin 15-20mg/kg q8-12h", "Dexamethasone"],
                "duration": "10-14 days (bacterial)"
            }
        }
        
        return regimens.get(site, {
            "primary": ["Broad-spectrum coverage pending culture"],
            "recommendation": "Consult infectious disease"
        })
    
    def _get_directed_therapy(self, culture_results: Dict, allergies: List[str]) -> Dict:
        """Get culture-directed antibiotic therapy"""
        organism = culture_results.get("organism", "")
        sensitivities = culture_results.get("sensitivities", [])
        
        # Simple lookup - in production, this would be more sophisticated
        directed = {
            "organism": organism,
            "sensitivities": sensitivities,
            "recommended": []
        }
        
        # Check common organisms
        organism_lower = organism.lower()
        
        if "mrsa" in organism_lower or "methicillin-resistant" in organism_lower:
            if "penicillin" not in [a.lower() for a in allergies]:
                directed["recommended"] = ["Vancomycin 15-20mg/kg q8-12h"]
            else:
                directed["recommended"] = ["Daptomycin 6-8mg/kg q24h", "Linezolid 600mg q12h"]
        elif "pseudomonas" in organism_lower:
            directed["recommended"] = ["Cefepime 2g IV q8h", "Piperacillin-Tazobactam 4.5g q6h"]
        elif "e. coli" in organism_lower or "klebsiella" in organism_lower:
            if "esbl" not in organism_lower:
                directed["recommended"] = ["Ceftriaxone 1g IV q24h"]
            else:
                directed["recommended"] = ["Meropenem 1g IV q8h"]
        
        return directed
    
    def _assess_de_escalation(
        self,
        current: List[str],
        directed: Dict,
        days: int
    ) -> Dict:
        """Assess opportunity for antibiotic de-escalation"""
        if days < 3:
            return {
                "opportunity": False,
                "reason": "Too early - await culture results and clinical response",
                "reassess_in": "24-48 hours"
            }
        
        if directed.get("recommended"):
            return {
                "opportunity": True,
                "action": f"Consider de-escalating to: {', '.join(directed['recommended'])}",
                "rationale": "Culture-directed therapy available",
                "benefits": ["Reduced resistance pressure", "Cost savings", "Reduced toxicity risk"]
            }
        
        return {
            "opportunity": False,
            "reason": "Insufficient culture data for de-escalation",
            "recommendation": "Continue current regimen with daily reassessment"
        }
    
    def _get_dose_adjustments(self, antibiotics: List[str], crcl: float) -> List[Dict]:
        """Get renal dose adjustments"""
        adjustments = []
        
        for abx in antibiotics:
            abx_lower = abx.lower()
            
            if "vancomycin" in abx_lower:
                if crcl < 30:
                    adjustments.append({
                        "drug": "Vancomycin",
                        "adjustment": "Load 25-30mg/kg, then adjust by levels",
                        "monitoring": "Trough before 4th dose, target 15-20 mcg/mL"
                    })
            elif "piperacillin" in abx_lower:
                if crcl < 40:
                    adjustments.append({
                        "drug": "Piperacillin-Tazobactam",
                        "adjustment": "2.25g IV q6h" if crcl > 20 else "2.25g IV q8h",
                        "note": f"CrCl: {crcl}"
                    })
            elif "meropenem" in abx_lower:
                if crcl < 50:
                    adjustments.append({
                        "drug": "Meropenem",
                        "adjustment": "1g IV q12h" if crcl > 25 else "500mg IV q12h",
                        "note": f"CrCl: {crcl}"
                    })
        
        return adjustments if adjustments else [{"note": "No renal adjustments required"}]
    
    def _get_duration_guidance(self, site: str, data: Dict) -> Dict:
        """Get antibiotic duration guidance"""
        durations = {
            "pneumonia_cap": {"minimum": 5, "typical": 7, "extended": 10},
            "pneumonia_hap": {"minimum": 7, "typical": 8, "extended": 14},
            "uti_complicated": {"minimum": 7, "typical": 10, "extended": 14},
            "intra_abdominal": {"minimum": 4, "typical": 7, "extended": 14},
            "bacteremia_primary": {"minimum": 14, "typical": 14, "extended": 42}
        }
        
        duration = durations.get(site, {"minimum": 7, "typical": 10, "extended": 14})
        
        return {
            "minimum_days": duration["minimum"],
            "typical_duration": duration["typical"],
            "extended_if": "Immunocompromised, slow response, or complicated infection",
            "stop_criteria": [
                "Afebrile for ≥48 hours",
                "WBC normalizing",
                "Clinical improvement",
                "Negative follow-up cultures (if applicable)"
            ]
        }
    
    def assess_weaning_readiness(
        self,
        patient_id: str,
        weaning_type: str,
        clinical_data: Dict
    ) -> Dict:
        """Assess readiness for ventilator or vasopressor weaning
        
        Args:
            patient_id: Patient identifier
            weaning_type: 'ventilator' or 'vasopressor'
            clinical_data: Current clinical parameters
            
        Returns:
            Weaning assessment with recommendations
        """
        if weaning_type == "ventilator":
            return self._assess_ventilator_weaning(patient_id, clinical_data)
        elif weaning_type == "vasopressor":
            return self._assess_vasopressor_weaning(patient_id, clinical_data)
        else:
            return {"error": f"Unknown weaning type: {weaning_type}"}
    
    def _assess_ventilator_weaning(self, patient_id: str, data: Dict) -> Dict:
        """Assess ventilator weaning readiness"""
        criteria = {
            "resolution_of_acute_phase": data.get("acute_phase_resolved", False),
            "adequate_oxygenation": data.get("pf_ratio", 0) >= 150 and data.get("peep", 20) <= 8,
            "hemodynamically_stable": data.get("map", 0) >= 65 and not data.get("high_dose_vasopressors", False),
            "adequate_consciousness": data.get("gcs", 0) >= 10 or data.get("follows_commands", False),
            "adequate_cough": data.get("cough_strength", "weak") in ["moderate", "strong"],
            "minimal_secretions": data.get("secretion_volume", "high") in ["minimal", "moderate"],
            "no_planned_surgery": not data.get("surgery_planned", False)
        }
        
        met_criteria = sum(1 for v in criteria.values() if v)
        total_criteria = len(criteria)
        readiness_score = met_criteria / total_criteria
        
        if readiness_score >= 0.85:
            recommendation = "READY for spontaneous breathing trial (SBT)"
            sbt_protocol = {
                "method": "T-piece or low PS (5-8 cmH2O)",
                "duration": "30-120 minutes",
                "monitoring": ["RR", "SpO2", "HR", "BP", "Patient comfort"],
                "failure_criteria": [
                    "RR >35 or <8 for >5 min",
                    "SpO2 <88% for >5 min",
                    "HR >140 or increase >20%",
                    "SBP >180 or <90 mmHg",
                    "Anxiety, diaphoresis, accessory muscle use"
                ]
            }
        elif readiness_score >= 0.6:
            recommendation = "APPROACHING readiness - address deficiencies"
            sbt_protocol = None
        else:
            recommendation = "NOT ready for weaning - continue supportive care"
            sbt_protocol = None
        
        return {
            "patient_id": patient_id,
            "weaning_type": "ventilator",
            "readiness_score": round(readiness_score, 2),
            "criteria_assessment": criteria,
            "recommendation": recommendation,
            "sbt_protocol": sbt_protocol,
            "barriers_to_weaning": [k for k, v in criteria.items() if not v],
            "timestamp": datetime.now().isoformat()
        }
    
    def _assess_vasopressor_weaning(self, patient_id: str, data: Dict) -> Dict:
        """Assess vasopressor weaning readiness"""
        current_dose = data.get("norepinephrine_dose", 0)  # mcg/kg/min
        map_stable = data.get("map_stable_4h", False)
        lactate_trend = data.get("lactate_trend", "unknown")
        urine_output = data.get("urine_output_ml_kg_h", 0)
        
        criteria = {
            "low_vasopressor_dose": current_dose <= 0.1,
            "map_stable": map_stable,
            "lactate_normalizing": lactate_trend in ["decreasing", "normal"],
            "adequate_uop": urine_output >= 0.5,
            "no_active_bleeding": not data.get("active_bleeding", False),
            "source_control": data.get("infection_controlled", True)
        }
        
        met_criteria = sum(1 for v in criteria.values() if v)
        readiness_score = met_criteria / len(criteria)
        
        if readiness_score >= 0.85 and current_dose <= 0.05:
            recommendation = "Ready for vasopressor discontinuation trial"
            weaning_protocol = {
                "method": "Gradual decrease by 0.02-0.05 mcg/kg/min q15-30min",
                "target": "Maintain MAP ≥65 mmHg",
                "monitoring": "Continuous arterial BP, hourly UOP, lactate q4h"
            }
        elif readiness_score >= 0.6:
            recommendation = "Ready to begin vasopressor weaning"
            weaning_protocol = {
                "method": "Decrease by 10-20% q30min to 1h",
                "target": "MAP ≥65 mmHg",
                "monitoring": "Continuous arterial BP"
            }
        else:
            recommendation = "Not ready for vasopressor weaning"
            weaning_protocol = None
        
        return {
            "patient_id": patient_id,
            "weaning_type": "vasopressor",
            "current_dose": current_dose,
            "readiness_score": round(readiness_score, 2),
            "criteria_assessment": criteria,
            "recommendation": recommendation,
            "weaning_protocol": weaning_protocol,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_nutrition_recommendation(
        self,
        patient_id: str,
        nutrition_data: Dict
    ) -> Dict:
        """Get nutrition optimization recommendations
        
        Args:
            patient_id: Patient identifier
            nutrition_data: Contains weight, height, stress factors, GI status
            
        Returns:
            Nutrition recommendations
        """
        weight_kg = nutrition_data.get("weight_kg", 70)
        height_cm = nutrition_data.get("height_cm", 170)
        age = nutrition_data.get("age", 50)
        gender = nutrition_data.get("gender", "M")
        stress_factor = nutrition_data.get("stress_factor", 1.2)
        gi_functional = nutrition_data.get("gi_functional", True)
        
        # Calculate IBW (Ideal Body Weight)
        if gender == "M":
            ibw = 50 + 2.3 * ((height_cm / 2.54) - 60)
        else:
            ibw = 45.5 + 2.3 * ((height_cm / 2.54) - 60)
        
        # Use adjusted body weight if obese
        if weight_kg > ibw * 1.2:
            adjusted_weight = ibw + 0.4 * (weight_kg - ibw)
        else:
            adjusted_weight = weight_kg
        
        # Calculate caloric needs (25-30 kcal/kg/day for ICU)
        calorie_target = round(25 * adjusted_weight * stress_factor)
        protein_target = round(1.5 * adjusted_weight)  # 1.2-2.0 g/kg/day for ICU
        
        # Route determination
        if gi_functional:
            route = "ENTERAL (preferred)"
            route_details = {
                "access": "Nasogastric or post-pyloric",
                "start": "Within 24-48 hours of ICU admission",
                "advancement": "Start at 20 mL/h, increase by 20 mL q6h to goal"
            }
        else:
            route = "PARENTERAL"
            route_details = {
                "access": "Central venous catheter",
                "start": "If EN not possible by day 7",
                "monitoring": "Daily electrolytes, weekly liver enzymes"
            }
        
        return {
            "patient_id": patient_id,
            "calculations": {
                "actual_weight": weight_kg,
                "ideal_body_weight": round(ibw, 1),
                "adjusted_body_weight": round(adjusted_weight, 1)
            },
            "daily_targets": {
                "calories": f"{calorie_target} kcal/day",
                "protein": f"{protein_target} g/day",
                "carbohydrates": "Limit to <4 g/kg/day to prevent hyperglycemia",
                "lipids": "0.7-1.5 g/kg/day"
            },
            "route": route,
            "route_details": route_details,
            "special_considerations": self._get_nutrition_considerations(nutrition_data),
            "monitoring": [
                "Daily weights",
                "Gastric residual volumes q4h initially",
                "Blood glucose q4-6h",
                "Weekly prealbumin (if available)",
                "Weekly nitrogen balance"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_nutrition_considerations(self, data: Dict) -> List[str]:
        """Get special nutrition considerations"""
        considerations = []
        
        if data.get("renal_failure"):
            considerations.append("Limit protein to 0.8-1.0 g/kg if not on RRT; increase to 1.5-2.0 if on RRT")
        
        if data.get("hepatic_failure"):
            considerations.append("Use branched-chain amino acid enriched formulas")
        
        if data.get("ards"):
            considerations.append("Consider anti-inflammatory lipid formulas (omega-3 enriched)")
        
        if data.get("pancreatitis"):
            considerations.append("Use post-pyloric feeding if enteral; low-fat formula")
        
        if data.get("hyperglycemia"):
            considerations.append("Use diabetes-specific formula; target glucose 140-180 mg/dL")
        
        if data.get("gi_surgery"):
            considerations.append("Start trophic feeds early; advance slowly")
        
        return considerations if considerations else ["No special considerations"]
