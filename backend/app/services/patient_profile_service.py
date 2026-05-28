"""患者全景画像服务"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from app.models.models import Patient
from app.models.family_models import HealthAlert

logger = logging.getLogger(__name__)


class PatientProfileService:
    """患者全景画像服务 - 聚合多源数据"""

    def generate_panorama(self, db: Session, patient_id: str) -> Dict[str, Any]:
        """生成患者全景画像"""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": "患者不存在"}

        chronic_diseases = self._get_chronic_diseases(db, patient_id)
        medications = self._get_medications(db, patient_id)
        vital_trends = self._get_vital_trends(db, patient_id)
        interventions = self._get_interventions(db, patient_id)
        missing_indicators = self._detect_missing_indicators(db, patient_id)
        risk_prediction = self._predict_risk(chronic_diseases, vital_trends, missing_indicators)

        return {
            "patient_id": patient_id,
            "patient_name": patient.name,
            "generated_at": datetime.utcnow().isoformat(),
            "chronic_diseases": chronic_diseases,
            "current_medications": medications,
            "vital_trends": vital_trends,
            "interventions": interventions,
            "missing_indicators": missing_indicators,
            "risk_prediction": risk_prediction,
        }

    def _get_chronic_diseases(self, db: Session, patient_id: str) -> List[Dict]:
        """获取慢病概览"""
        rows = db.execute(text(
            "SELECT disease_name, diagnosed_date, status FROM disease_records "
            "WHERE patient_id = :pid"
        ), {"pid": patient_id}).mappings().all()

        result = []
        for row in rows:
            result.append({
                "disease": row["disease_name"],
                "diagnosed_date": row["diagnosed_date"].isoformat() if row["diagnosed_date"] else None,
                "control_status": self._assess_control_status(row["disease_name"], patient_id, db),
            })
        return result

    def _assess_control_status(self, disease_name: str, patient_id: str, db: Session) -> str:
        """评估疾病控制状态"""
        rows = db.execute(text(
            "SELECT glucose_value FROM glucose_records "
            "WHERE patient_id = :pid ORDER BY measurement_time DESC LIMIT 10"
        ), {"pid": patient_id}).mappings().all()

        if not rows:
            return "数据不足"

        glucose_vals = []
        for row in rows:
            if row["glucose_value"] is not None:
                try:
                    glucose_vals.append(float(row["glucose_value"]))
                except (ValueError, TypeError):
                    pass

        if not glucose_vals:
            return "数据不足"

        if "糖尿病" in disease_name or "血糖" in disease_name:
            avg_bs = sum(glucose_vals) / len(glucose_vals)
            if avg_bs < 7.0:
                return "良好"
            elif avg_bs < 9.0:
                return "一般"
            else:
                return "较差"

        return "待评估"

    def _get_medications(self, db: Session, patient_id: str) -> List[Dict]:
        """获取用药全景"""
        rows = db.execute(text(
            "SELECT drug_name, dosage, frequency FROM medication_records "
            "WHERE patient_id = :pid"
        ), {"pid": patient_id}).mappings().all()

        return [
            {
                "drug": row["drug_name"],
                "dosage": row["dosage"],
                "frequency": row["frequency"],
            }
            for row in rows
        ]

    def _get_vital_trends(self, db: Session, patient_id: str) -> Dict[str, Any]:
        """获取指标趋势"""
        cutoff = datetime.utcnow() - timedelta(days=90)
        rows = db.execute(text(
            "SELECT glucose_value, measurement_time FROM glucose_records "
            "WHERE patient_id = :pid AND measurement_time >= :cutoff "
            "ORDER BY measurement_time"
        ), {"pid": patient_id, "cutoff": cutoff}).mappings().all()

        trends = {}
        for row in rows:
            if row["glucose_value"] is None:
                continue
            key = "blood_sugar"
            if key not in trends:
                trends[key] = {"values": [], "dates": []}
            try:
                trends[key]["values"].append(float(row["glucose_value"]))
                trends[key]["dates"].append(
                    row["measurement_time"].isoformat() if row["measurement_time"] else None
                )
            except (ValueError, TypeError):
                pass

        result = {}
        for key, data in trends.items():
            latest = data["values"][-1] if data["values"] else None
            trend = self._calculate_trend(data["values"])
            target = self._get_target_value(key)
            result[key] = {
                "latest": latest,
                "trend": trend,
                "target": target,
                "data_points": len(data["values"]),
            }
        return result

    def _get_interventions(self, db: Session, patient_id: str) -> List[Dict]:
        """获取干预记录"""
        alerts = (
            db.query(HealthAlert)
            .filter(HealthAlert.patient_id == patient_id)
            .order_by(desc(HealthAlert.created_at))
            .limit(10)
            .all()
        )
        return [
            {
                "type": alert.alert_type,
                "date": alert.created_at.isoformat() if alert.created_at else None,
                "detail": alert.content,
            }
            for alert in alerts
        ]

    def _detect_missing_indicators(self, db: Session, patient_id: str) -> List[Dict]:
        """检测缺失指标"""
        rows = db.execute(text(
            "SELECT glucose_value, measurement_time FROM glucose_records "
            "WHERE patient_id = :pid"
        ), {"pid": patient_id}).mappings().all()

        has_glucose = any(row["glucose_value"] is not None for row in rows)

        cutoff_30 = datetime.utcnow() - timedelta(days=30)
        recent_rows = [r for r in rows if r["measurement_time"] and r["measurement_time"] >= cutoff_30]
        has_recent_glucose = any(r["glucose_value"] is not None for r in recent_rows)

        missing = []

        if not has_recent_glucose:
            missing.append({"indicator": "血糖", "missing_days": 30, "severity": "critical"})

        if not has_glucose:
            missing.append({"indicator": "体重", "missing_days": 60, "severity": "important"})
            missing.append({"indicator": "血压", "missing_days": 60, "severity": "important"})
            missing.append({"indicator": "血脂", "missing_days": 90, "severity": "general"})

        return missing

    def _predict_risk(
        self, diseases: List[Dict], trends: Dict, missing: List[Dict]
    ) -> Dict[str, Any]:
        """基于画像数据预测风险"""
        complication_risk = "low"
        hospitalization_risk = "low"

        if len(diseases) >= 3:
            complication_risk = "high"
        elif len(diseases) >= 2:
            complication_risk = "medium"

        for key, data in trends.items():
            if data.get("trend") == "worsening":
                if complication_risk != "high":
                    complication_risk = "high"
                hospitalization_risk = "medium"

        critical_missing = [m for m in missing if m.get("severity") == "critical"]
        if len(critical_missing) >= 2:
            hospitalization_risk = "medium"

        return {
            "complication_risk": complication_risk,
            "hospitalization_risk": hospitalization_risk,
        }

    def _calculate_trend(self, values: List) -> str:
        """计算趋势方向"""
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue

        if len(numeric_values) < 2:
            return "stable"

        first_half = numeric_values[:len(numeric_values)//2]
        second_half = numeric_values[len(numeric_values)//2:]

        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        diff = avg_second - avg_first
        threshold = avg_first * 0.05 if avg_first != 0 else 0.1

        if diff > threshold:
            return "rising"
        elif diff < -threshold:
            return "improving"
        else:
            return "stable"

    def _get_target_value(self, indicator: str) -> Optional[str]:
        """获取指标目标值"""
        targets = {
            "blood_sugar": "<7.0 mmol/L",
            "血糖": "<7.0 mmol/L",
            "blood_pressure": "<130/80 mmHg",
            "血压": "<130/80 mmHg",
            "weight": "BMI 18.5-24",
        }
        return targets.get(indicator)


_service: Optional[PatientProfileService] = None


def get_patient_profile_service() -> PatientProfileService:
    global _service
    if _service is None:
        _service = PatientProfileService()
    return _service
