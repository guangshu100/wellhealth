"""数据挖掘服务"""
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from collections import Counter, defaultdict
import math

from sqlalchemy.orm import Session
from sqlalchemy import text, bindparam

logger = logging.getLogger(__name__)


class DataMiningService:
    """数据挖掘服务 - 提供历史数据分析和仿真推演"""

    def disease_trajectory(self, db: Session, patient_id: Optional[str], time_range: str) -> Dict[str, Any]:
        """疾病轨迹分析"""
        cache_key = self._cache_key("disease_trajectory", {"patient_id": patient_id, "time_range": time_range})
        cached = self._get_cached_result(db, cache_key)
        if cached:
            return cached

        months = self._parse_time_range(time_range)
        cutoff = datetime.utcnow() - timedelta(days=months * 30)

        if patient_id:
            rows = db.execute(text(
                "SELECT glucose_value, glucose_type, measurement_time FROM glucose_records "
                "WHERE patient_id = :pid AND measurement_time >= :cutoff "
                "ORDER BY measurement_time"
            ), {"pid": patient_id, "cutoff": cutoff}).mappings().all()

            trajectory = []
            for row in rows:
                trajectory.append({
                    "date": row["measurement_time"].isoformat() if row["measurement_time"] else None,
                    "values": {"blood_sugar": float(row["glucose_value"])} if row["glucose_value"] is not None else {},
                })

            transition_matrix = self._compute_transition_matrix(trajectory)

            result = {
                "patient_id": patient_id,
                "time_range": time_range,
                "trajectory": trajectory,
                "transition_matrix": transition_matrix,
                "data_points": len(trajectory),
            }
        else:
            rows = db.execute(text(
                "SELECT disease_name, COUNT(*) AS cnt FROM disease_records "
                "GROUP BY disease_name ORDER BY cnt DESC"
            )).mappings().all()

            result = {
                "time_range": time_range,
                "disease_distribution": [
                    {"disease": row["disease_name"], "count": row["cnt"]} for row in rows
                ],
            }

        self._save_cached_result(db, cache_key, result)
        return result

    def indicator_pattern(self, db: Session, patient_id: str, indicators: List[str]) -> Dict[str, Any]:
        """指标规律分析"""
        cache_key = self._cache_key("indicator_pattern", {"patient_id": patient_id, "indicators": sorted(indicators)})
        cached = self._get_cached_result(db, cache_key)
        if cached:
            return cached

        rows = db.execute(text(
            "SELECT glucose_value, glucose_type, measurement_time FROM glucose_records "
            "WHERE patient_id = :pid ORDER BY measurement_time"
        ), {"pid": patient_id}).mappings().all()

        all_values = []
        for row in rows:
            all_values.append({
                "date": row["measurement_time"].isoformat() if row["measurement_time"] else None,
                "value": float(row["glucose_value"]) if row["glucose_value"] is not None else None,
            })

        patterns = {}
        for indicator in indicators:
            if indicator in ("blood_sugar", "血糖"):
                values = [v for v in all_values if v["value"] is not None]
            else:
                values = []

            if len(values) >= 2:
                numeric_vals = [v["value"] for v in values]
                seasonality = self._detect_seasonality(numeric_vals)

                patterns[indicator] = {
                    "values": values,
                    "mean": sum(numeric_vals) / len(numeric_vals),
                    "std": self._std(numeric_vals),
                    "min": min(numeric_vals),
                    "max": max(numeric_vals),
                    "correlations": {},
                    "seasonality": seasonality,
                }
            else:
                patterns[indicator] = {"values": values, "message": "数据不足"}

        result = {"patient_id": patient_id, "patterns": patterns}
        self._save_cached_result(db, cache_key, result)
        return result

    def whatif_simulation(self, db: Session, patient_id: str, intervention: Dict[str, Any]) -> Dict[str, Any]:
        """What-If仿真推演"""
        cache_key = self._cache_key("whatif_simulation", {"patient_id": patient_id, "intervention": intervention})
        cached = self._get_cached_result(db, cache_key)
        if cached:
            return cached

        rows = db.execute(text(
            "SELECT glucose_value FROM glucose_records "
            "WHERE patient_id = :pid ORDER BY measurement_time DESC LIMIT 30"
        ), {"pid": patient_id}).mappings().all()

        baseline = {}
        glucose_vals = [float(r["glucose_value"]) for r in rows if r["glucose_value"] is not None]
        if glucose_vals:
            baseline["blood_sugar"] = sum(glucose_vals) / len(glucose_vals)

        intervention_type = intervention.get("type", "")
        duration = intervention.get("duration", 3)

        simulation_result = self._run_simulation(baseline, intervention_type, duration)

        result = {
            "patient_id": patient_id,
            "intervention": intervention,
            "baseline": baseline,
            "prediction": simulation_result["prediction"],
            "shap_values": simulation_result["shap_values"],
            "confidence": simulation_result["confidence"],
        }
        self._save_cached_result(db, cache_key, result)
        return result

    def comorbidity_network(
        self, db: Session, patient_ids: Optional[List[str]], min_support: float
    ) -> Dict[str, Any]:
        """共病网络分析"""
        cache_key = self._cache_key("comorbidity_network", {"patient_ids": patient_ids, "min_support": min_support})
        cached = self._get_cached_result(db, cache_key)
        if cached:
            return cached

        if patient_ids:
            stmt = text(
                "SELECT patient_id, disease_name FROM disease_records "
                "WHERE patient_id IN :pids"
            ).bindparams(bindparam('pids', expanding=True))
            rows = db.execute(stmt, {"pids": patient_ids}).mappings().all()
        else:
            rows = db.execute(text(
                "SELECT patient_id, disease_name FROM disease_records"
            )).mappings().all()

        patient_diseases = defaultdict(set)
        for row in rows:
            patient_diseases[row["patient_id"]].add(row["disease_name"])

        total_patients = len(patient_diseases) or 1
        disease_count = Counter()
        pair_count = Counter()

        for diseases in patient_diseases.values():
            for d in diseases:
                disease_count[d] += 1
            disease_list = sorted(diseases)
            for i in range(len(disease_list)):
                for j in range(i + 1, len(disease_list)):
                    pair_count[(disease_list[i], disease_list[j])] += 1

        nodes = [{"id": d, "count": c, "prevalence": c / total_patients}
                 for d, c in disease_count.most_common(20)]

        edges = []
        for (d1, d2), count in pair_count.most_common(50):
            if count / total_patients >= min_support:
                pmi = math.log2(
                    (count / total_patients) /
                    ((disease_count[d1] / total_patients) * (disease_count[d2] / total_patients) + 1e-10)
                )
                edges.append({
                    "source": d1, "target": d2,
                    "weight": count, "pmi": round(pmi, 3),
                })

        communities = self._detect_communities(nodes, edges)

        result = {
            "network": {"nodes": nodes, "edges": edges},
            "communities": communities,
            "total_patients": total_patients,
        }
        self._save_cached_result(db, cache_key, result)
        return result

    def epidemiology_alert(
        self, db: Session, region: str, indicator: str, threshold: float
    ) -> Dict[str, Any]:
        """流行病学预警"""
        cache_key = self._cache_key("epidemiology_alert", {"region": region, "indicator": indicator, "threshold": threshold})
        cached = self._get_cached_result(db, cache_key)
        if cached:
            return cached

        cutoff = datetime.utcnow() - timedelta(days=30)
        rows = db.execute(text(
            "SELECT patient_id, glucose_value FROM glucose_records "
            "WHERE measurement_time >= :cutoff"
        ), {"cutoff": cutoff}).mappings().all()

        values = []
        for row in rows:
            if row["glucose_value"] is not None:
                try:
                    values.append(float(row["glucose_value"]))
                except (ValueError, TypeError):
                    pass

        if not values:
            result = {"alerts": [], "message": "无足够数据"}
            self._save_cached_result(db, cache_key, result)
            return result

        mean = sum(values) / len(values)
        std = self._std(values)

        alerts = []
        for row in rows:
            if row["glucose_value"] is not None:
                try:
                    val = float(row["glucose_value"])
                    z_score = (val - mean) / (std + 1e-10)
                    if abs(z_score) > threshold:
                        alerts.append({
                            "patient_id": row["patient_id"],
                            "value": val,
                            "z_score": round(z_score, 2),
                            "severity": "high" if abs(z_score) > 3 else "medium",
                        })
                except (ValueError, TypeError):
                    pass

        result = {
            "indicator": indicator,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "alerts": alerts,
            "affected_patients": len(set(a["patient_id"] for a in alerts)),
            "total_records": len(values),
        }
        self._save_cached_result(db, cache_key, result)
        return result

    # ---- Helper Methods ----

    def _parse_time_range(self, time_range: str) -> int:
        """解析时间范围"""
        mapping = {"1m": 1, "3m": 3, "6m": 6, "1y": 12, "2y": 24}
        return mapping.get(time_range, 6)

    def _compute_transition_matrix(self, trajectory: List[Dict]) -> Dict[str, Any]:
        """计算简化转移矩阵"""
        if len(trajectory) < 2:
            return {"states": [], "matrix": []}

        states = ["low", "normal", "elevated", "high"]
        transitions = defaultdict(lambda: defaultdict(int))

        prev_state = None
        for point in trajectory:
            values = point.get("values", {})
            bs = values.get("blood_sugar") or values.get("血糖")
            if bs is not None:
                try:
                    bs_val = float(bs)
                    if bs_val < 3.9:
                        curr_state = "low"
                    elif bs_val < 7.0:
                        curr_state = "normal"
                    elif bs_val < 11.1:
                        curr_state = "elevated"
                    else:
                        curr_state = "high"

                    if prev_state:
                        transitions[prev_state][curr_state] += 1
                    prev_state = curr_state
                except (ValueError, TypeError):
                    pass

        matrix = []
        for from_state in states:
            row = []
            total = sum(transitions[from_state].values()) or 1
            for to_state in states:
                row.append(round(transitions[from_state].get(to_state, 0) / total, 3))
            matrix.append(row)

        return {"states": states, "matrix": matrix}

    def _detect_seasonality(self, values: List[float]) -> Dict[str, Any]:
        """检测季节性（简化）"""
        if len(values) < 7:
            return {"detected": False, "message": "数据不足"}

        n = len(values)
        if n < 14:
            return {"detected": False, "period": None}

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n

        if variance < 1e-10:
            return {"detected": False, "period": None}

        lag = min(7, n // 2)
        autocorr = sum(
            (values[i] - mean) * (values[i + lag] - mean)
            for i in range(n - lag)
        ) / ((n - lag) * variance)

        return {
            "detected": abs(autocorr) > 0.3,
            "period": 7 if abs(autocorr) > 0.3 else None,
            "autocorrelation": round(autocorr, 3),
        }

    def _run_simulation(
        self, baseline: Dict[str, float], intervention_type: str, duration: int
    ) -> Dict[str, Any]:
        """运行仿真推演（简化）"""
        prediction = []
        shap_values = {}

        bs_baseline = baseline.get("blood_sugar", baseline.get("血糖", 7.0))

        if intervention_type == "stop_medication":
            for month in range(1, duration + 1):
                prediction.append({
                    "month": month,
                    "blood_sugar": round(bs_baseline + month * 0.3, 1),
                    "risk_level": "increasing",
                })
            shap_values = {"medication_discontinuation": 0.65, "disease_progression": 0.25, "other": 0.10}
        elif intervention_type == "add_exercise":
            for month in range(1, duration + 1):
                prediction.append({
                    "month": month,
                    "blood_sugar": round(max(bs_baseline - month * 0.2, 5.0), 1),
                    "risk_level": "decreasing",
                })
            shap_values = {"exercise": 0.45, "diet_improvement": 0.20, "weight_loss": 0.15, "other": 0.20}
        elif intervention_type == "diet_change":
            for month in range(1, duration + 1):
                prediction.append({
                    "month": month,
                    "blood_sugar": round(max(bs_baseline - month * 0.15, 5.5), 1),
                    "risk_level": "decreasing",
                })
            shap_values = {"dietary_change": 0.40, "calorie_reduction": 0.25, "other": 0.35}
        else:
            for month in range(1, duration + 1):
                prediction.append({
                    "month": month,
                    "blood_sugar": round(bs_baseline, 1),
                    "risk_level": "stable",
                })
            shap_values = {"baseline": 0.50, "natural_variation": 0.30, "other": 0.20}

        confidence = max(0.5, 0.9 - duration * 0.05)

        return {
            "prediction": prediction,
            "shap_values": shap_values,
            "confidence": round(confidence, 2),
        }

    def _detect_communities(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """简化的社区检测"""
        if not edges:
            return []

        adjacency = defaultdict(set)
        for edge in edges:
            adjacency[edge["source"]].add(edge["target"])
            adjacency[edge["target"]].add(edge["source"])

        visited = set()
        communities = []
        community_id = 0

        for node in nodes:
            node_id = node["id"]
            if node_id not in visited:
                community = set()
                queue = [node_id]
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        community.add(current)
                        queue.extend(adjacency[current] - visited)

                if len(community) > 1:
                    community_id += 1
                    communities.append({
                        "id": community_id,
                        "members": list(community),
                        "size": len(community),
                    })

        return communities

    @staticmethod
    def _spearman_correlation(x: List[float], y: List[float]) -> float:
        """计算Spearman秩相关"""
        n = len(x)
        if n < 3:
            return 0.0

        def rank_data(data):
            sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
            ranks = [0] * len(data)
            for i, idx in enumerate(sorted_indices):
                ranks[idx] = i + 1
            return ranks

        rx = rank_data(x)
        ry = rank_data(y)

        d_squared = sum((rx[i] - ry[i]) ** 2 for i in range(n))
        return 1 - (6 * d_squared) / (n * (n ** 2 - 1))

    @staticmethod
    def _std(values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1))

    # ---- Cache Helper Methods ----

    def _cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        raw = f"{method}:{json.dumps(params, sort_keys=True, default=str)}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cached_result(self, db: Session, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        try:
            row = db.execute(text(
                "SELECT result_data FROM mining_result_cache "
                "WHERE parameters = :key AND expires_at > :now LIMIT 1"
            ), {"key": cache_key, "now": datetime.utcnow()}).mappings().first()

            if row and row["result_data"]:
                return json.loads(row["result_data"])
        except Exception as e:
            logger.warning(f"Cache read failed for key {cache_key}: {e}")
        return None

    def _save_cached_result(self, db: Session, cache_key: str, result: Dict[str, Any]) -> None:
        """保存缓存结果"""
        try:
            existing = db.execute(text(
                "SELECT id FROM mining_result_cache WHERE parameters = :key LIMIT 1"
            ), {"key": cache_key}).mappings().first()

            now = datetime.utcnow()
            expires = now + timedelta(hours=24)
            result_json = json.dumps(result, default=str, ensure_ascii=False)

            if existing:
                db.execute(text(
                    "UPDATE mining_result_cache SET result_data = :data, expires_at = :expires "
                    "WHERE parameters = :key"
                ), {"data": result_json, "expires": expires, "key": cache_key})
            else:
                db.execute(text(
                    "INSERT INTO mining_result_cache "
                    "(result_type, parameters, result_data, expires_at, is_mock, create_time) "
                    "VALUES (:type, :key, :data, :expires, :mock, :ctime)"
                ), {
                    "type": "mining",
                    "key": cache_key,
                    "data": result_json,
                    "expires": expires,
                    "mock": 0,
                    "ctime": now,
                })
            db.commit()
        except Exception as e:
            logger.warning(f"Cache save failed for key {cache_key}: {e}")
            db.rollback()


_service = None


def get_data_mining_service() -> DataMiningService:
    """获取数据挖掘服务单例"""
    global _service
    if _service is None:
        _service = DataMiningService()
    return _service
