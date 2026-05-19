"""
知识库模块
医学知识图谱构建、RAG检索
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class KnowledgeType(str, Enum):
    """知识类型"""

    DISEASE = "disease"
    DRUG = "drug"
    FOOD = "food"
    EXERCISE = "exercise"
    GUIDELINE = "guideline"
    NURSING = "nursing"
    OTHER = "other"


@dataclass
class KnowledgeItem:
    """知识条目"""

    id: str
    title: str
    content: str
    type: KnowledgeType
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    embedding: Optional[List[float]] = None


class KnowledgeGraph:
    """
    医学知识图谱
    基于Neo4j实现
    """

    ENTITY_TYPES = {
        "Disease": "疾病",
        "Drug": "药物",
        "Symptom": "症状",
        "Food": "食物",
        "Exercise": "运动",
        "Complication": "并发症",
        "Exam": "检查",
    }

    RELATION_TYPES = {
        "TREATS": "治疗",
        "CAUSES": "导致",
        "COMPLICATES": "并发",
        "INTERACTS_WITH": "相互作用",
        "BELONGS_TO": "属于",
        "HAS_SYMPTOM": "有症状",
        "NEED_EXAM": "需要检查",
        "RECOMMEND": "推荐",
    }

    def __init__(self):
        self.initialized = False
        self._client = None

    async def initialize(self):
        """初始化图谱"""
        try:
            from neo4j import AsyncGraphDatabase

            self._client = AsyncGraphDatabase.driver(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            await self._client.verify_connectivity()
            self.initialized = True
            logger.info("Neo4j connected successfully")
        except Exception as e:
            logger.warning(f"Neo4j not available: {e}, using fallback mode")
            self.initialized = False

    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.close()

    async def add_knowledge(self, item: KnowledgeItem):
        """添加知识到图谱"""
        if not self.initialized:
            return

        async with self._client.session() as session:
            await session.run(
                """
                MERGE (d:Disease {name: $title})
                SET d.description = $content
                """,
                title=item.title,
                content=item.content,
            )

    async def query(self, entity: str, relation: str = None) -> List[Dict]:
        """查询知识"""
        if not self.initialized:
            return []

        async with self._client.session() as session:
            if relation:
                result = await session.run(
                    """
                    MATCH (d:Disease)-[r:INTERACTS_WITH]->(d2:Disease)
                    WHERE d.name CONTAINS $entity OR d2.name CONTAINS $entity
                    RETURN d.name, type(r), d2.name
                    """,
                    entity=entity,
                )
            else:
                result = await session.run(
                    """
                    MATCH (d:Disease)
                    WHERE d.name CONTAINS $entity
                    RETURN d
                    """,
                    entity=entity,
                )

            return [dict(record) for record in result]

    async def get_disease_info(self, disease: str) -> Dict:
        """获取疾病信息"""
        if not self.initialized:
            return self._get_mock_disease_info(disease)

        async with self._client.session() as session:
            result = await session.run(
                """
                MATCH (d:Disease {name: $disease})
                OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
                OPTIONAL MATCH (d)-[:COMPLICATES]->(c:Complication)
                OPTIONAL MATCH (d)<-[:TREATS]-(dr:Drug)
                RETURN d.name as name, d.description as description,
                       collect(DISTINCT s.name) as symptoms,
                       collect(DISTINCT c.name) as complications,
                       collect(DISTINCT dr.name) as treatments
                """,
                disease=disease,
            )

            record = await result.single()
            if record:
                return dict(record)

        return self._get_mock_disease_info(disease)

    def _get_mock_disease_info(self, disease: str) -> Dict:
        """获取模拟疾病信息"""
        mock_data = {
            "糖尿病": {
                "name": "糖尿病",
                "description": "糖尿病是一种以高血糖为特征的代谢性疾病",
                "symptoms": ["多饮", "多食", "多尿", "体重下降"],
                "complications": ["糖尿病肾病", "糖尿病视网膜病变", "糖尿病神经病变"],
                "treatments": ["二甲双胍", "胰岛素", "磺脲类药物"],
            },
            "高血压": {
                "name": "高血压",
                "description": "高血压是以体循环动脉血压增高为主要特征的慢性病",
                "symptoms": ["头痛", "头晕", "胸闷", "疲劳"],
                "complications": ["脑卒中", "冠心病", "肾功能不全"],
                "treatments": ["ACEI类", "ARB类", "钙通道阻滞剂", "利尿剂"],
            },
        }
        return mock_data.get(
            disease,
            {
                "name": disease,
                "description": "",
                "symptoms": [],
                "complications": [],
                "treatments": [],
            },
        )

    async def get_drug_info(self, drug: str) -> Dict:
        """获取药物信息"""
        if not self.initialized:
            return self._get_mock_drug_info(drug)

        async with self._client.session() as session:
            result = await session.run(
                """
                MATCH (dr:Drug {name: $drug})
                OPTIONAL MATCH (dr)-[:INTERACTS_WITH]->(dr2:Drug)
                RETURN dr.name as name, dr.indications as indications,
                       dr.dosage as dosage, dr.side_effects as side_effects,
                       collect(DISTINCT dr2.name) as interactions
                """,
                drug=drug,
            )

            record = await result.single()
            if record:
                return dict(record)

        return self._get_mock_drug_info(drug)

    def _get_mock_drug_info(self, drug: str) -> Dict:
        """获取模拟药物信息"""
        mock_data = {
            "二甲双胍": {
                "name": "二甲双胍",
                "indications": ["2型糖尿病"],
                "dosage": "见说明书",
                "side_effects": ["胃肠道反应", "乳酸酸中毒"],
                "interactions": ["酒精", "碘造影剂"],
            },
            "阿司匹林": {
                "name": "阿司匹林",
                "indications": ["预防心脑血管疾病", "解热镇痛"],
                "dosage": "见说明书",
                "side_effects": ["胃肠道出血", "过敏反应"],
                "interactions": ["华法林", "其他抗凝药物"],
            },
        }
        return mock_data.get(
            drug,
            {"name": drug, "indications": [], "dosage": "", "side_effects": [], "interactions": []},
        )

    async def check_drug_interaction(self, drug1: str, drug2: str) -> Dict:
        """检查药物相互作用"""
        if not self.initialized:
            return self._get_mock_drug_interaction(drug1, drug2)

        async with self._client.session() as session:
            result = await session.run(
                """
                MATCH (d1:Drug {name: $drug1})-[r:INTERACTS_WITH]->(d2:Drug {name: $drug2})
                RETURN r.level as level, r.description as description
                UNION
                MATCH (d2:Drug {name: $drug2})-[r:INTERACTS_WITH]->(d1:Drug {name: $drug1})
                RETURN r.level as level, r.description as description
                """,
                drug1=drug1,
                drug2=drug2,
            )

            record = await result.single()
            if record:
                return {
                    "has_interaction": True,
                    "level": record["level"],
                    "description": record["description"],
                }

        return {"has_interaction": False, "level": "none", "description": ""}

    def _get_mock_drug_interaction(self, drug1: str, drug2: str) -> Dict:
        """模拟药物相互作用检查"""
        known_interactions = {
            ("阿司匹林", "华法林"): {
                "has_interaction": True,
                "level": "high",
                "description": "阿司匹林增强华法林的抗凝作用，增加出血风险",
            },
            ("二甲双胍", "酒精"): {
                "has_interaction": True,
                "level": "moderate",
                "description": "饮酒可能增加乳酸酸中毒风险",
            },
        }

        key = (drug1, drug2)
        reverse_key = (drug2, drug1)

        if key in known_interactions:
            return known_interactions[key]
        if reverse_key in known_interactions:
            return known_interactions[reverse_key]

        return {"has_interaction": False, "level": "none", "description": "未发现明显相互作用"}


class VectorStore:
    """向量存储"""

    def __init__(self):
        self.initialized = False
        self._client = None
        self._collection = None

    async def initialize(self):
        """初始化向量存储"""
        try:
            from qdrant_client import AsyncQdrantClient

            self._client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
            )
            self.initialized = True
            logger.info("Qdrant connected successfully")
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}, using fallback mode")
            self.initialized = False

    async def add(self, item: KnowledgeItem):
        """添加向量"""
        if not self.initialized:
            return

    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """向量搜索"""
        if not self.initialized:
            return []
        return []


def get_knowledge_from_db() -> List[KnowledgeItem]:
    """从数据库获取知识库数据"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal

        db = SessionLocal()
        try:
            result = db.execute(
                text("""
                SELECT id, title, content, type, tags
                FROM knowledge_base 
                WHERE status = 'published'
                ORDER BY id
            """)
            )
            rows = result.fetchall()

            items = []
            for row in rows:
                import json

                tags = json.loads(row[4]) if row[4] else []
                items.append(
                    KnowledgeItem(
                        id=str(row[0]),
                        title=row[1],
                        content=row[2],
                        type=KnowledgeType(row[3]) if row[3] else KnowledgeType.OTHER,
                        tags=tags,
                    )
                )
            return items
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to load knowledge from database: {e}")
        return []


