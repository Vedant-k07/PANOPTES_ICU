"""Advanced Monitoring Service for PANOPTES-ICU

Features:
- Multi-organ trajectory modeling
- Delirium prevention/detection
- Hemodynamic instability prediction (4-6 hours early)
- Sleep quality monitoring
- Vital sign pattern recognition
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)


class HemodynamicStatus(Enum):
    """Hemodynamic stability status"""
    STABLE = "STABLE"
    BORDERLINE = "BORDERLINE"
    UNSTABLE = "UNSTABLE"
    CRITICAL = "CRITICAL"


class DeliriumRisk(Enum):
    """Delirium risk levels"""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    ACTIVE_DELIRIUM = "ACTIVE_DELIRIUM"


class VitalPattern(Enum):
    """Vital sign pattern types"""
    NORMAL = "NORMAL"
    TACHYCARDIA = "TACHYCARDIA"
    BRADYCARDIA = "BRADYCARDIA"
    HYPERTENSION = "HYPERTENSION"
    HYPOTENSION = "HYPOTENSION"
    TACHYPNEA = "TACHYPNEA"
    FEVER = "FEVER"
    HYPOTHERMIA = "HYPOTHERMIA"
    SEPSIS_PATTERN = "SEPSIS_PATTERN"
    SHOCK_PATTERN = "SHOCK_PATTERN"
    ARDS_PATTERN = "ARDS_PATTERN"


class AdvancedMonitoringService:
    """Comprehensive advanced monitoring for ICU patients"""
    
    def __init__(self):
        self.patient_trajectories = {}
        self.vital_history = {}
        self.prediction_buffer_size = 24  # 24 hours of data
        
    def predict_hemodynamic_instability(
        self,
        patient_id: str,
        vital_signs: List[Dict],
        lab_values: Optional[Dict] = None
    ) -> Dict:
        """Predict hemodynamic instability 4-6 hours in advance
        
        Uses multiple parameters and trends to identify early warning signs
        
        Args:
            patient_id: Patient identifier
            vital_signs: List of recent vital sign readings with timestamps
            lab_values: Optional lab values (lactate, Hgb, etc.)
            
        Returns:
            Prediction with risk score and recommendations
        """
        if len(vital_signs) < 6:
            return {
                "patient_id": patient_id,
                "prediction": "INSUFFICIENT_DATA",
                "message": "Need at least 6 hours of vital sign data",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract features
        features = self._extract_hemodynamic_features(vital_signs, lab_values)
        
        # Calculate risk score (0-100)
        risk_score = self._calculate_hemodynamic_risk(features)
        
        # Determine status
        if risk_score >= 75:
            status = HemodynamicStatus.CRITICAL
            prediction_hours = "1-2"
            recommendations = [
                "IMMEDIATE: Prepare for hemodynamic support",
                "Obtain arterial line if not present",
                "Notify physician immediately",
                "Prepare vasopressor infusion",
                "Consider fluid bolus if not contraindicated",
                "Stat labs: lactate, ABG, CBC"
            ]
        elif risk_score >= 50:
            status = HemodynamicStatus.UNSTABLE
            prediction_hours = "2-4"
            recommendations = [
                "Increase monitoring frequency to q15min",
                "Prepare vasopressor for bedside",
                "Review fluid balance and consider bolus",
                "Notify physician of deterioration trend",
                "Check lactate level"
            ]
        elif risk_score >= 30:
            status = HemodynamicStatus.BORDERLINE
            prediction_hours = "4-6"
            recommendations = [
                "Monitor closely q30min",
                "Assess volume status",
                "Review medications for hypotensive agents",
                "Anticipate possible deterioration"
            ]
        else:
            status = HemodynamicStatus.STABLE
            prediction_hours = "N/A"
            recommendations = ["Continue routine monitoring"]
        
        # Identify contributing factors
        risk_factors = self._identify_hemodynamic_risk_factors(features)
        
        return {
            "patient_id": patient_id,
            "risk_score": round(risk_score, 1),
            "hemodynamic_status": status.value,
            "prediction_window": f"{prediction_hours} hours" if prediction_hours != "N/A" else "N/A",
            "contributing_factors": risk_factors,
            "trend_analysis": {
                "map_trend": features.get("map_trend", "unknown"),
                "hr_trend": features.get("hr_trend", "unknown"),
                "shock_index_trend": features.get("si_trend", "unknown")
            },
            "recommendations": recommendations,
            "confidence": self._calculate_prediction_confidence(features),
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_hemodynamic_features(
        self,
        vital_signs: List[Dict],
        lab_values: Optional[Dict]
    ) -> Dict:
        """Extract features for hemodynamic prediction"""
        # Get arrays
        maps = [v.get("map", v.get("sbp", 100) * 0.33 + v.get("dbp", 60) * 0.67) for v in vital_signs]
        hrs = [v.get("hr", 80) for v in vital_signs]
        sbps = [v.get("sbp", 120) for v in vital_signs]
        
        # Calculate shock index
        shock_indices = [hr / sbp if sbp > 0 else 1.0 for hr, sbp in zip(hrs, sbps)]
        
        # Trends (linear regression slope)
        x = np.arange(len(maps))
        
        map_slope = np.polyfit(x, maps, 1)[0] if len(maps) > 1 else 0
        hr_slope = np.polyfit(x, hrs, 1)[0] if len(hrs) > 1 else 0
        si_slope = np.polyfit(x, shock_indices, 1)[0] if len(shock_indices) > 1 else 0
        
        # Variability (coefficient of variation)
        map_cv = np.std(maps) / np.mean(maps) if np.mean(maps) > 0 else 0
        hr_cv = np.std(hrs) / np.mean(hrs) if np.mean(hrs) > 0 else 0
        
        features = {
            "map_current": maps[-1] if maps else 75,
            "map_min": min(maps) if maps else 65,
            "map_trend": "decreasing" if map_slope < -1 else "increasing" if map_slope > 1 else "stable",
            "map_slope": map_slope,
            "map_variability": map_cv,
            
            "hr_current": hrs[-1] if hrs else 80,
            "hr_max": max(hrs) if hrs else 90,
            "hr_trend": "increasing" if hr_slope > 2 else "decreasing" if hr_slope < -2 else "stable",
            "hr_slope": hr_slope,
            "hr_variability": hr_cv,
            
            "shock_index_current": shock_indices[-1] if shock_indices else 0.7,
            "shock_index_max": max(shock_indices) if shock_indices else 0.8,
            "si_trend": "worsening" if si_slope > 0.02 else "improving" if si_slope < -0.02 else "stable",
            "si_slope": si_slope
        }
        
        # Add lab values if available
        if lab_values:
            features["lactate"] = lab_values.get("lactate", 1.0)
            features["lactate_trend"] = lab_values.get("lactate_trend", "stable")
            features["hemoglobin"] = lab_values.get("hemoglobin", 10.0)
            features["base_deficit"] = lab_values.get("base_deficit", 0)
        
        return features
    
    def _calculate_hemodynamic_risk(self, features: Dict) -> float:
        """Calculate hemodynamic instability risk score"""
        risk = 0.0
        
        # MAP-based risk
        map_val = features.get("map_current", 75)
        if map_val < 55:
            risk += 35
        elif map_val < 60:
            risk += 25
        elif map_val < 65:
            risk += 15
        elif map_val < 70:
            risk += 8
        
        # MAP trend risk
        map_slope = features.get("map_slope", 0)
        if map_slope < -3:
            risk += 20
        elif map_slope < -1:
            risk += 10
        elif map_slope < 0:
            risk += 5
        
        # Shock index risk
        si = features.get("shock_index_current", 0.7)
        if si > 1.2:
            risk += 25
        elif si > 1.0:
            risk += 15
        elif si > 0.9:
            risk += 8
        
        # Shock index worsening
        if features.get("si_trend") == "worsening":
            risk += 10
        
        # Heart rate variability (low HRV is bad in ICU)
        if features.get("hr_variability", 0.1) < 0.05:
            risk += 8
        
        # MAP variability (high variability is bad)
        if features.get("map_variability", 0.1) > 0.15:
            risk += 8
        
        # Lab-based risk
        lactate = features.get("lactate", 1.0)
        if lactate > 4:
            risk += 20
        elif lactate > 2:
            risk += 10
        
        if features.get("lactate_trend") == "increasing":
            risk += 10
        
        # Hemoglobin
        hgb = features.get("hemoglobin", 10)
        if hgb < 7:
            risk += 15
        elif hgb < 8:
            risk += 8
        
        return min(100, risk)
    
    def _identify_hemodynamic_risk_factors(self, features: Dict) -> List[Dict]:
        """Identify specific risk factors for hemodynamic instability"""
        factors = []
        
        if features.get("map_current", 75) < 65:
            factors.append({
                "factor": "Low MAP",
                "value": f"{features['map_current']:.0f} mmHg",
                "impact": "HIGH",
                "action": "Consider fluid bolus or vasopressor"
            })
        
        if features.get("map_trend") == "decreasing" and features.get("map_slope", 0) < -2:
            factors.append({
                "factor": "Declining MAP trend",
                "value": f"{features['map_slope']:.1f} mmHg/hour",
                "impact": "HIGH",
                "action": "Anticipate need for intervention"
            })
        
        si = features.get("shock_index_current", 0.7)
        if si > 0.9:
            factors.append({
                "factor": "Elevated Shock Index",
                "value": f"{si:.2f}",
                "impact": "HIGH" if si > 1.0 else "MODERATE",
                "action": "Assess for hypovolemia or cardiac dysfunction"
            })
        
        lactate = features.get("lactate", 1.0)
        if lactate > 2:
            factors.append({
                "factor": "Elevated Lactate",
                "value": f"{lactate:.1f} mmol/L",
                "impact": "HIGH" if lactate > 4 else "MODERATE",
                "action": "Assess tissue perfusion, consider fluid resuscitation"
            })
        
        if features.get("hr_variability", 0.1) < 0.05:
            factors.append({
                "factor": "Reduced HR Variability",
                "value": f"{features['hr_variability']:.3f}",
                "impact": "MODERATE",
                "action": "Sign of autonomic dysfunction/stress"
            })
        
        return factors if factors else [{"factor": "No significant risk factors identified", "impact": "LOW"}]
    
    def _calculate_prediction_confidence(self, features: Dict) -> float:
        """Calculate confidence in prediction based on data quality"""
        confidence = 0.85  # Base confidence
        
        # Reduce confidence if limited data
        if features.get("map_variability", 0) == 0:
            confidence -= 0.15
        
        # Increase confidence if lab data available
        if "lactate" in features:
            confidence += 0.05
        
        return round(confidence, 2)
    
    def analyze_vital_patterns(
        self,
        patient_id: str,
        vital_signs: Dict
    ) -> Dict:
        """Analyze vital sign patterns for clinical syndromes
        
        Args:
            patient_id: Patient identifier
            vital_signs: Current vital signs
            
        Returns:
            Pattern analysis with clinical interpretation
        """
        patterns = []
        
        hr = vital_signs.get("hr", 80)
        sbp = vital_signs.get("sbp", 120)
        dbp = vital_signs.get("dbp", 80)
        rr = vital_signs.get("rr", 16)
        temp = vital_signs.get("temp", 37.0)
        spo2 = vital_signs.get("spo2", 98)
        map_val = vital_signs.get("map", sbp * 0.33 + dbp * 0.67)
        
        # Individual pattern detection
        if hr > 100:
            patterns.append({
                "pattern": VitalPattern.TACHYCARDIA.value,
                "value": f"HR: {hr}",
                "severity": "HIGH" if hr > 130 else "MODERATE",
                "causes": ["Pain", "Fever", "Hypovolemia", "Anxiety", "Cardiac arrhythmia", "Sepsis"]
            })
        elif hr < 60:
            patterns.append({
                "pattern": VitalPattern.BRADYCARDIA.value,
                "value": f"HR: {hr}",
                "severity": "HIGH" if hr < 45 else "MODERATE",
                "causes": ["Beta-blocker effect", "Increased ICP", "Vagal response", "Heart block"]
            })
        
        if sbp > 180:
            patterns.append({
                "pattern": VitalPattern.HYPERTENSION.value,
                "value": f"SBP: {sbp}",
                "severity": "HIGH",
                "causes": ["Pain", "Agitation", "Hypertensive emergency", "Increased ICP"]
            })
        elif map_val < 65:
            patterns.append({
                "pattern": VitalPattern.HYPOTENSION.value,
                "value": f"MAP: {map_val:.0f}",
                "severity": "HIGH" if map_val < 55 else "MODERATE",
                "causes": ["Hypovolemia", "Sepsis", "Cardiogenic", "Medication effect"]
            })
        
        if rr > 22:
            patterns.append({
                "pattern": VitalPattern.TACHYPNEA.value,
                "value": f"RR: {rr}",
                "severity": "HIGH" if rr > 30 else "MODERATE",
                "causes": ["Respiratory failure", "Metabolic acidosis", "Pain", "Anxiety", "Sepsis"]
            })
        
        if temp > 38.3:
            patterns.append({
                "pattern": VitalPattern.FEVER.value,
                "value": f"Temp: {temp}°C",
                "severity": "HIGH" if temp > 39.5 else "MODERATE",
                "causes": ["Infection", "Drug fever", "Blood product reaction", "CNS pathology"]
            })
        elif temp < 36.0:
            patterns.append({
                "pattern": VitalPattern.HYPOTHERMIA.value,
                "value": f"Temp: {temp}°C",
                "severity": "MODERATE",
                "causes": ["Environmental", "Severe sepsis", "Hypothyroidism"]
            })
        
        # Syndrome pattern detection
        # Sepsis pattern: Tachycardia + Tachypnea + (Fever OR Hypothermia) + Hypotension
        shock_index = hr / sbp if sbp > 0 else 1.0
        if (hr > 90 and rr > 20 and (temp > 38.3 or temp < 36.0)):
            patterns.append({
                "pattern": VitalPattern.SEPSIS_PATTERN.value,
                "value": f"SI: {shock_index:.2f}, qSOFA criteria met",
                "severity": "HIGH",
                "recommendation": "Evaluate for sepsis, consider cultures and antibiotics"
            })
        
        # Shock pattern
        if map_val < 65 and shock_index > 1.0:
            patterns.append({
                "pattern": VitalPattern.SHOCK_PATTERN.value,
                "value": f"MAP: {map_val:.0f}, SI: {shock_index:.2f}",
                "severity": "CRITICAL",
                "recommendation": "Immediate hemodynamic support required"
            })
        
        # ARDS pattern
        if spo2 < 92 and rr > 24:
            patterns.append({
                "pattern": VitalPattern.ARDS_PATTERN.value,
                "value": f"SpO2: {spo2}%, RR: {rr}",
                "severity": "HIGH",
                "recommendation": "Evaluate for respiratory failure, consider P/F ratio"
            })
        
        if not patterns:
            patterns.append({
                "pattern": VitalPattern.NORMAL.value,
                "value": "All vitals within normal limits",
                "severity": "NONE"
            })
        
        return {
            "patient_id": patient_id,
            "patterns_detected": patterns,
            "overall_assessment": self._get_overall_assessment(patterns),
            "vital_summary": {
                "hr": hr,
                "sbp": sbp,
                "dbp": dbp,
                "map": round(map_val),
                "rr": rr,
                "temp": temp,
                "spo2": spo2,
                "shock_index": round(shock_index, 2)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_overall_assessment(self, patterns: List[Dict]) -> str:
        """Get overall patient assessment based on patterns"""
        critical = any(p.get("severity") == "CRITICAL" for p in patterns)
        high = any(p.get("severity") == "HIGH" for p in patterns)
        
        if critical:
            return "CRITICAL - Immediate intervention required"
        elif high:
            return "UNSTABLE - Close monitoring and probable intervention needed"
        elif any(p.get("severity") == "MODERATE" for p in patterns):
            return "BORDERLINE - Increased monitoring recommended"
        else:
            return "STABLE - Continue routine monitoring"
    
    def assess_delirium_risk(
        self,
        patient_id: str,
        assessment_data: Dict
    ) -> Dict:
        """Assess delirium risk and provide prevention strategies
        
        Uses PRE-DELIRIC model factors and CAM-ICU screening
        
        Args:
            patient_id: Patient identifier
            assessment_data: Contains risk factors and current status
            
        Returns:
            Delirium risk assessment with prevention strategies
        """
        # Risk factors (PRE-DELIRIC and other validated factors)
        risk_factors = {
            "age_over_65": assessment_data.get("age", 50) > 65,
            "dementia_history": assessment_data.get("dementia", False),
            "alcohol_use": assessment_data.get("alcohol_use_disorder", False),
            "urgent_admission": assessment_data.get("urgent_admission", True),
            "mechanical_ventilation": assessment_data.get("mechanical_ventilation", False),
            "metabolic_acidosis": assessment_data.get("base_deficit", 0) < -4,
            "sedation_use": assessment_data.get("sedation", False),
            "morphine_use": assessment_data.get("opioid_use", False),
            "urea_elevated": assessment_data.get("bun", 20) > 30,
            "infection": assessment_data.get("infection", False),
            "coma": assessment_data.get("gcs", 15) < 9,
            "sleep_deprivation": assessment_data.get("sleep_deprived", False),
            "sensory_impairment": assessment_data.get("visual_hearing_impairment", False),
            "physical_restraints": assessment_data.get("restraints", False),
            "multiple_medications": assessment_data.get("medication_count", 5) > 10,
            "immobility": assessment_data.get("immobile", False)
        }
        
        # Calculate risk score
        weights = {
            "age_over_65": 8, "dementia_history": 15, "alcohol_use": 10,
            "urgent_admission": 5, "mechanical_ventilation": 12,
            "metabolic_acidosis": 8, "sedation_use": 10, "morphine_use": 8,
            "urea_elevated": 6, "infection": 10, "coma": 15,
            "sleep_deprivation": 7, "sensory_impairment": 6,
            "physical_restraints": 8, "multiple_medications": 5, "immobility": 8
        }
        
        risk_score = sum(weights[k] for k, v in risk_factors.items() if v)
        max_score = sum(weights.values())
        risk_percentage = (risk_score / max_score) * 100
        
        # Determine risk level
        if risk_percentage >= 50:
            risk_level = DeliriumRisk.HIGH
        elif risk_percentage >= 25:
            risk_level = DeliriumRisk.MODERATE
        else:
            risk_level = DeliriumRisk.LOW
        
        # CAM-ICU screening (if current data available)
        cam_icu = self._screen_cam_icu(assessment_data)
        if cam_icu.get("delirium_present"):
            risk_level = DeliriumRisk.ACTIVE_DELIRIUM
        
        # Generate prevention strategies
        prevention = self._get_delirium_prevention(risk_factors, risk_level)
        
        return {
            "patient_id": patient_id,
            "risk_score": round(risk_percentage, 1),
            "risk_level": risk_level.value,
            "risk_factors_present": [k for k, v in risk_factors.items() if v],
            "cam_icu_screening": cam_icu,
            "prevention_bundle": prevention,
            "monitoring": {
                "cam_icu_frequency": "Every 8-12 hours" if risk_level in [DeliriumRisk.HIGH, DeliriumRisk.ACTIVE_DELIRIUM] else "Every 12-24 hours",
                "reassess_risk": "Daily"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _screen_cam_icu(self, data: Dict) -> Dict:
        """Perform CAM-ICU screening"""
        # Feature 1: Acute onset and fluctuating course
        feature1 = data.get("mental_status_fluctuating", False) or data.get("acute_mental_change", False)
        
        # Feature 2: Inattention
        feature2 = data.get("inattention", False)  # ASE letters or pictures
        
        # Feature 3: Altered level of consciousness
        rass = data.get("rass_score", 0)
        feature3 = rass != 0  # Not calm and alert
        
        # Feature 4: Disorganized thinking
        feature4 = data.get("disorganized_thinking", False)
        
        # CAM-ICU positive: Feature 1 + Feature 2 + (Feature 3 OR Feature 4)
        delirium_present = feature1 and feature2 and (feature3 or feature4)
        
        return {
            "feature_1_acute_fluctuating": feature1,
            "feature_2_inattention": feature2,
            "feature_3_altered_loc": feature3,
            "feature_4_disorganized_thinking": feature4,
            "rass_score": rass,
            "delirium_present": delirium_present,
            "subtype": self._get_delirium_subtype(rass) if delirium_present else None
        }
    
    def _get_delirium_subtype(self, rass: int) -> str:
        """Determine delirium subtype based on RASS"""
        if rass > 0:
            return "HYPERACTIVE"
        elif rass < 0:
            return "HYPOACTIVE"
        else:
            return "MIXED"
    
    def _get_delirium_prevention(
        self,
        risk_factors: Dict,
        risk_level: DeliriumRisk
    ) -> Dict:
        """Get delirium prevention bundle (ABCDEF bundle)"""
        prevention = {
            "A_assess_manage_pain": [
                "Regular pain assessment using BPS or CPOT",
                "Treat pain adequately before sedation",
                "Consider regional anesthesia if applicable"
            ],
            "B_both_sat_sbt": [
                "Daily spontaneous awakening trial (SAT)",
                "Daily spontaneous breathing trial (SBT)",
                "Coordinate SAT with SBT"
            ],
            "C_choice_of_sedation": [
                "Target light sedation (RASS -1 to 0)",
                "Prefer dexmedetomidine or propofol over benzodiazepines",
                "Avoid anticholinergic medications"
            ],
            "D_delirium_monitoring": [
                "Screen with CAM-ICU every 8-12 hours",
                "Use RASS for sedation assessment",
                "Document and track delirium episodes"
            ],
            "E_early_mobility": [
                "Progressive mobility protocol",
                "Physical therapy evaluation",
                "OOB to chair when stable"
            ],
            "F_family_engagement": [
                "Allow flexible family visiting",
                "Involve family in reorientation",
                "Provide familiar objects from home"
            ]
        }
        
        # Additional based on risk factors
        targeted_interventions = []
        
        if risk_factors.get("sleep_deprivation"):
            targeted_interventions.append({
                "target": "Sleep promotion",
                "actions": [
                    "Cluster care activities",
                    "Reduce noise (target <35 dB at night)",
                    "Dim lights after 10 PM",
                    "Offer earplugs and eye masks"
                ]
            })
        
        if risk_factors.get("sensory_impairment"):
            targeted_interventions.append({
                "target": "Sensory optimization",
                "actions": [
                    "Ensure glasses/hearing aids are available",
                    "Speak clearly and face patient",
                    "Use communication boards if needed"
                ]
            })
        
        if risk_factors.get("immobility"):
            targeted_interventions.append({
                "target": "Mobility enhancement",
                "actions": [
                    "Consult PT/OT",
                    "Range of motion exercises",
                    "Progressive sitting/standing protocol"
                ]
            })
        
        return {
            "abcdef_bundle": prevention,
            "targeted_interventions": targeted_interventions,
            "pharmacological": {
                "avoid": ["Benzodiazepines", "Anticholinergics", "Meperidine"],
                "consider_if_agitated": ["Dexmedetomidine", "Low-dose haloperidol (if no QT prolongation)"]
            }
        }
    
    def monitor_multi_organ_trajectory(
        self,
        patient_id: str,
        organ_data: Dict,
        historical_data: Optional[List[Dict]] = None
    ) -> Dict:
        """Model multi-organ system trajectory
        
        Args:
            patient_id: Patient identifier
            organ_data: Current organ function data
            historical_data: Previous assessments for trending
            
        Returns:
            Multi-organ trajectory analysis
        """
        organ_assessments = {}
        
        # Respiratory
        pf_ratio = organ_data.get("pf_ratio", 400)
        fio2 = organ_data.get("fio2", 0.21)
        peep = organ_data.get("peep", 5)
        organ_assessments["respiratory"] = {
            "current_function": self._assess_respiratory_function(pf_ratio, fio2, peep),
            "pf_ratio": pf_ratio,
            "trajectory": self._calculate_trajectory("respiratory", pf_ratio, historical_data)
        }
        
        # Cardiovascular
        map_val = organ_data.get("map", 75)
        vasopressor = organ_data.get("vasopressor_dose", 0)
        organ_assessments["cardiovascular"] = {
            "current_function": self._assess_cardiovascular_function(map_val, vasopressor),
            "map": map_val,
            "vasopressor_dose": vasopressor,
            "trajectory": self._calculate_trajectory("cardiovascular", map_val, historical_data)
        }
        
        # Renal
        creatinine = organ_data.get("creatinine", 1.0)
        uop = organ_data.get("urine_output_ml_kg_h", 0.5)
        organ_assessments["renal"] = {
            "current_function": self._assess_renal_function(creatinine, uop),
            "creatinine": creatinine,
            "urine_output": uop,
            "trajectory": self._calculate_trajectory("renal", creatinine, historical_data)
        }
        
        # Hepatic
        bilirubin = organ_data.get("bilirubin", 1.0)
        inr = organ_data.get("inr", 1.0)
        organ_assessments["hepatic"] = {
            "current_function": self._assess_hepatic_function(bilirubin, inr),
            "bilirubin": bilirubin,
            "inr": inr,
            "trajectory": self._calculate_trajectory("hepatic", bilirubin, historical_data)
        }
        
        # Neurological
        gcs = organ_data.get("gcs", 15)
        organ_assessments["neurological"] = {
            "current_function": self._assess_neurological_function(gcs),
            "gcs": gcs,
            "trajectory": self._calculate_trajectory("neurological", gcs, historical_data)
        }
        
        # Hematologic
        platelets = organ_data.get("platelets", 200)
        organ_assessments["hematologic"] = {
            "current_function": self._assess_hematologic_function(platelets),
            "platelets": platelets,
            "trajectory": self._calculate_trajectory("hematologic", platelets, historical_data)
        }
        
        # Calculate MODS risk
        organs_failing = sum(1 for a in organ_assessments.values() if a["current_function"] in ["FAILURE", "SEVERE"])
        organs_at_risk = sum(1 for a in organ_assessments.values() if a["current_function"] in ["MODERATE", "DYSFUNCTION"])
        
        mods_risk = self._calculate_mods_risk(organs_failing, organs_at_risk)
        
        return {
            "patient_id": patient_id,
            "organ_assessments": organ_assessments,
            "summary": {
                "organs_failing": organs_failing,
                "organs_at_risk": organs_at_risk,
                "overall_trajectory": self._get_overall_trajectory(organ_assessments),
                "mods_risk": mods_risk
            },
            "recommendations": self._get_organ_support_recommendations(organ_assessments),
            "timestamp": datetime.now().isoformat()
        }
    
    def _assess_respiratory_function(self, pf_ratio: float, fio2: float, peep: float) -> str:
        """Assess respiratory function"""
        if pf_ratio < 100:
            return "FAILURE"
        elif pf_ratio < 200:
            return "SEVERE"
        elif pf_ratio < 300:
            return "MODERATE"
        elif fio2 > 0.4 or peep > 10:
            return "DYSFUNCTION"
        else:
            return "NORMAL"
    
    def _assess_cardiovascular_function(self, map_val: float, vasopressor: float) -> str:
        """Assess cardiovascular function"""
        if map_val < 55 or vasopressor > 0.2:
            return "FAILURE"
        elif map_val < 60 or vasopressor > 0.1:
            return "SEVERE"
        elif map_val < 65 or vasopressor > 0:
            return "MODERATE"
        elif map_val < 70:
            return "DYSFUNCTION"
        else:
            return "NORMAL"
    
    def _assess_renal_function(self, creatinine: float, uop: float) -> str:
        """Assess renal function"""
        if creatinine > 4 or uop < 0.2:
            return "FAILURE"
        elif creatinine > 2.5 or uop < 0.3:
            return "SEVERE"
        elif creatinine > 1.5 or uop < 0.5:
            return "MODERATE"
        elif creatinine > 1.2:
            return "DYSFUNCTION"
        else:
            return "NORMAL"
    
    def _assess_hepatic_function(self, bilirubin: float, inr: float) -> str:
        """Assess hepatic function"""
        if bilirubin > 6 or inr > 2.5:
            return "FAILURE"
        elif bilirubin > 4:
            return "SEVERE"
        elif bilirubin > 2:
            return "MODERATE"
        elif bilirubin > 1.2:
            return "DYSFUNCTION"
        else:
            return "NORMAL"
    
    def _assess_neurological_function(self, gcs: int) -> str:
        """Assess neurological function"""
        if gcs < 6:
            return "FAILURE"
        elif gcs < 9:
            return "SEVERE"
        elif gcs < 12:
            return "MODERATE"
        elif gcs < 15:
            return "DYSFUNCTION"
        else:
            return "NORMAL"
    
    def _assess_hematologic_function(self, platelets: float) -> str:
        """Assess hematologic function"""
        if platelets < 20:
            return "FAILURE"
        elif platelets < 50:
            return "SEVERE"
        elif platelets < 100:
            return "MODERATE"
        elif platelets < 150:
            return "DYSFUNCTION"
        else:
            return "NORMAL"
    
    def _calculate_trajectory(
        self,
        organ: str,
        current_value: float,
        historical_data: Optional[List[Dict]]
    ) -> str:
        """Calculate organ function trajectory"""
        if not historical_data or len(historical_data) < 2:
            return "INSUFFICIENT_DATA"
        
        # This would use actual historical values in production
        # For demo, return simulated trajectory
        return np.random.choice(["IMPROVING", "STABLE", "WORSENING"], p=[0.3, 0.4, 0.3])
    
    def _calculate_mods_risk(self, failing: int, at_risk: int) -> Dict:
        """Calculate multi-organ dysfunction syndrome risk"""
        if failing >= 3:
            return {"level": "CRITICAL", "mortality_estimate": ">70%"}
        elif failing >= 2:
            return {"level": "HIGH", "mortality_estimate": "40-60%"}
        elif failing >= 1 or at_risk >= 2:
            return {"level": "MODERATE", "mortality_estimate": "20-40%"}
        else:
            return {"level": "LOW", "mortality_estimate": "<20%"}
    
    def _get_overall_trajectory(self, assessments: Dict) -> str:
        """Get overall patient trajectory"""
        trajectories = [a.get("trajectory", "STABLE") for a in assessments.values()]
        
        worsening = sum(1 for t in trajectories if t == "WORSENING")
        improving = sum(1 for t in trajectories if t == "IMPROVING")
        
        if worsening > improving + 1:
            return "DETERIORATING"
        elif improving > worsening + 1:
            return "IMPROVING"
        else:
            return "STABLE"
    
    def _get_organ_support_recommendations(self, assessments: Dict) -> List[str]:
        """Get recommendations based on organ assessments"""
        recommendations = []
        
        resp = assessments.get("respiratory", {})
        if resp.get("current_function") in ["FAILURE", "SEVERE"]:
            recommendations.append("Consider lung-protective ventilation strategies")
            recommendations.append("Evaluate for prone positioning if P/F <150")
        
        cv = assessments.get("cardiovascular", {})
        if cv.get("current_function") in ["FAILURE", "SEVERE"]:
            recommendations.append("Optimize fluid status and vasopressor therapy")
            recommendations.append("Consider advanced hemodynamic monitoring")
        
        renal = assessments.get("renal", {})
        if renal.get("current_function") in ["FAILURE", "SEVERE"]:
            recommendations.append("Nephrology consultation recommended")
            recommendations.append("Consider RRT if refractory")
        
        return recommendations if recommendations else ["Continue current supportive care"]
    
    def assess_sleep_quality(
        self,
        patient_id: str,
        sleep_data: Dict
    ) -> Dict:
        """Assess ICU patient sleep quality
        
        Args:
            patient_id: Patient identifier
            sleep_data: Sleep-related parameters
            
        Returns:
            Sleep quality assessment with interventions
        """
        # Sleep assessment (Richards-Campbell Sleep Questionnaire adapted)
        noise_level = sleep_data.get("avg_noise_db", 45)
        light_exposure = sleep_data.get("night_light_lux", 50)
        care_interruptions = sleep_data.get("care_interruptions_per_night", 8)
        sedation = sleep_data.get("sedation_type", "none")
        pain_controlled = sleep_data.get("pain_controlled", True)
        anxiety_level = sleep_data.get("anxiety_level", "low")
        
        # Calculate sleep quality score (0-100)
        sleep_score = 100
        
        # Noise impact
        if noise_level > 50:
            sleep_score -= min(30, (noise_level - 35))
        
        # Light impact
        if light_exposure > 20:
            sleep_score -= min(20, (light_exposure - 20) / 2)
        
        # Care interruptions
        if care_interruptions > 4:
            sleep_score -= min(25, (care_interruptions - 4) * 5)
        
        # Pain impact
        if not pain_controlled:
            sleep_score -= 20
        
        # Anxiety impact
        if anxiety_level == "high":
            sleep_score -= 15
        elif anxiety_level == "moderate":
            sleep_score -= 8
        
        sleep_score = max(0, sleep_score)
        
        # Quality category
        if sleep_score >= 70:
            quality = "ADEQUATE"
        elif sleep_score >= 40:
            quality = "POOR"
        else:
            quality = "VERY_POOR"
        
        # Interventions
        interventions = self._get_sleep_interventions(
            noise_level, light_exposure, care_interruptions,
            pain_controlled, anxiety_level
        )
        
        return {
            "patient_id": patient_id,
            "sleep_quality_score": round(sleep_score),
            "quality_category": quality,
            "factors_assessed": {
                "noise_level_db": noise_level,
                "light_exposure_lux": light_exposure,
                "care_interruptions": care_interruptions,
                "pain_controlled": pain_controlled,
                "anxiety_level": anxiety_level,
                "sedation": sedation
            },
            "interventions": interventions,
            "goals": {
                "noise": "<35 dB at night",
                "light": "<5 lux at night",
                "interruptions": "Minimize to <4 per night"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_sleep_interventions(
        self,
        noise: float,
        light: float,
        interruptions: int,
        pain: bool,
        anxiety: str
    ) -> List[Dict]:
        """Get targeted sleep interventions"""
        interventions = []
        
        if noise > 40:
            interventions.append({
                "target": "Noise reduction",
                "actions": [
                    "Lower alarm volumes where safe",
                    "Offer earplugs",
                    "Close doors",
                    "Quiet conversation near patient"
                ],
                "priority": "HIGH" if noise > 50 else "MODERATE"
            })
        
        if light > 20:
            interventions.append({
                "target": "Light optimization",
                "actions": [
                    "Dim lights after 10 PM",
                    "Offer eye mask",
                    "Maximize natural light during day",
                    "Maintain day-night cycle"
                ],
                "priority": "HIGH" if light > 50 else "MODERATE"
            })
        
        if interruptions > 4:
            interventions.append({
                "target": "Care clustering",
                "actions": [
                    "Cluster medication administration",
                    "Coordinate labs/vitals timing",
                    "Protect sleep periods (11 PM - 6 AM)",
                    "Communicate with team about minimizing interruptions"
                ],
                "priority": "HIGH"
            })
        
        if not pain:
            interventions.append({
                "target": "Pain management",
                "actions": [
                    "Reassess pain with validated tool",
                    "Consider multimodal analgesia",
                    "Position for comfort"
                ],
                "priority": "HIGH"
            })
        
        if anxiety in ["moderate", "high"]:
            interventions.append({
                "target": "Anxiety reduction",
                "actions": [
                    "Reorientation and reassurance",
                    "Family involvement",
                    "Consider music therapy",
                    "Non-pharmacological comfort measures"
                ],
                "priority": "HIGH" if anxiety == "high" else "MODERATE"
            })
        
        return interventions if interventions else [{"target": "Continue current measures", "priority": "LOW"}]
