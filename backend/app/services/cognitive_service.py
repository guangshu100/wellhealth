import uuid
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.services.llm_client import get_llm_client
from app.utils.database import get_db_session

logger = logging.getLogger(__name__)


CATEGORY_DATA = {
    "easy": [
        {"category": "降糖食物", "items": ["苦瓜", "燕麦", "荞麦", "山药", "秋葵", "莴笋", "黄瓜", "冬瓜", "芹菜", "菠菜"]},
        {"category": "降压运动", "items": ["散步", "太极拳", "游泳", "瑜伽", "慢跑", "骑自行车", "八段锦", "广场舞"]},
        {"category": "常见药物", "items": ["二甲双胍", "阿司匹林", "硝苯地平", "氨氯地平", "卡托普利", "缬沙坦", "阿卡波糖"]},
    ],
    "medium": [
        {"category": "低GI食物", "items": ["全麦面包", "糙米", "燕麦片", "红薯", "苹果", "柚子", "樱桃", "豆腐", "绿豆", "黑豆"]},
        {"category": "有氧运动", "items": ["快走", "慢跑", "游泳", "骑车", "跳绳", "有氧操", "划船", "椭圆机"]},
        {"category": "心血管药物", "items": ["阿托伐他汀", "氯吡格雷", "美托洛尔", "依那普利", "地高辛", "华法林", "硝酸甘油"]},
    ],
    "hard": [
        {"category": "禁忌食物组合", "items": ["蜂蜜+降糖药", "葡萄柚+他汀", "酒精+甲硝唑", "牛奶+四环素", "茶+铁剂", "西柚+降压药"]},
        {"category": "运动禁忌", "items": ["空腹剧烈运动", "血糖>16.7运动", "视网膜病变负重", "肾病高强度", "神经病变长跑", "足部溃疡负重"]},
        {"category": "药物相互作用", "items": ["二甲双胍+造影剂", "华法林+阿司匹林", "ACEI+螺内酯", "他汀+大环内酯", "磺脲类+酒精"]},
    ],
}

SEQUENCE_DATA = [
    {
        "title": "胰岛素注射流程",
        "steps": ["洗手", "检查胰岛素有效期和性状", "选择注射部位并消毒", "捏起皮肤", "垂直进针注射", "按压推注", "停留10秒后拔针", "按压注射部位(不要揉)", "记录注射时间和剂量", "妥善处理针头"],
        "difficulty": "easy",
    },
    {
        "title": "就诊准备流程",
        "steps": ["整理近期症状记录", "准备既往病历资料", "列出正在服用的药物清单", "记录近期血糖/血压数据", "写下想咨询医生的问题", "准备医保卡和身份证", "预约挂号", "按时就诊"],
        "difficulty": "easy",
    },
    {
        "title": "低血糖急救步骤",
        "steps": ["识别低血糖症状", "立即停止当前活动", "进食15g速效糖(葡萄糖片/果汁)", "等待15分钟", "复测血糖", "如仍低于3.9mmol/L再次补糖", "血糖恢复后进食少量碳水+蛋白质", "记录低血糖事件", "分析原因并调整方案", "严重时拨打120"],
        "difficulty": "medium",
    },
]

WORD_POOLS = {
    "easy": ["苹果", "桌子", "太阳", "花朵", "书本", "电视", "电话", "钥匙", "雨伞", "杯子"],
    "medium": ["医院", "处方", "血压", "血糖", "运动", "饮食", "睡眠", "体重", "心率", "体温"],
    "hard": ["胰岛素", "糖化血红蛋白", "并发症", "低血糖反应", "肾功能", "视网膜", "神经病变", "酮症酸中毒", "黎明现象", "苏木杰效应"],
}


