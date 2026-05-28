"""处方前置审核服务 - 三层架构"""
import logging
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class PrescriptionReviewService:
    """处方审核服务 - 编排三层审核流程"""

    def __init__(self):
        self._rule_engine = RuleEngineChecker()
        self._insurance_checker = InsurancePolicyChecker()
        self._individualized_checker = IndividualizedReviewer()

    async def review_prescription(
        self,
        db: Session,
        patient_id: str,
        medications: List[Dict[str, Any]],
        diagnosis: List[str],
        patient_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行三层处方审核"""
        review_id = str(uuid.uuid4())
        results = {}

        # Layer 1: 规则引擎检查
        layer1 = self._rule_engine.check(medications, diagnosis, patient_context)
        self._save_review_result(db, review_id, patient_id, "rule_engine", layer1)
        results["rule_engine"] = layer1

        # Layer 2: 医保政策检查
        layer2 = self._insurance_checker.check(medications)
        self._save_review_result(db, review_id, patient_id, "insurance_policy", layer2)
        results["insurance_policy"] = layer2

        # Layer 3: 个体化审核
        layer3 = self._individualized_checker.check(medications, patient_context, diagnosis)
        self._save_review_result(db, review_id, patient_id, "individualized", layer3)
        results["individualized"] = layer3

        # 统一提交所有审核结果
        db.commit()

        # 综合判定
        overall = self._synthesize_results(results)
        overall["review_id"] = review_id
        overall["patient_id"] = patient_id
        overall["reviewed_at"] = datetime.utcnow().isoformat()

        return overall

    def _save_review_result(
        self, db: Session, review_id: str, patient_id: str,
        reviewer_type: str, result: Dict[str, Any]
    ):
        """保存审核结果到数据库"""
        try:
            record_id = str(uuid.uuid4())
            status = result.get("status", "unknown")
            issues_json = json.dumps(result.get("issues"), default=str, ensure_ascii=False) if result.get("issues") else None
            suggestions_json = json.dumps(result.get("suggestions"), default=str, ensure_ascii=False) if result.get("suggestions") else None
            reviewed_at = datetime.utcnow()

            db.execute(text(
                "INSERT INTO prescription_review_results "
                "(id, review_id, patient_id, reviewer_type, status, issues, suggestions, reviewed_at) "
                "VALUES (:id, :review_id, :patient_id, :reviewer_type, :status, :issues, :suggestions, :reviewed_at)"
            ), {
                "id": record_id,
                "review_id": review_id,
                "patient_id": patient_id,
                "reviewer_type": reviewer_type,
                "status": status,
                "issues": issues_json,
                "suggestions": suggestions_json,
                "reviewed_at": reviewed_at,
            })
            db.flush()
        except Exception as e:
            logger.warning(f"Failed to save review result: {e}")

    def _synthesize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """综合三层审核结果"""
        statuses = [r.get("status", "pass") for r in results.values()]

        if any(s == "reject" for s in statuses):
            overall_status = "reject"
        elif any(s == "warning" for s in statuses):
            overall_status = "warning"
        else:
            overall_status = "pass"

        all_issues = []
        all_suggestions = []
        for layer_name, layer_result in results.items():
            for issue in layer_result.get("issues", []):
                if isinstance(issue, dict):
                    issue["layer"] = layer_name
                    all_issues.append(issue)
            for suggestion in layer_result.get("suggestions", []):
                if isinstance(suggestion, dict):
                    suggestion["layer"] = layer_name
                    all_suggestions.append(suggestion)

        return {
            "status": overall_status,
            "layers": results,
            "all_issues": all_issues,
            "all_suggestions": all_suggestions,
            "summary": self._generate_summary(overall_status, all_issues, all_suggestions),
        }

    def _generate_summary(self, status: str, issues: List, suggestions: List) -> str:
        """生成审核摘要"""
        critical_count = sum(1 for i in issues if isinstance(i, dict) and i.get("severity") == "critical")
        major_count = sum(1 for i in issues if isinstance(i, dict) and i.get("severity") == "major")
        warning_count = len(issues) - critical_count - major_count

        if status == "reject":
            return f"审核不通过：{critical_count}项严重问题，{major_count}项重要问题，建议修改后重新审核"
        elif status == "warning":
            return f"审核警告：{warning_count}项警告，{len(suggestions)}条建议，请关注后确认"
        else:
            return "审核通过：未发现明显问题"


class RuleEngineChecker:
    """Layer 1: 规则引擎检查"""

    def check(
        self,
        medications: List[Dict[str, Any]],
        diagnosis: List[str],
        patient_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行规则引擎检查"""
        issues = []
        suggestions = []

        # 1. 药物相互作用检查
        interaction_issues = self._check_drug_interactions(medications)
        issues.extend(interaction_issues)

        # 2. 禁忌症检查
        contraindication_issues = self._check_contraindications(medications, diagnosis)
        issues.extend(contraindication_issues)

        # 3. 重复用药检查
        duplicate_issues = self._check_duplicate_medications(medications)
        issues.extend(duplicate_issues)

        # 4. 剂量范围检查
        dosage_issues = self._check_dosage_ranges(medications, patient_context)
        issues.extend(dosage_issues)

        status = "pass"
        if any(i.get("severity") == "critical" for i in issues):
            status = "reject"
        elif any(i.get("severity") in ("major", "moderate") for i in issues):
            status = "warning"

        return {
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
        }

    def _check_drug_interactions(self, medications: List[Dict]) -> List[Dict]:
        """检查药物相互作用"""
        issues = []
        drug_names = [m.get("drug_name", "") for m in medications]

        # 检查所有药物对
        for i in range(len(drug_names)):
            for j in range(i + 1, len(drug_names)):
                interaction = self._query_interaction(drug_names[i], drug_names[j])
                if interaction:
                    issues.append({
                        "type": "interaction",
                        "severity": interaction["severity"],
                        "drugs": [drug_names[i], drug_names[j]],
                        "detail": interaction["clinical_effect"],
                        "recommendation": interaction["management"],
                    })
        return issues

    def _query_interaction(self, drug_a: str, drug_b: str) -> Optional[Dict]:
        """查询药物相互作用（从数据库或缓存）"""
        # 实际实现需要查询 drug_interaction 表
        # 这里提供基于常见药物相互作用的内置规则
        known_interactions = {
            frozenset(["二甲双胍", "西咪替丁"]): {
                "severity": "major",
                "clinical_effect": "西咪替丁可减少二甲双胍肾清除率，增加乳酸酸中毒风险",
                "management": "避免合用，或减少二甲双胍剂量并密切监测肾功能",
            },
            frozenset(["二甲双胍", "造影剂"]): {
                "severity": "critical",
                "clinical_effect": "碘造影剂可引起肾功能急剧下降，增加乳酸酸中毒风险",
                "management": "造影前48小时停用二甲双胍，造影后48小时复查肾功能后决定是否恢复",
            },
            frozenset(["阿司匹林", "华法林"]): {
                "severity": "critical",
                "clinical_effect": "增加出血风险，尤其消化道出血",
                "management": "避免合用，如必须合用需加用质子泵抑制剂并密切监测INR",
            },
            frozenset(["ACEI", "螺内酯"]): {
                "severity": "major",
                "clinical_effect": "增加高钾血症风险",
                "management": "合用时监测血钾，避免补钾",
            },
            frozenset(["硝苯地平", "美托洛尔"]): {
                "severity": "moderate",
                "clinical_effect": "协同降压，可能引起低血压和心动过缓",
                "management": "合用时从小剂量开始，监测血压和心率",
            },
        }
        return known_interactions.get(frozenset([drug_a, drug_b]))

    def _check_contraindications(self, medications: List[Dict], diagnosis: List[str]) -> List[Dict]:
        """检查禁忌症"""
        issues = []
        # 常见禁忌症规则
        contraindication_rules = [
            {
                "drug": "二甲双胍",
                "contraindicated_if": ["严重肾功能不全", "乳酸酸中毒"],
                "severity": "critical",
                "detail": "严重肾功能不全(eGFR<30)患者禁用二甲双胍",
            },
            {
                "drug": "ACEI",
                "contraindicated_if": ["妊娠", "双侧肾动脉狭窄"],
                "severity": "critical",
                "detail": "妊娠期及双侧肾动脉狭窄患者禁用ACEI",
            },
            {
                "drug": "美托洛尔",
                "contraindicated_if": ["严重心动过缓", "二度以上房室传导阻滞"],
                "severity": "critical",
                "detail": "严重心动过缓或房室传导阻滞患者禁用β受体阻滞剂",
            },
        ]

        for rule in contraindication_rules:
            for med in medications:
                if rule["drug"] in med.get("drug_name", ""):
                    for dx in diagnosis:
                        if any(ci in dx for ci in rule["contraindicated_if"]):
                            issues.append({
                                "type": "contraindication",
                                "severity": rule["severity"],
                                "drugs": [med["drug_name"]],
                                "detail": rule["detail"],
                                "recommendation": "更换为替代药物",
                            })
        return issues

    def _check_duplicate_medications(self, medications: List[Dict]) -> List[Dict]:
        """检查重复用药"""
        issues = []
        drug_classes = {
            "ACEI": ["依那普利", "卡托普利", "赖诺普利", "培哚普利"],
            "ARB": ["缬沙坦", "氯沙坦", "厄贝沙坦", "替米沙坦"],
            "他汀": ["阿托伐他汀", "瑞舒伐他汀", "辛伐他汀"],
            "二甲双胍类": ["二甲双胍", "二甲双胍缓释片"],
        }

        for drug_class, members in drug_classes.items():
            found = [m.get("drug_name", "") for m in medications if any(member in m.get("drug_name", "") for member in members)]
            if len(found) > 1:
                issues.append({
                    "type": "duplicate",
                    "severity": "moderate",
                    "drugs": found,
                    "detail": f"同一类药物({drug_class})使用了多种: {', '.join(found)}",
                    "recommendation": f"建议仅保留一种{drug_class}类药物",
                })
        return issues

    def _check_dosage_ranges(self, medications: List[Dict], patient_context: Dict) -> List[Dict]:
        """检查剂量范围"""
        issues = []
        # 常见药物剂量范围
        dosage_rules = {
            "二甲双胍": {"min": 250, "max": 2550, "unit": "mg/日"},
            "阿托伐他汀": {"min": 10, "max": 80, "unit": "mg/日"},
            "氨氯地平": {"min": 2.5, "max": 10, "unit": "mg/日"},
            "缬沙坦": {"min": 80, "max": 320, "unit": "mg/日"},
        }

        for med in medications:
            drug_name = med.get("drug_name", "")
            dosage_str = med.get("dosage", "")

            for rule_drug, rule in dosage_rules.items():
                if rule_drug in drug_name:
                    try:
                        # 尝试解析剂量数字
                        dosage_val = float("".join(c for c in dosage_str if c.isdigit() or c == "."))
                        if dosage_val > rule["max"]:
                            issues.append({
                                "type": "overdose",
                                "severity": "major",
                                "drugs": [drug_name],
                                "detail": f"剂量{dosage_val}{rule['unit']}超过最大推荐剂量{rule['max']}{rule['unit']}",
                                "recommendation": f"建议减量至{rule['max']}{rule['unit']}以下",
                            })
                        elif dosage_val < rule["min"]:
                            issues.append({
                                "type": "underdose",
                                "severity": "moderate",
                                "drugs": [drug_name],
                                "detail": f"剂量{dosage_val}{rule['unit']}低于最小有效剂量{rule['min']}{rule['unit']}",
                                "recommendation": f"建议增量至{rule['min']}{rule['unit']}以上",
                            })
                    except (ValueError, TypeError):
                        pass
        return issues


class InsurancePolicyChecker:
    """Layer 2: 医保政策检查"""

    def check(self, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行医保政策检查"""
        issues = []
        suggestions = []
        coverage = []

        for med in medications:
            drug_name = med.get("drug_name", "")
            catalog_info = self._query_catalog(drug_name)

            if catalog_info:
                coverage.append({
                    "drug": drug_name,
                    "category": catalog_info["category"],
                    "reimbursement_rate": catalog_info["reimbursement_rate"],
                    "restrictions": catalog_info.get("restrictions"),
                })
                if catalog_info.get("restrictions"):
                    issues.append({
                        "type": "insurance_restriction",
                        "severity": "moderate",
                        "drugs": [drug_name],
                        "detail": f"该药品有医保限制条件: {catalog_info['restrictions']}",
                        "recommendation": "确认是否满足限制条件，否则需自费",
                    })
            else:
                coverage.append({
                    "drug": drug_name,
                    "category": "非医保",
                    "reimbursement_rate": 0,
                    "restrictions": None,
                })
                issues.append({
                    "type": "not_in_catalog",
                    "severity": "moderate",
                    "drugs": [drug_name],
                    "detail": f"{drug_name}不在医保目录内",
                    "recommendation": "考虑替换为同类医保药品",
                })
                # 推荐替代药品
                alternatives = self._find_alternatives(drug_name)
                for alt in alternatives:
                    suggestions.append({
                        "type": "alternative",
                        "drug": drug_name,
                        "alternative": alt["name"],
                        "category": alt["category"],
                        "reimbursement_rate": alt["reimbursement_rate"],
                        "detail": f"可替换为{alt['name']}({alt['category']}，报销{alt['reimbursement_rate']*100:.0f}%)",
                    })

        status = "pass"
        if any(i.get("severity") == "major" for i in issues):
            status = "warning"
        elif issues:
            status = "warning"

        return {
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
            "coverage": coverage,
        }

    def _query_catalog(self, drug_name: str) -> Optional[Dict]:
        """查询医保目录（内置常见药品数据）"""
        catalog = {
            "二甲双胍": {"category": "甲类", "reimbursement_rate": 0.85, "restrictions": None},
            "阿托伐他汀": {"category": "乙类", "reimbursement_rate": 0.70, "restrictions": "限有明确调脂适应症"},
            "氨氯地平": {"category": "甲类", "reimbursement_rate": 0.85, "restrictions": None},
            "缬沙坦": {"category": "乙类", "reimbursement_rate": 0.70, "restrictions": None},
            "美托洛尔": {"category": "甲类", "reimbursement_rate": 0.85, "restrictions": None},
            "阿司匹林": {"category": "甲类", "reimbursement_rate": 0.85, "restrictions": None},
            "硝苯地平": {"category": "甲类", "reimbursement_rate": 0.85, "restrictions": None},
        }
        return catalog.get(drug_name)

    def _find_alternatives(self, drug_name: str) -> List[Dict]:
        """查找替代药品"""
        alternatives_map = {
            "阿托伐他汀": [{"name": "辛伐他汀", "category": "甲类", "reimbursement_rate": 0.85}],
            "缬沙坦": [{"name": "依那普利", "category": "甲类", "reimbursement_rate": 0.85}],
        }
        return alternatives_map.get(drug_name, [])


class IndividualizedReviewer:
    """Layer 3: 个体化审核"""

    def check(
        self,
        medications: List[Dict[str, Any]],
        patient_context: Dict[str, Any],
        diagnosis: List[str],
    ) -> Dict[str, Any]:
        """执行个体化审核"""
        issues = []
        suggestions = []

        age = patient_context.get("age")
        weight = patient_context.get("weight")
        renal_function = patient_context.get("renal_function", "")
        hepatic_function = patient_context.get("hepatic_function", "")
        allergies = patient_context.get("allergies", [])

        # 1. 肾功能相关调整
        renal_issues = self._check_renal_adjustment(medications, renal_function)
        issues.extend(renal_issues)

        # 2. 老年人用药调整
        if age and age >= 65:
            elderly_issues = self._check_elderly_adjustment(medications, age)
            issues.extend(elderly_issues)

        # 3. 过敏检查
        allergy_issues = self._check_allergies(medications, allergies)
        issues.extend(allergy_issues)

        # 4. 体重相关调整
        if weight:
            weight_issues = self._check_weight_adjustment(medications, weight)
            issues.extend(weight_issues)

        status = "pass"
        if any(i.get("severity") == "critical" for i in issues):
            status = "reject"
        elif any(i.get("severity") in ("major", "moderate") for i in issues):
            status = "warning"

        return {
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
        }

    def _check_renal_adjustment(self, medications: List[Dict], renal_function: str) -> List[Dict]:
        """肾功能相关剂量调整"""
        issues = []
        # 解析 eGFR 值
        eGFR = None
        if renal_function:
            try:
                eGFR = float("".join(c for c in renal_function if c.isdigit() or c == "."))
            except (ValueError, TypeError):
                pass

        if eGFR is None:
            return issues

        renal_rules = [
            {
                "drug": "二甲双胍",
                "rules": [
                    {"eGFR_max": 30, "action": "禁用", "severity": "critical", "detail": "eGFR<30禁用二甲双胍"},
                    {"eGFR_max": 45, "action": "减量", "severity": "major", "detail": "eGFR 30-45时二甲双胍减量至最大1000mg/日"},
                ],
            },
            {
                "drug": "ACEI",
                "rules": [
                    {"eGFR_max": 30, "action": "慎用", "severity": "major", "detail": "eGFR<30时ACEI需慎用，监测肾功能"},
                ],
            },
        ]

        for rule in renal_rules:
            for med in medications:
                if rule["drug"] in med.get("drug_name", ""):
                    for r in rule["rules"]:
                        if eGFR < r["eGFR_max"]:
                            issues.append({
                                "type": "renal_adjustment",
                                "severity": r["severity"],
                                "drugs": [med["drug_name"]],
                                "detail": f"{r['detail']}（当前eGFR={eGFR}）",
                                "recommendation": f"建议{r['action']}",
                            })
        return issues

    def _check_elderly_adjustment(self, medications: List[Dict], age: int) -> List[Dict]:
        """老年人用药调整"""
        issues = []
        elderly_rules = {
            "美托洛尔": {"detail": "老年人起始剂量减半", "severity": "moderate"},
            "氨氯地平": {"detail": "老年人起始剂量2.5mg/日", "severity": "moderate"},
        }
        for med in medications:
            drug_name = med.get("drug_name", "")
            for rule_drug, rule in elderly_rules.items():
                if rule_drug in drug_name:
                    issues.append({
                        "type": "elderly_adjustment",
                        "severity": rule["severity"],
                        "drugs": [drug_name],
                        "detail": f"患者{age}岁，{rule['detail']}",
                        "recommendation": "老年人应从小剂量开始，缓慢加量",
                    })
        return issues

    def _check_allergies(self, medications: List[Dict], allergies: List) -> List[Dict]:
        """过敏检查"""
        issues = []
        if not allergies:
            return issues
        for med in medications:
            drug_name = med.get("drug_name", "")
            for allergy in allergies:
                if allergy and allergy in drug_name:
                    issues.append({
                        "type": "allergy",
                        "severity": "critical",
                        "drugs": [drug_name],
                        "detail": f"患者对{allergy}过敏",
                        "recommendation": "禁用该药物，更换为替代药物",
                    })
        return issues

    def _check_weight_adjustment(self, medications: List[Dict], weight: float) -> List[Dict]:
        """体重相关调整"""
        issues = []
        if weight < 50:
            for med in medications:
                drug_name = med.get("drug_name", "")
                if "二甲双胍" in drug_name:
                    issues.append({
                        "type": "weight_adjustment",
                        "severity": "moderate",
                        "drugs": [drug_name],
                        "detail": f"患者体重{weight}kg偏低，二甲双胍起始剂量建议减半",
                        "recommendation": "低体重患者从小剂量开始",
                    })
        return issues


# 全局单例
_service: Optional[PrescriptionReviewService] = None


def get_prescription_review_service() -> PrescriptionReviewService:
    """获取处方审核服务实例"""
    global _service
    if _service is None:
        _service = PrescriptionReviewService()
    return _service
