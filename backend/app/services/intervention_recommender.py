"""
干预建议生成服务
使用LLM根据患者和预测结果生成个性化建议
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DISEASE_NAMES = {"diabetes": "糖尿病", "hypertension": "高血压"}

INTERVENTION_NAMES = {
    "diet": "饮食干预",
    "exercise": "运动干预",
    "medication": "药物调整",
    "lifestyle": "生活方式干预",
    "combined": "综合干预方案",
}


class InterventionRecommender:
    """干预建议生成器 - 使用LLM生成个性化建议"""

    def __init__(self):
        from app.services.llm_client import get_llm_client

        self.llm = get_llm_client()

    async def generate_recommendations(
        self,
        patient_name: str,
        age: int,
        disease: str,
        baseline: Dict[str, float],
        predicted: Dict[str, float],
        intervention_type: str,
        intervention_name: str,
    ) -> List[str]:
        """
        生成个性化建议

        Args:
            patient_name: 患者姓名
            age: 年龄
            disease: 疾病代码 (diabetes/hypertension)
            baseline: 当前指标
            predicted: 预测指标
            intervention_type: 干预类型
            intervention_name: 干预名称

        Returns:
            建议列表
        """
        disease_name = DISEASE_NAMES.get(disease, disease)
        int_name = INTERVENTION_NAMES.get(intervention_type, intervention_name)

        baseline_str = self._format_vitals(baseline)
        predicted_str = self._format_vitals(predicted)

        # 计算变化
        changes = []
        for key in baseline:
            if key in predicted:
                change = predicted[key] - baseline[key]
                change_pct = (change / baseline[key] * 100) if baseline[key] != 0 else 0
                direction = "下降" if change < 0 else "上升"
                changes.append(f"{key}{direction}{abs(change):.1f}({abs(change_pct):.0f}%)")
        changes_str = "，".join(changes)

        prompt = f"""你是一位专业的慢病管理健康顾问。请为患者生成个性化的健康建议。

【患者信息】
- 姓名：{patient_name}
- 年龄：{age}岁
- 疾病：{disease_name}

【当前健康指标】
{baseline_str}

【干预方案】
{int_name}

【预测指标变化】
{predicted_str}
预计变化：{changes_str}

请根据以上信息，生成温暖、专业、实用的健康建议。要求：
1. 第一句是鼓励的话（15字以内）
2. 生成3条具体可执行的建议（每条20字以内）
3. 最后1条是注意事项提醒（20字以内）

请直接输出建议内容，每条一行，不要添加任何格式符号。"""

        try:
            response = await self.llm.chat_with_system(
                system_prompt="你是一位专业的慢病管理健康顾问。输出简洁温暖的专业建议。",
                user_message=prompt,
                temperature=0.5,
                max_tokens=300,
            )

            # 解析结果
            lines = [line.strip() for line in response.split("\n") if line.strip()]

            # 过滤掉空行和特殊字符
            lines = [line for line in lines if line and not line.startswith("#")]

            # 确保至少有建议
            if not lines:
                return self._get_default_recommendations(disease)

            # 限制数量
            return lines[:5]

        except Exception as e:
            logger.warning(f"LLM生成建议失败: {e}")
            return self._get_default_recommendations(disease)

    def _format_vitals(self, vitals: Dict[str, float]) -> str:
        """格式化指标"""
        return "，".join([f"{k}: {v}" for k, v in vitals.items()])

    def _get_default_recommendations(self, disease: str) -> List[str]:
        """获取默认建议"""
        defaults = {
            "diabetes": [
                "坚持就是胜利！",
                "坚持低糖饮食，定时定量",
                "每周至少150分钟中等强度运动",
                "定期监测血糖，按医嘱用药",
            ],
            "hypertension": [
                "健康生活从今天开始！",
                "坚持低盐低脂饮食",
                "规律运动，控制体重",
                "定期测量血压，按时服药",
            ],
        }
        return defaults.get(
            disease, ["坚持干预方案", "定期复查", "保持良好生活习惯", "如有不适及时就医"]
        )


# 全局单例
_recommender = None


def get_recommender() -> InterventionRecommender:
    """获取建议生成器单例"""
    global _recommender
    if _recommender is None:
        _recommender = InterventionRecommender()
    return _recommender