class CognitiveService:

    async def analyze_text(self, text: str, user_id: str) -> Dict[str, Any]:
        llm = get_llm_client()
        system_prompt = (
            "你是一位专业的认知健康评估师，专注于通过语言分析评估认知功能。"
            "请根据用户提供的文本，从以下四个维度评估认知状态：\n"
            "1. 语言能力(language)：词汇丰富度、表达连贯性、用词准确性\n"
            "2. 记忆能力(memory)：时间线索、事件细节、信息完整性\n"
            "3. 执行功能(executive_function)：逻辑组织、因果关系、计划性表达\n"
            "4. 注意力(attention)：话题聚焦、细节关注、信息一致性\n\n"
            "请严格按照以下JSON格式返回评估结果，不要添加任何其他文字：\n"
            "{\n"
            '  "risk_score": 0.0-1.0的浮点数，表示认知衰退风险，\n'
            '  "domain_scores": {\n'
            '    "language": 0.0-1.0,\n'
            '    "memory": 0.0-1.0,\n'
            '    "executive_function": 0.0-1.0,\n'
            '    "attention": 0.0-1.0\n'
            "  },\n"
            '  "evidence": "评估依据的简要说明",\n'
            '  "recommendations": ["建议1", "建议2"],\n'
            '  "confidence": 0.0-1.0的浮点数，表示评估置信度\n'
            "}"
        )

        try:
            response = await llm.chat_with_system(
                system_prompt=system_prompt,
                user_message=f"请评估以下文本的认知功能：\n\n{text}",
                temperature=0.3,
                max_tokens=2000,
            )

            result = self._parse_llm_response(response)

            overall_score = int(result.get("risk_score", 0.5) * 100)
            domain_scores = result.get("domain_scores", {})
            language_score = int(domain_scores.get("language", 0.5) * 100)
            memory_score = int(domain_scores.get("memory", 0.5) * 100)
            executive_function_score = int(domain_scores.get("executive_function", 0.5) * 100)
            attention_score = int(domain_scores.get("attention", 0.5) * 100)

            if overall_score <= 40:
                risk_level = "low"
            elif overall_score <= 70:
                risk_level = "medium"
            else:
                risk_level = "high"

            confidence = result.get("confidence", 0.5)
            recommendations = result.get("recommendations", [])
            evidence = result.get("evidence", "")

            linguistic_features = {
                "text_length": len(text),
                "word_count": len(text),
                "evidence": evidence,
            }

            assessment_id = str(uuid.uuid4())
            with get_db_session() as session:
                from app.models.models import CognitiveAssessment
                assessment = CognitiveAssessment(
                    id=assessment_id,
                    user_id=user_id,
                    assessment_type="text",
                    input_text=text,
                    overall_score=overall_score,
                    risk_level=risk_level,
                    language_score=language_score,
                    memory_score=memory_score,
                    executive_function_score=executive_function_score,
                    attention_score=attention_score,
                    confidence=confidence,
                    recommendations=recommendations,
                    linguistic_features=linguistic_features,
                )
                session.add(assessment)

            return {
                "assessment_id": assessment_id,
                "overall_score": overall_score,
                "risk_level": risk_level,
                "domain_scores": {
                    "language": language_score,
                    "memory": memory_score,
                    "executive_function": executive_function_score,
                    "attention": attention_score,
                },
                "confidence": confidence,
                "recommendations": recommendations,
                "evidence": evidence,
            }

        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            raise

    async def analyze_speech(self, audio_file, user_id: str) -> Dict[str, Any]:
        return {
            "assessment_id": str(uuid.uuid4()),
            "overall_score": None,
            "risk_level": None,
            "domain_scores": {
                "language": None,
                "memory": None,
                "executive_function": None,
                "attention": None,
            },
            "confidence": None,
            "recommendations": ["语音分析功能即将上线，敬请期待"],
            "message": "语音分析功能暂未开放，后续将集成Whisper语音识别模型",
        }

    async def generate_exercise(self, exercise_type: str, difficulty: str) -> Dict[str, Any]:
        if exercise_type == "memory_match":
            return self._generate_memory_match(difficulty)
        elif exercise_type == "category_naming":
            return self._generate_category_naming(difficulty)
        elif exercise_type == "sequence_sorting":
            return self._generate_sequence_sorting(difficulty)
        elif exercise_type == "word_recall":
            return self._generate_word_recall(difficulty)
        else:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

    def _generate_memory_match(self, difficulty: str) -> Dict[str, Any]:
        pair_count = {"easy": 4, "medium": 6, "hard": 8}.get(difficulty, 6)
        pool = WORD_POOLS.get(difficulty, WORD_POOLS["medium"])
        selected = random.sample(pool, min(pair_count, len(pool)))
        pairs = selected + selected
        random.shuffle(pairs)
        return {
            "exercise_type": "memory_match",
            "difficulty": difficulty,
            "data": {
                "pairs": pairs,
                "pair_count": pair_count,
                "time_limit": pair_count * 15,
            },
            "cognitive_domains": ["memory", "attention"],
        }

    def _generate_category_naming(self, difficulty: str) -> Dict[str, Any]:
        diff_key = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}.get(difficulty, difficulty)
        categories = CATEGORY_DATA.get(diff_key, CATEGORY_DATA["medium"])
        selected = random.choice(categories)
        return {
            "exercise_type": "category_naming",
            "difficulty": difficulty,
            "data": {
                "category": selected["category"],
                "item_count": len(selected["items"]),
                "time_limit": 60,
            },
            "cognitive_domains": ["language", "memory", "executive_function"],
        }

    def _generate_sequence_sorting(self, difficulty: str) -> Dict[str, Any]:
        diff_key = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}.get(difficulty, difficulty)
        matching = [s for s in SEQUENCE_DATA if s["difficulty"] == diff_key]
        if not matching:
            matching = SEQUENCE_DATA
        selected = random.choice(matching)
        shuffled_steps = selected["steps"][:]
        random.shuffle(shuffled_steps)
        return {
            "exercise_type": "sequence_sorting",
            "difficulty": difficulty,
            "data": {
                "title": selected["title"],
                "steps": shuffled_steps,
                "correct_count": len(selected["steps"]),
                "time_limit": len(selected["steps"]) * 10,
            },
            "cognitive_domains": ["executive_function", "memory"],
        }

    def _generate_word_recall(self, difficulty: str) -> Dict[str, Any]:
        pool = WORD_POOLS.get(difficulty, WORD_POOLS["medium"])
        word_count = {"easy": 5, "medium": 7, "hard": 10}.get(difficulty, 7)
        selected = random.sample(pool, min(word_count, len(pool)))
        return {
            "exercise_type": "word_recall",
            "difficulty": difficulty,
            "data": {
                "words": selected,
                "display_time": word_count * 2,
                "recall_time": word_count * 5,
            },
            "cognitive_domains": ["memory", "attention"],
        }

    async def evaluate_session(
        self, exercise_type: str, session_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        if exercise_type == "memory_match":
            score, accuracy = self._evaluate_memory_match(session_data)
        elif exercise_type == "category_naming":
            score, accuracy = self._evaluate_category_naming(session_data)
        elif exercise_type == "sequence_sorting":
            score, accuracy = self._evaluate_sequence_sorting(session_data)
        elif exercise_type == "word_recall":
            score, accuracy = self._evaluate_word_recall(session_data)
        else:
            score = session_data.get("score", 0)
            accuracy = session_data.get("accuracy", 0.0)

        cognitive_domains = self._get_domains_for_exercise(exercise_type)
        duration_seconds = session_data.get("duration_seconds")

        session_id = str(uuid.uuid4())
        with get_db_session() as db:
            from app.models.models import CognitiveTrainingSession
            training = CognitiveTrainingSession(
                id=session_id,
                user_id=user_id,
                exercise_type=exercise_type,
                difficulty=session_data.get("difficulty", "intermediate"),
                score=score,
                accuracy=accuracy,
                duration_seconds=duration_seconds,
                details=session_data.get("details"),
                cognitive_domains=cognitive_domains,
            )
            db.add(training)

        return {
            "session_id": session_id,
            "exercise_type": exercise_type,
            "score": score,
            "accuracy": round(accuracy, 2),
            "cognitive_domains": cognitive_domains,
        }

    def _evaluate_memory_match(self, data: Dict) -> tuple:
        pair_count = data.get("pair_count", 6)
        attempts = data.get("attempts", pair_count * 2)
        correct_matches = data.get("correct_matches", pair_count)
        accuracy = correct_matches / attempts if attempts > 0 else 0
        score = int(min(100, (correct_matches / pair_count) * 100 * (pair_count / max(attempts, pair_count))))
        return score, accuracy

    def _evaluate_category_naming(self, data: Dict) -> tuple:
        category = data.get("category", "")
        user_answers = data.get("user_answers", [])
        diff_key = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}.get(
            data.get("difficulty", "intermediate"), data.get("difficulty", "intermediate")
        )
        correct_items = set()
        for cat_group in CATEGORY_DATA.get(diff_key, CATEGORY_DATA["medium"]):
            if cat_group["category"] == category:
                correct_items = set(cat_group["items"])
                break

        matched = [a for a in user_answers if a in correct_items]
        accuracy = len(matched) / len(user_answers) if user_answers else 0
        coverage = len(matched) / len(correct_items) if correct_items else 0
        score = int(coverage * 70 + accuracy * 30)
        return min(100, score), accuracy

    def _evaluate_sequence_sorting(self, data: Dict) -> tuple:
        user_order = data.get("user_order", [])
        title = data.get("title", "")
        correct_order = []
        for seq in SEQUENCE_DATA:
            if seq["title"] == title:
                correct_order = seq["steps"]
                break

        if not correct_order or not user_order:
            return 0, 0.0

        correct_positions = 0
        for i, step in enumerate(user_order):
            if i < len(correct_order) and step == correct_order[i]:
                correct_positions += 1

        accuracy = correct_positions / len(correct_order)
        score = int(accuracy * 100)
        return score, accuracy

    def _evaluate_word_recall(self, data: Dict) -> tuple:
        original_words = set(data.get("original_words", []))
        recalled_words = set(data.get("recalled_words", []))

        if not original_words:
            return 0, 0.0

        correct = original_words & recalled_words
        accuracy = len(correct) / len(recalled_words) if recalled_words else 0
        recall_rate = len(correct) / len(original_words)
        score = int(recall_rate * 100)
        return score, accuracy

    def _get_domains_for_exercise(self, exercise_type: str) -> List[str]:
        domain_map = {
            "memory_match": ["memory", "attention"],
            "category_naming": ["language", "memory", "executive_function"],
            "sequence_sorting": ["executive_function", "memory"],
            "word_recall": ["memory", "attention"],
        }
        return domain_map.get(exercise_type, [])

    async def get_progress_metrics(self, user_id: str) -> Dict[str, Any]:
        with get_db_session() as db:
            from app.models.models import CognitiveTrainingSession, CognitiveAssessment
            from sqlalchemy import func

            sessions = db.query(CognitiveTrainingSession).filter(
                CognitiveTrainingSession.user_id == user_id
            ).order_by(CognitiveTrainingSession.created_at.desc()).all()

            assessments = db.query(CognitiveAssessment).filter(
                CognitiveAssessment.user_id == user_id
            ).order_by(CognitiveAssessment.created_at.desc()).all()

        total_sessions = len(sessions)
        total_assessments = len(assessments)

        if total_sessions > 0:
            avg_score = sum(s.score for s in sessions if s.score is not None) / total_sessions
            avg_accuracy = sum(s.accuracy for s in sessions if s.accuracy is not None) / total_sessions
        else:
            avg_score = 0
            avg_accuracy = 0

        exercise_counts = {}
        domain_scores = {}
        for s in sessions:
            exercise_counts[s.exercise_type] = exercise_counts.get(s.exercise_type, 0) + 1
            if s.cognitive_domains and s.score is not None:
                for domain in s.cognitive_domains:
                    if domain not in domain_scores:
                        domain_scores[domain] = []
                    domain_scores[domain].append(s.score)

        domain_averages = {}
        for domain, scores in domain_scores.items():
            domain_averages[domain] = round(sum(scores) / len(scores), 1)

        consistency_score = 0.0
        if total_sessions >= 2:
            dates = sorted(set(s.created_at.date() for s in sessions if s.created_at))
            if len(dates) >= 2:
                intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_interval = sum(intervals) / len(intervals)
                consistency_score = round(max(0, 1 - avg_interval / 10), 2)

        latest_assessment = None
        if assessments:
            a = assessments[0]
            latest_assessment = {
                "overall_score": a.overall_score,
                "risk_level": a.risk_level,
                "language_score": a.language_score,
                "memory_score": a.memory_score,
                "executive_function_score": a.executive_function_score,
                "attention_score": a.attention_score,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }

        return {
            "total_sessions": total_sessions,
            "total_assessments": total_assessments,
            "avg_score": round(avg_score, 1),
            "avg_accuracy": round(avg_accuracy, 2),
            "exercise_counts": exercise_counts,
            "domain_averages": domain_averages,
            "consistency_score": consistency_score,
            "latest_assessment": latest_assessment,
        }

    async def get_assessment_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with get_db_session() as db:
            from app.models.models import CognitiveAssessment
            assessments = db.query(CognitiveAssessment).filter(
                CognitiveAssessment.user_id == user_id
            ).order_by(CognitiveAssessment.created_at.desc()).limit(limit).all()

        result = []
        for a in assessments:
            result.append({
                "id": a.id,
                "assessment_type": a.assessment_type,
                "overall_score": a.overall_score,
                "risk_level": a.risk_level,
                "language_score": a.language_score,
                "memory_score": a.memory_score,
                "executive_function_score": a.executive_function_score,
                "attention_score": a.attention_score,
                "confidence": a.confidence,
                "recommendations": a.recommendations,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })
        return result

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        try:
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return {
                "risk_score": 0.5,
                "domain_scores": {
                    "language": 0.5,
                    "memory": 0.5,
                    "executive_function": 0.5,
                    "attention": 0.5,
                },
                "evidence": "无法解析评估结果",
                "recommendations": ["建议重新进行评估"],
                "confidence": 0.3,
            }