class RAGSystem:
    """
    RAG检索系统
    知识检索 + 生成
    """

    _instance = None
    _db_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.kg = KnowledgeGraph()
            self.vector_store = VectorStore()
            self._fallback_knowledge: List[KnowledgeItem] = []
            self._initialized = True
            self._load_knowledge()

    def _load_knowledge(self):
        """加载知识库，优先从数据库，失败则用内置数据"""
        db_knowledge = get_knowledge_from_db()
        if db_knowledge:
            self._fallback_knowledge = db_knowledge
            RAGSystem._db_loaded = True
            logger.info(f"Loaded {len(self._fallback_knowledge)} knowledge items from database")
        else:
            self._fallback_knowledge = self._init_fallback_knowledge()
            logger.info(f"Using {len(self._fallback_knowledge)} fallback knowledge items")

    async def initialize(self):
        """初始化"""
        await self.kg.initialize()
        await self.vector_store.initialize()

    def _init_fallback_knowledge(self) -> List[KnowledgeItem]:
        """初始化备用知识库"""
        return [
            # 糖尿病相关 (1-15)
            KnowledgeItem(
                id="1",
                title="糖尿病饮食指南",
                content="糖尿病患者应该控制碳水化合物摄入，选择低GI食物，如全谷物、蔬菜等。建议每天摄入碳水化合物占总热量的45-60%。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "饮食", "血糖"],
            ),
            KnowledgeItem(
                id="2",
                title="血糖监测建议",
                content="建议糖尿病患者每天监测空腹血糖，空腹血糖目标值为4.4-7.0 mmol/L。餐后2小时血糖应控制在10.0 mmol/L以下。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "血糖监测"],
            ),
            KnowledgeItem(
                id="3",
                title="糖尿病并发症筛查",
                content="糖尿病并发症筛查建议：眼底检查每年1次，尿蛋白/肌酐比每年1次，足部检查每半年1次，HbA1c每3个月1次。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "并发症", "筛查"],
            ),
            KnowledgeItem(
                id="4",
                title="低血糖处理",
                content="低血糖处理：当血糖<3.9 mmol/L时，轻度可口服葡萄糖15-20g，重度需静脉注射葡萄糖。常见症状：出汗、颤抖、心慌、饥饿感。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "低血糖", "急救"],
            ),
            KnowledgeItem(
                id="5",
                title="糖尿病足护理",
                content="糖尿病足护理：每天检查足部，保持清洁干燥，穿合适鞋子，避免赤脚走路，及时处理伤口。定期进行足部神经和血管检查。",
                type=KnowledgeType.NURSING,
                tags=["糖尿病", "足部", "护理"],
            ),
            KnowledgeItem(
                id="6",
                title="HbA1c控制目标",
                content="糖化血红蛋白(HbA1c)控制目标：一般患者<7%，年轻、病程短、无并发症者可<6.5%，老年、并发症多者可<8%。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "HbA1c", "控制目标"],
            ),
            KnowledgeItem(
                id="7",
                title="糖尿病视网膜病变",
                content="糖尿病视网膜病变是最常见微血管并发症，早期无明显症状。控制血糖、血压、血脂是预防关键。眼底检查是主要筛查方法。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "视网膜", "并发症"],
            ),
            KnowledgeItem(
                id="8",
                title="糖尿病肾病",
                content="糖尿病肾病是主要微血管并发症，早期表现为微量白蛋白尿。控制血糖、血压（<130/80 mmHg），使用ACEI/ARB类药物可延缓进展。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "肾病", "并发症"],
            ),
            KnowledgeItem(
                id="9",
                title="GI食物表",
                content="低GI食物(<55)：全麦面包、燕麦、苹果、梨、牛奶。中GI食物(55-70)：白面包、蜂蜜、西瓜。高GI食物(>70)：白米饭、土豆、西瓜。",
                type=KnowledgeType.FOOD,
                tags=["食物", "GI", "升糖指数"],
            ),
            KnowledgeItem(
                id="10",
                title="GL食物表",
                content="GL=GI×碳水化合物含量÷100。低GL食物(<10)：苹果、梨。中GL食物(11-19)：香蕉、葡萄。高GL食物(>20)：米饭、馒头。",
                type=KnowledgeType.FOOD,
                tags=["食物", "GL", "血糖负荷"],
            ),
            KnowledgeItem(
                id="11",
                title="糖尿病运动处方",
                content="糖尿病运动处方：每周至少150分钟中等强度有氧运动，分5天进行。每次30分钟，运动后心率达到最大心率的50-70%。",
                type=KnowledgeType.EXERCISE,
                tags=["糖尿病", "运动", "处方"],
            ),
            KnowledgeItem(
                id="12",
                title="二甲双胍用药指南",
                content="二甲双胍是2型糖尿病一线用药，餐中或餐后服用以减少胃肠道反应。常见副作用：恶心、腹泻、腹胀。肝肾功能不全者禁用。",
                type=KnowledgeType.DRUG,
                tags=["糖尿病", "二甲双胍", "用药"],
            ),
            KnowledgeItem(
                id="13",
                title="胰岛素存储",
                content="胰岛素存储：未开封2-8°C冷藏，开封后可室温(<30°C)保存30天。避免冷冻、阳光直射、剧烈摇晃。外出携带使用保温包。",
                type=KnowledgeType.DRUG,
                tags=["糖尿病", "胰岛素", "存储"],
            ),
            KnowledgeItem(
                id="14",
                title="糖尿病患者水果选择",
                content="糖尿病患者可适量食用低GI水果：草莓、蓝莓、樱桃、苹果、梨、橙子。建议在两餐之间食用，每天200g以内。",
                type=KnowledgeType.FOOD,
                tags=["糖尿病", "水果", "饮食"],
            ),
            KnowledgeItem(
                id="15",
                title="糖尿病酮症酸中毒",
                content="糖尿病酮症酸中毒(DKA)是严重急性并发症，常见于1型糖尿病。症状：口渴、多尿、恶心呕吐、腹痛、呼气有烂苹果味。需立即就医。",
                type=KnowledgeType.DISEASE,
                tags=["糖尿病", "酮症酸中毒", "急症"],
            ),
            # 高血压相关 (16-30)
            KnowledgeItem(
                id="16",
                title="高血压诊断标准",
                content="高血压诊断标准：收缩压≥140 mmHg或舒张压≥90 mmHg。正常血压：收缩压<120 mmHg且舒张压<80 mmHg。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "诊断", "血压"],
            ),
            KnowledgeItem(
                id="17",
                title="高血压生活方式干预",
                content="高血压生活方式干预包括：限盐（<6g/天）、控制体重（BMI<24）、戒烟限酒、适量运动、保持心理平衡。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "生活方式"],
            ),
            KnowledgeItem(
                id="18",
                title="血压控制目标",
                content="血压控制目标：一般高血压患者<140/90 mmHg，糖尿病患者<130/80 mmHg，老年患者(≥65岁)<150/90 mmHg。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "控制目标"],
            ),
            KnowledgeItem(
                id="19",
                title="高血压药物选择",
                content="常用降压药：利尿剂（氢氯噻嗪）、钙通道阻滞剂（氨氯地平）、ACEI（培哚普利）、ARB（厄贝沙坦）、β受体阻滞剂（美托洛尔）。",
                type=KnowledgeType.DRUG,
                tags=["高血压", "降压药", "用药"],
            ),
            KnowledgeItem(
                id="20",
                title="清晨高血压",
                content="清晨高血压指清晨醒后1小时内血压≥140/90 mmHg。建议使用长效降压药，睡前服用，可监测动态血压评估。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "清晨血压"],
            ),
            KnowledgeItem(
                id="21",
                title="盐敏感性高血压",
                content="盐敏感性高血压患者限盐降压效果明显。建议每日食盐<3g，可使用低钠富钾盐替代。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "限盐"],
            ),
            KnowledgeItem(
                id="22",
                title="高血压急症",
                content="高血压急症：血压≥180/120 mmHg伴靶器官损害。症状：胸痛、呼吸困难、头痛、视力模糊、意识障碍。需立即就医。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "急症"],
            ),
            KnowledgeItem(
                id="23",
                title="运动与高血压",
                content="高血压运动处方：有氧运动为主，快走、慢跑、游泳、骑自行车，每周5-7次，每次30-60分钟。运动强度达到中等，RPE 12-14。",
                type=KnowledgeType.EXERCISE,
                tags=["高血压", "运动"],
            ),
            KnowledgeItem(
                id="24",
                title="DASH饮食",
                content="DASH饮食：富含水果、蔬菜、全谷物、低脂奶制品、坚果。钠摄入<1500mg/天，可降低血压8-14 mmHg。",
                type=KnowledgeType.FOOD,
                tags=["高血压", "DASH", "饮食"],
            ),
            KnowledgeItem(
                id="25",
                title="高血压心血管风险评估",
                content="高血压心血管风险评估因素：年龄、性别、吸烟、总胆固醇、糖尿病、心血管病家族史、左心室肥厚、蛋白尿等。",
                type=KnowledgeType.DISEASE,
                tags=["高血压", "心血管", "风险"],
            ),
            # 高血脂相关 (26-35)
            KnowledgeItem(
                id="26",
                title="血脂检查项目",
                content="血脂检查项目：总胆固醇(TC)、甘油三酯(TG)、低密度脂蛋白(LDL-C)、高密度脂蛋白(HDL-C)。LDL-C是首要治疗目标。",
                type=KnowledgeType.DISEASE,
                tags=["高血脂", "血脂", "检查"],
            ),
            KnowledgeItem(
                id="27",
                title="血脂控制目标",
                content="血脂控制目标：极高危(ASCVD)<1.8 mmol/L，高危<2.6 mmol/L，中危<3.4 mmol/L。HDL-C>1.0 mmol/L(男)/1.2 mmol/L(女)。",
                type=KnowledgeType.DISEASE,
                tags=["高血脂", "控制目标"],
            ),
            KnowledgeItem(
                id="28",
                title="他汀类药物",
                content="他汀类药物是降脂一线用药：阿托伐他汀、瑞舒伐他汀、辛伐他汀等。主要副作用：肝酶升高、肌肉疼痛。定期监测肌酸激酶。",
                type=KnowledgeType.DRUG,
                tags=["高血脂", "他汀", "用药"],
            ),
            KnowledgeItem(
                id="29",
                title="饮食降脂",
                content="降脂饮食：减少饱和脂肪(动物油、肥肉)、反式脂肪(油炸食品)摄入。增加膳食纤维(燕麦、苹果)、植物甾醇(坚果)。",
                type=KnowledgeType.FOOD,
                tags=["高血脂", "饮食"],
            ),
            # 慢病综合 (30-40)
            KnowledgeItem(
                id="30",
                title="慢性病运动处方",
                content="慢性病患者运动建议：每周至少150分钟中等强度有氧运动，如快走、游泳、骑自行车。运动前后监测血压和心率。",
                type=KnowledgeType.EXERCISE,
                tags=["运动", "处方", "慢性病"],
            ),
            KnowledgeItem(
                id="31",
                title="药物服用时间",
                content="不同药物服用时间：二甲双胍餐中或餐后服用，阿司匹林肠溶片空腹服用，他汀类药物晚上服用效果更好。",
                type=KnowledgeType.DRUG,
                tags=["药物", "服用时间"],
            ),
            KnowledgeItem(
                id="32",
                title="慢性病心理支持",
                content="慢性病患者常见心理问题：焦虑、抑郁。应对方法：保持社交活动，培养兴趣爱好、必要时寻求专业心理帮助。",
                type=KnowledgeType.NURSING,
                tags=["心理", "慢性病", "情绪"],
            ),
            KnowledgeItem(
                id="33",
                title="慢病患者体重管理",
                content="体重管理：超重或肥胖患者减轻5-10%体重可显著改善血糖、血压、血脂。目标BMI 18.5-24。",
                type=KnowledgeType.DISEASE,
                tags=["体重", "管理", "肥胖"],
            ),
            KnowledgeItem(
                id="34",
                title="戒烟对慢病的好处",
                content="戒烟好处：降低心血管病风险，改善血压、血脂、肺功能。戒烟后1年冠心病风险下降50%，5年后接近非吸烟者。",
                type=KnowledgeType.NURSING,
                tags=["戒烟", "心血管"],
            ),
            KnowledgeItem(
                id="35",
                title="慢病随访计划",
                content="慢病随访：糖尿病每3个月复查HbA1c，每半年全面检查。高血压每月复查，病情稳定可延长间隔。定期评估并发症。",
                type=KnowledgeType.NURSING,
                tags=["随访", "慢性病"],
            ),
            # 营养知识 (36-45)
            KnowledgeItem(
                id="36",
                title="蛋白质摄入建议",
                content="蛋白质摄入：慢性肾病患者需限制(0.6-0.8g/kg/天)，一般患者1.0-1.2g/kg/天。优质蛋白占50%以上：鱼、蛋、奶、豆制品。",
                type=KnowledgeType.FOOD,
                tags=["营养", "蛋白质"],
            ),
            KnowledgeItem(
                id="37",
                title="膳食纤维摄入",
                content="膳食纤维摄入建议：25-30g/天。可降低血糖、血脂，改善便秘。来源：全谷物、蔬菜、水果、豆类。",
                type=KnowledgeType.FOOD,
                tags=["营养", "膳食纤维"],
            ),
            KnowledgeItem(
                id="38",
                title="钠钾摄入平衡",
                content="钠钾平衡：钠<2000mg/天，钾3600mg/天(男)/2700mg/天(女)。高钾食物：香蕉、橙子、土豆、菠菜。肾功能不全者需注意。",
                type=KnowledgeType.FOOD,
                tags=["营养", "钠", "钾"],
            ),
            KnowledgeItem(
                id="39",
                title="慢病患者饮酒建议",
                content="饮酒建议：糖尿病患者限制饮酒，女性<15g/天，男性<25g/天，每周不超过2次。高血压患者最好戒酒。",
                type=KnowledgeType.FOOD,
                tags=["饮酒", "糖尿病", "高血压"],
            ),
            KnowledgeItem(
                id="40",
                title="维生素D与慢病",
                content="维生素D与慢病：缺乏增加糖尿病、高血压、骨质疏松风险。建议晒太阳15-30分钟/天，或补充400-800IU/天。",
                type=KnowledgeType.NURSING,
                tags=["维生素D", "营养"],
            ),
        ]

    async def retrieve(
        self, query: str, patient_context: Dict = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识
        """
        results = []

        # 1. 优先从向量存储检索
        if self.vector_store.initialized:
            vector_results = await self.vector_store.search(query, top_k)
            results.extend(vector_results)

        # 2. 如果向量检索无结果，使用关键词匹配
        if not results:
            query_lower = query.lower()
            for item in self._fallback_knowledge:
                score = 0
                for tag in item.tags:
                    if tag in query_lower:
                        score += 1
                if score > 0:
                    results.append(
                        {
                            "title": item.title,
                            "content": item.content,
                            "source": item.type.value,
                            "relevance": score / len(item.tags),
                        }
                    )

        # 3. 排序并返回top_k
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return results[:top_k]

    async def generate(
        self, query: str, context: List[Dict[str, Any]], system_prompt: str = ""
    ) -> str:
        """
        基于知识生成回答
        """
        from app.services.llm_client import get_llm_client

        # 构建上下文
        context_text = "\n\n".join([f"【{item['title']}】\n{item['content']}" for item in context])

        # 构建prompt
        prompt = f"""
请根据以下医学知识回答用户问题。如果知识不足以回答，请说明需要咨询专业医生。

相关知识：
{context_text}

用户问题：{query}

回答要求：
1. 基于提供的知识回答
2. 如涉及具体医疗建议，请提醒咨询医生
3. 回答要通俗易懂
"""

        # 调用LLM生成
        try:
            response = await get_llm_client().chat_with_system(
                system_prompt=system_prompt, user_message=prompt, temperature=0.7, max_tokens=1000
            )
            return response
        except Exception as e:
            logger.error(f"RAG generate error: {e}")
            # 如果LLM调用失败，返回基于知识的简单回答
            if context:
                return f"根据知识库：{context[0]['content']}\n\n如需更详细的解答，请咨询专业医生。"
            return "抱歉，暂时无法生成回答，请咨询专业医生。"

    async def query_with_rag(
        self, query: str, patient_context: Dict = None, system_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        RAG完整流程：检索+生成
        """
        # 1. 检索
        context = await self.retrieve(query, patient_context)

        # 2. 生成
        response = await self.generate(query, context, system_prompt)

        return {"response": response, "sources": context, "query": query}


class KnowledgeManager:
    """
    知识库管理器
    负责知识的导入、管理
    """

    def __init__(self):
        self.rag = RAGSystem()
        self.kg = KnowledgeGraph()

    async def initialize(self):
        """初始化"""
        await self.rag.initialize()
        await self.kg.initialize()

    async def add_knowledge(self, item: KnowledgeItem):
        """添加知识"""
        await self.kg.add_knowledge(item)

    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索知识"""
        return await self.rag.retrieve(query, top_k=top_k)

    async def get_recommendations(
        self, patient_diseases: List[str], patient_vitals: Dict = None
    ) -> List[Dict]:
        """获取个性化推荐"""
        recommendations = []

        for disease in patient_diseases:
            disease_info = await self.kg.get_disease_info(disease)

            # 基于疾病生成推荐
            rec = {"disease": disease, "recommendations": []}

            if "糖尿病" in disease:
                rec["recommendations"].extend(
                    [
                        "定期监测血糖",
                        "控制碳水化合物摄入",
                        "每周至少150分钟运动",
                        "每年进行并发症筛查",
                    ]
                )
            elif "高血压" in disease:
                rec["recommendations"].extend(
                    ["限制盐的摄入", "定期测量血压", "保持规律运动", "避免情绪激动"]
                )

            recommendations.append(rec)

        return recommendations

    async def check_medication_safety(self, drugs: List[str]) -> Dict:
        """检查用药安全"""
        if len(drugs) < 2:
            return {"safe": True, "interactions": []}

        interactions = []
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                result = await self.kg.check_drug_interaction(drugs[i], drugs[j])
                if result.get("has_interaction"):
                    interactions.append(
                        {
                            "drug1": drugs[i],
                            "drug2": drugs[j],
                            "level": result.get("level"),
                            "description": result.get("description"),
                        }
                    )

        return {"safe": len(interactions) == 0, "interactions": interactions}


# 全局单例
knowledge_manager = KnowledgeManager()
