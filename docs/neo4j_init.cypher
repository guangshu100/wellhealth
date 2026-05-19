// =====================================================
// 康伴(WellHealth) 慢病管理平台 - Neo4j 知识图谱初始化脚本
// 数据库: Neo4j 5.x
// 作者: WellHealth Team
// 描述: 初始化医学知识图谱（疾病、药物、症状、食物、运动等实体及关系）
// =====================================================

// =====================================================
// 第一部分: 创建约束和索引 (可选，Neo4j 5.x自动优化)
// =====================================================

// 禁用自动索引以提高导入速度
SET autocommit = false;

// =====================================================
// 第二部分: 疾病实体
// =====================================================

// 糖尿病
CREATE (d: Disease {
    name: '糖尿病',
    code: 'E11',
    description: '糖尿病是一种以高血糖为特征的代谢性疾病，由于胰岛素分泌缺陷或作用障碍引起。',
    category: '代谢性疾病',
    prevalence: '10.9%'  // 中国成人患病率
});

CREATE (d1: Symptom {name: '多饮'})
CREATE (d2: Symptom {name: '多食'})
CREATE (d3: Symptom {name: '多尿'})
CREATE (d4: Symptom {name: '体重下降'})
CREATE (d5: Symptom {name: '疲乏'})
CREATE (d6: Symptom {name: '视力模糊'})

CREATE (d)-[:HAS_SYMPTOM]->(d1)
CREATE (d)-[:HAS_SYMPTOM]->(d2)
CREATE (d)-[:HAS_SYMPTOM]->(d3)
CREATE (d)-[:HAS_SYMPTOM]->(d4)
CREATE (d)-[:HAS_SYMPTOM]->(d5)
CREATE (d)-[:HAS_SYMPTOM]->(d6)

// 糖尿病并发症
CREATE (c1: Complication {name: '糖尿病视网膜病变', description: '糖尿病微血管并发症，是成人失明的主要原因'})
CREATE (c2: Complication {name: '糖尿病肾病', description: '糖尿病微血管并发症，最终可发展为尿毒症'})
CREATE (c3: Complication {name: '糖尿病神经病变', description: '糖尿病微血管并发症，可导致感觉减退、足部溃疡'})
CREATE (c4: Complication {name: '糖尿病足', description: '足部感染、溃疡、坏疽'})
CREATE (c5: Complication {name: '心血管疾病', description: '冠心病、脑卒中等'})
CREATE (c6: Complication {name: '酮症酸中毒', description: '糖尿病急性并发症，危及生命'})

CREATE (d)-[:COMPLICATES]->(c1)
CREATE (d)-[:COMPLICATES]->(c2)
CREATE (d)-[:COMPLICATES]->(c3)
CREATE (d)-[:COMPLICATES]->(c4)
CREATE (c4)-[:COMPLICATES]->(c5)  // 糖尿病足可导致心血管疾病
CREATE (d)-[:COMPLICATES]->(c6)

// 糖尿病相关检查
CREATE (e1: Exam {name: '空腹血糖', normal_range: '4.4-7.0 mmol/L', description: '空腹状态下的血糖水平'})
CREATE (e2: Exam {name: '餐后2小时血糖', normal_range: '<10.0 mmol/L', description: '餐后2小时血糖水平'})
CREATE (e3: Exam {name: 'HbA1c', normal_range: '<7.0%', description: '糖化血红蛋白，反映近3月平均血糖'})
CREATE (e4: Exam {name: '尿微量白蛋白', normal_range: '<30 mg/24h', description: '评估糖尿病肾病'})
CREATE (e5: Exam {name: '眼底检查', normal_range: '无异常', description: '筛查糖尿病视网膜病变'})
CREATE (e6: Exam {name: '足部检查', normal_range: '无异常', description: '筛查糖尿病足'})

CREATE (d)-[:NEED_EXAM]->(e1)
CREATE (d)-[:NEED_EXAM]->(e2)
CREATE (d)-[:NEED_EXAM]->(e3)
CREATE (d)-[:NEED_EXAM]->(e4)
CREATE (d)-[:NEED_EXAM]->(e5)
CREATE (d)-[:NEED_EXAM]->(e6)

// 高血压
CREATE (h: Disease {
    name: '高血压',
    code: 'I10',
    description: '高血压是以体循环动脉血压增高为主要特征的慢性病，是心脑血管疾病的重要危险因素。',
    category: '心血管疾病',
    prevalence: '27.9%'  // 中国成人患病率
});

CREATE (h1: Symptom {name: '头痛'})
CREATE (h2: Symptom {name: '头晕'})
CREATE (h3: Symptom {name: '胸闷'})
CREATE (h4: Symptom {name: '疲乏'})
CREATE (h5: Symptom {name: '心悸'})
CREATE (h6: Symptom {name: '鼻出血'})

CREATE (h)-[:HAS_SYMPTOM]->(h1)
CREATE (h)-[:HAS_SYMPTOM]->(h2)
CREATE (h)-[:HAS_SYMPTOM]->(h3)
CREATE (h)-[:HAS_SYMPTOM]->(h4)
CREATE (h)-[:HAS_SYMPTOM]->(h5)
CREATE (h)-[:HAS_SYMPTOM]->(h6)

// 高血压并发症
CREATE (hc1: Complication {name: '脑卒中', description: '脑出血或脑梗死'})
CREATE (hc2: Complication {name: '冠心病', description: '冠状动脉粥样硬化性心脏病'})
CREATE (hc3: Complication {name: '心力衰竭', description: '心脏泵血功能减退'})
CREATE (hc4: Complication {name: '肾功能不全', description: '肾脏损害，最终可发展为尿毒症'})
CREATE (hc5: Complication {name: '视网膜病变', description: '眼底血管病变'})

CREATE (h)-[:COMPLICATES]->(hc1)
CREATE (h)-[:COMPLICATES]->(hc2)
CREATE (h)-[:COMPLICATES]->(hc3)
CREATE (h)-[:COMPLICATES]->(hc4)
CREATE (h)-[:COMPLICATES]->(hc5)

// 高血压相关检查
CREATE (he1: Exam {name: '诊室血压', normal_range: '<140/90 mmHg', description: '诊室测量血压'})
CREATE (he2: Exam {name: '家庭血压', normal_range: '<135/85 mmHg', description: '家庭自测血压'})
CREATE (he3: Exam {name: '24小时动态血压', normal_range: '白天<135/85, 夜间<120/70', description: '24小时动态监测'})
CREATE (he4: Exam {name: '心电图', normal_range: '正常', description: '评估心脏电活动'})
CREATE (he5: Exam {name: '超声心动图', normal_range: '正常', description: '评估心脏结构和功能'})

CREATE (h)-[:NEED_EXAM]->(he1)
CREATE (h)-[:NEED_EXAM]->(he2)
CREATE (h)-[:NEED_EXAM]->(he3)
CREATE (h)-[:NEED_EXAM]->(he4)
CREATE (h)-[:NEED_EXAM]->(he5)

// 糖尿病与高血压的关系（糖尿病可导致高血压）
CREATE (d)-[:CAUSES {probability: 0.5}]->(h);

// =====================================================
// 第三部分: 药物实体
// =====================================================

// 糖尿病药物
CREATE (drug1: Drug {
    name: '二甲双胍',
    generic_name: '盐酸二甲双胍',
    category: '双胍类',
    indications: ['2型糖尿病', '肥胖型糖尿病', '糖尿病前期'],
    dosage: '500-2000mg/日，分2-3次服用',
    contraindications: ['严重肝肾功能不全', '酮症酸中毒', '心衰', '酗酒'],
    side_effects: ['胃肠道反应', '乳酸酸中毒', '维生素B12缺乏'],
    manufacturer: '多家'
});

CREATE (drug2: Drug {
    name: '格列齐特',
    generic_name: '格列齐特缓释片',
    category: '磺脲类',
    indications: ['2型糖尿病'],
    dosage: '30-120mg/日，每日1次',
    contraindications: ['1型糖尿病', '严重肝肾功能不全', '酮症酸中毒'],
    side_effects: ['低血糖', '体重增加', '胃肠道反应'],
    manufacturer: '多家'
});

CREATE (drug3: Drug {
    name: '阿卡波糖',
    generic_name: '阿卡波糖片',
    category: 'α-葡萄糖苷酶抑制剂',
    indications: ['2型糖尿病', '糖耐量异常'],
    dosage: '50-100mg/次，每日3次，餐前服用',
    contraindications: ['严重肝肾功能不全', '肠道疾病', '妊娠'],
    side_effects: ['胃肠道胀气', '腹泻', '肝功能异常'],
    manufacturer: '多家'
});

CREATE (drug4: Drug {
    name: '胰岛素',
    generic_name: '重组人胰岛素',
    category: '胰岛素',
    indications: ['1型糖尿病', '2型糖尿病口服药失效', '糖尿病急性并发症', '手术期间'],
    dosage: '个体化，从低剂量开始',
    contraindications: ['低血糖', '胰岛素过敏'],
    side_effects: ['低血糖', '体重增加', '注射部位反应', '水肿'],
    manufacturer: '多家'
});

CREATE (drug5: Drug {
    name: '利拉鲁肽',
    generic_name: '利拉鲁肽注射液',
    category: 'GLP-1受体激动剂',
    indications: ['2型糖尿病', '肥胖'],
    dosage: '0.6-1.8mg/日，每日1次皮下注射',
    contraindications: ['甲状腺髓样癌病史', '胰腺炎', '严重胃肠道疾病'],
    side_effects: ['恶心呕吐', '腹泻', '胰腺炎', '甲状腺C细胞肿瘤风险'],
    manufacturer: '诺和诺德'
});

CREATE (drug6: Drug {
    name: '达格列净',
    generic_name: '达格列净片',
    category: 'SGLT2抑制剂',
    indications: ['2型糖尿病', '心力衰竭', '慢性肾病'],
    dosage: '5-10mg/日，每日1次',
    contraindications: ['严重肝肾功能不全', '酮症酸中毒', '妊娠哺乳'],
    side_effects: ['泌尿系统感染', '生殖系统感染', '体重下降', '酮症酸中毒'],
    manufacturer: '阿斯利康'
});

// 高血压药物
CREATE (drug7: Drug {
    name: '氨氯地平',
    generic_name: '苯磺酸氨氯地平',
    category: '钙通道阻滞剂',
    indications: ['高血压', '冠心病', '心绞痛'],
    dosage: '5-10mg/日，每日1次',
    contraindications: ['严重低血压', '心源性休克', '妊娠'],
    side_effects: ['水肿', '头痛', '面部潮红', '牙龈增生'],
    manufacturer: '多家'
});

CREATE (drug8: Drug {
    name: '厄贝沙坦',
    generic_name: '厄贝沙坦片',
    category: 'ARB类',
    indications: ['高血压', '糖尿病肾病'],
    dosage: '150-300mg/日，每日1次',
    contraindications: ['妊娠', '双侧肾动脉狭窄', '高钾血症'],
    side_effects: ['头晕', '高钾血症', '肾功能恶化', '血管性水肿'],
    manufacturer: '赛诺菲'
});

CREATE (drug9: Drug {
    name: '培哚普利',
    generic_name: '培哚普利片',
    category: 'ACEI类',
    indications: ['高血压', '心力衰竭', '糖尿病肾病'],
    dosage: '4-8mg/日，每日1次',
    contraindications: ['妊娠', '血管性水肿史', '双侧肾动脉狭窄', '高钾血症'],
    side_effects: ['干咳', '高钾血症', '肾功能恶化', '血管性水肿'],
    manufacturer: '施维雅'
});

CREATE (drug10: Drug {
    name: '氢氯噻嗪',
    generic_name: '氢氯噻嗪片',
    category: '利尿剂',
    indications: ['高血压', '水肿', '心力衰竭'],
    dosage: '12.5-50mg/日，每日1-2次',
    contraindications: ['无尿', '严重电解质紊乱', '痛风'],
    side_effects: ['电解质紊乱', '尿酸升高', '血糖升高', '血脂升高'],
    manufacturer: '多家'
});

CREATE (drug11: Drug {
    name: '美托洛尔',
    generic_name: '酒石酸美托洛尔',
    category: 'β受体阻滞剂',
    indications: ['高血压', '冠心病', '心绞痛', '心律失常', '心力衰竭'],
    dosage: '25-100mg/次，每日2次',
    contraindications: ['严重心动过缓', '心源性休克', '哮喘', '严重外周血管疾病'],
    side_effects: ['心动过缓', '疲劳', '阳痿', '血脂影响'],
    manufacturer: '多家'
});

// 其他常用药物
CREATE (drug12: Drug {
    name: '阿司匹林',
    generic_name: '阿司匹林肠溶片',
    category: '抗血小板药',
    indications: ['心脑血管疾病二级预防', '心绞痛', '脑卒中', '心肌梗死'],
    dosage: '75-100mg/日，每日1次',
    contraindications: ['活动性出血', '严重肝肾功能不全', '哮喘', '妊娠最后3个月'],
    side_effects: ['胃肠道出血', '过敏反应', '出血倾向'],
    manufacturer: '拜耳'
});

CREATE (drug13: Drug {
    name: '瑞舒伐他汀',
    generic_name: '瑞舒伐他汀钙片',
    category: '他汀类',
    indications: ['高胆固醇血症', '冠心病', '脑卒中预防'],
    dosage: '5-20mg/日，每日1次',
    contraindications: ['活动性肝病', '严重肾功能不全', '妊娠哺乳'],
    side_effects: ['肌肉疼痛', '肝功能异常', '血糖升高', '消化道症状'],
    manufacturer: '阿斯利康'
});

// 药物与疾病的治疗关系
CREATE (drug1)-[:TREATS {first_line: true}]->(d)
CREATE (drug2)-[:TREATS {first_line: true}]->(d)
CREATE (drug3)-[:TREATS {first_line: false}]->(d)
CREATE (drug4)-[:TREATS {first_line: true}]->(d)
CREATE (drug5)-[:TREATS {first_line: false}]->(d)
CREATE (drug6)-[:TREATS {first_line: false}]->(d)

CREATE (drug7)-[:TREATS {first_line: true}]->(h)
CREATE (drug8)-[:TREATS {first_line: true}]->(h)
CREATE (drug9)-[:TREATS {first_line: true}]->(h)
CREATE (drug10)-[:TREATS {first_line: true}]->(h)
CREATE (drug11)-[:TREATS {first_line: false}]->(h)

CREATE (drug12)-[:TREATS]->(c5)
CREATE (drug12)-[:TREATS]->(hc2)
CREATE (drug13)-[:TREATS]->(c5)
CREATE (drug13)-[:TREATS]->(hc2)

// 糖尿病肾病的治疗
CREATE (drug8)-[:TREATS]->(c2)
CREATE (drug9)-[:TREATS]->(c2)
CREATE (drug6)-[:TREATS]->(c2)

// =====================================================
// 第四部分: 药物相互作用
// =====================================================

// 高风险相互作用 (level: high)
CREATE (drug12)-[:INTERACTS_WITH {
    level: 'high',
    description: '阿司匹林增强华法林的抗凝作用，增加出血风险',
    clinical_significance: '需避免合用或密切监测INR',
    management: '避免合用，或使用其他抗血小板药物'
}]->(dw: Drug {name: '华法林'});

CREATE (drug1)-[:INTERACTS_WITH {
    level: 'high',
    description: '饮酒可能增加乳酸酸中毒风险',
    clinical_significance: '糖尿病患者应限制饮酒',
    management: '用药期间避免饮酒'
}]->(alc: Drug {name: '酒精'});

CREATE (drug4)-[:INTERACTS_WITH {
    level: 'high',
    description: 'β受体阻滞剂可能掩盖低血糖症状',
    clinical_significance: '合用时需更密切监测血糖',
    management: '密切监测血糖，注意低血糖症状'
}]->(drug11);

// 中风险相互作用 (level: moderate)
CREATE (drug1)-[:INTERACTS_WITH {
    level: 'moderate',
    description: '二甲双胍可能增强磺脲类药物的降糖作用',
    clinical_significance: '合用时需调整剂量',
    management: '密切监测血糖，调整药物剂量'
}]->(drug2);

CREATE (drug7)-[:INTERACTS_WITH {
    level: 'moderate',
    description: '氨氯地平与非甾体抗炎药合用可能增加肾损害风险',
    clinical_significance: '肾功能不全患者需谨慎',
    management: '监测肾功能'
}]->(nsaid: Drug {name: '布洛芬'});

CREATE (drug8)-[:INTERACTS_WITH {
    level: 'moderate',
    description: '厄贝沙坦与保钾利尿剂合用可能增加高钾血症风险',
    clinical_significance: '需监测血钾',
    management: '监测血钾，避免补钾'
}]->(sp: Drug {name: '螺内酯'});

CREATE (drug9)-[:INTERACTS_WITH {
    level: 'moderate',
    description: '培哚普利与钾剂合用可能引起高钾血症',
    clinical_significance: '需监测血钾',
    management: '避免合用或监测血钾'
}]->(k: Drug {name: '氯化钾'});

// 低风险相互作用 (level: low)
CREATE (drug1)-[:INTERACTS_WITH {
    level: 'low',
    description: '二甲双胍与ACEI类药物可能协同改善血糖',
    clinical_significance: '可能是有益的相互作用',
    management: '可合用'
}]->(drug9);

CREATE (drug6)-[:INTERACTS_WITH {
    level: 'low',
    description: '达格列净与利尿剂合用可能增强降压效果',
    clinical_significance: '注意血压监测',
    management: '监测血压，调整剂量'
}]->(drug10);

// 药物与食物相互作用
CREATE (drug3)-[:INTERACTS_WITH {
    level: 'moderate',
    description: '阿卡波糖与碳水化合物合用效果最佳',
    clinical_significance: '需与主食同服',
    management: '餐前立即服用'
}]->(food: Drug {name: '米饭'});

CREATE (drug3)-[:INTERACTS_WITH {
    level: 'low',
    description: '阿卡波糖可能增加蔗糖吸收，引起腹泻',
    clinical_significance: '避免大量蔗糖摄入',
    management: '避免高蔗糖饮食'
}]->(sugar: Drug {name: '蔗糖'});

// =====================================================
// 第五部分: 食物实体 (部分示例)
// =====================================================

// 低GI食物
CREATE (f1: Food {
    name: '糙米饭',
    category: '主食',
    gi: 68,
    carbs_per_100g: 23.5,
    calories: 152,
    serving_size: 150,
    description: '糙米富含膳食纤维，GI值低于白米饭',
    recommendation: '适合糖尿病患者作为主食'
});

CREATE (f2: Food {
    name: '燕麦片',
    category: '主食',
    gi: 55,
    carbs_per_100g: 12.0,
    calories: 150,
    serving_size: 40,
    description: '富含β-葡聚糖，有助于控制血糖',
    recommendation: '适合糖尿病患者早餐'
});

CREATE (f3: Food {
    name: '全麦面包',
    category: '主食',
    gi: 50,
    carbs_per_100g: 41.0,
    calories: 81,
    serving_size: 30,
    description: '全麦制作，富含膳食纤维',
    recommendation: '适合糖尿病患者'
});

CREATE (f4: Food {
    name: '荞麦面',
    category: '主食',
    gi: 59,
    carbs_per_100g: 25.0,
    calories: 172,
    serving_size: 150,
    description: '荞麦富含黄酮类物质，有助于血糖控制',
    recommendation: '适合糖尿病患者'
});

// 中GI食物
CREATE (f5: Food {
    name: '白米饭',
    category: '主食',
    gi: 73,
    carbs_per_100g: 28.2,
    calories: 174,
    serving_size: 150,
    description: '主要主食，碳水化合物含量高',
    recommendation: '糖尿病患者需控制摄入量'
});

CREATE (f6: Food {
    name: '馒头',
    category: '主食',
    gi: 85,
    carbs_per_100g: 47.0,
    calories: 223,
    serving_size: 100,
    description: '精制面粉制作，GI值较高',
    recommendation: '糖尿病患者需谨慎食用'
});

// 高GI食物
CREATE (f7: Food {
    name: '土豆',
    category: '蔬菜',
    gi: 62,
    carbs_per_100g: 17.0,
    calories: 77,
    serving_size: 100,
    description: '淀粉含量高，作为蔬菜需控制量',
    recommendation: '糖尿病患者当主食适量食用'
});

CREATE (f8: Food {
    name: '西瓜',
    category: '水果',
    gi: 76,
    carbs_per_100g: 6.0,
    calories: 30,
    serving_size: 200,
    description: 'GI值高但GL低，适量食用可',
    recommendation: '糖尿病患者需控制量，每次<200g'
});

// 低GI水果
CREATE (f9: Food {
    name: '苹果',
    category: '水果',
    gi: 36,
    carbs_per_100g: 14.0,
    calories: 52,
    serving_size: 200,
    description: '富含果胶，有助于血糖控制',
    recommendation: '适合糖尿病患者，每日1个'
});

CREATE (f10: Food {
    name: '梨',
    category: '水果',
    gi: 38,
    carbs_per_100g: 13.0,
    calories: 50,
    serving_size: 200,
    description: '富含膳食纤维',
    recommendation: '适合糖尿病患者'
});

CREATE (f11: Food {
    name: '草莓',
    category: '水果',
    gi: 40,
    carbs_per_100g: 8.0,
    calories: 32,
    serving_size: 150,
    description: '低糖水果，富含维生素C',
    recommendation: '适合糖尿病患者'
});

CREATE (f12: Food {
    name: '蓝莓',
    category: '水果',
    gi: 53,
    carbs_per_100g: 14.0,
    calories: 57,
    serving_size: 100,
    description: '富含花青素，有助于改善胰岛素敏感性',
    recommendation: '适合糖尿病患者'
});

// 绿叶蔬菜（GI极低）
CREATE (f13: Food {
    name: '菠菜',
    category: '蔬菜',
    gi: 15,
    carbs_per_100g: 2.0,
    calories: 14,
    serving_size: 100,
    description: '富含铁、维生素K、叶酸',
    recommendation: '适合糖尿病患者，多吃有益'
});

CREATE (f14: Food {
    name: '西兰花',
    category: '蔬菜',
    gi: 15,
    carbs_per_100g: 3.0,
    calories: 24,
    serving_size: 100,
    description: '富含膳食纤维和维生素C',
    recommendation: '适合糖尿病患者'
});

CREATE (f15: Food {
    name: '番茄',
    category: '蔬菜',
    gi: 15,
    carbs_per_100g: 3.0,
    calories: 15,
    serving_size: 100,
    description: '低GI，富含番茄红素',
    recommendation: '适合糖尿病患者'
});

// 蛋白质食物
CREATE (f16: Food {
    name: '鸡胸肉',
    category: '肉类',
    gi: 0,
    carbs_per_100g: 0,
    calories: 165,
    serving_size: 100,
    description: '低脂高蛋白',
    recommendation: '适合糖尿病患者'
});

CREATE (f17: Food {
    name: '三文鱼',
    category: '鱼类',
    gi: 0,
    carbs_per_100g: 0,
    calories: 208,
    serving_size: 100,
    description: '富含Omega-3脂肪酸',
    recommendation: '适合糖尿病患者，有心血管保护作用'
});

CREATE (f18: Food {
    name: '鸡蛋',
    category: '蛋类',
    gi: 0,
    carbs_per_100g: 1.0,
    calories: 155,
    serving_size: 50,
    description: '优质蛋白质来源',
    recommendation: '适合糖尿病患者，每天1个'
});

CREATE (f19: Food {
    name: '牛奶',
    category: '奶类',
    gi: 27,
    carbs_per_100g: 5.0,
    calories: 54,
    serving_size: 250,
    description: '富含钙和蛋白质',
    recommendation: '适合糖尿病患者，建议选低脂牛奶'
});

CREATE (f20: Food {
    name: '豆腐',
    category: '豆类',
    gi: 15,
    carbs_per_100g: 2.0,
    calories: 76,
    serving_size: 100,
    description: '优质植物蛋白',
    recommendation: '适合糖尿病患者'
});

// 食物与GI的关系
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f1)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f2)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f3)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f9)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f10)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f11)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f13)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f14)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f15)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f16)
CREATE (d)-[:RECOMMEND {preference: 'positive'}]->(f17)
CREATE (d)-[:RECOMMEND {preference: 'negative'}]->(f5)
CREATE (d)-[:RECOMMEND {preference: 'negative'}]->(f6)
CREATE (d)-[:RECOMMEND {preference: 'negative'}]->(f7)
CREATE (d)-[:RECOMMEND {preference: 'negative'}]->(f8)

// 高血压推荐食物
CREATE (h)-[:RECOMMEND {preference: 'positive'}]->(f13)  // 菠菜
CREATE (h)-[:RECOMMEND {preference: 'positive'}]->(f14)  // 西兰花
CREATE (h)-[:RECOMMEND {preference: 'positive'}]->(f15)  // 番茄
CREATE (h)-[:RECOMMEND {preference: 'positive'}]->(f17)  // 三文鱼

// 食物类别
CREATE (cat1: FoodCategory {name: '主食', description: '米面类主食'})
CREATE (cat2: FoodCategory {name: '蔬菜', description: '各类蔬菜'})
CREATE (cat3: FoodCategory {name: '水果', description: '各类水果'})
CREATE (cat4: FoodCategory {name: '肉类', description: '禽肉、畜肉'})
CREATE (cat5: FoodCategory {name: '鱼类', description: '各类鱼虾'})
CREATE (cat6: FoodCategory {name: '蛋类', description: '鸡蛋、鸭蛋等'})
CREATE (cat7: FoodCategory {name: '奶类', description: '牛奶、酸奶等'})
CREATE (cat8: FoodCategory {name: '豆类', description: '大豆及豆制品'})

CREATE (f1)-[:BELONGS_TO]->(cat1)
CREATE (f2)-[:BELONGS_TO]->(cat1)
CREATE (f3)-[:BELONGS_TO]->(cat1)
CREATE (f4)-[:BELONGS_TO]->(cat1)
CREATE (f5)-[:BELONGS_TO]->(cat1)
CREATE (f6)-[:BELONGS_TO]->(cat1)

CREATE (f7)-[:BELONGS_TO]->(cat2)
CREATE (f13)-[:BELONGS_TO]->(cat2)
CREATE (f14)-[:BELONGS_TO]->(cat2)
CREATE (f15)-[:BELONGS_TO]->(cat2)

CREATE (f8)-[:BELONGS_TO]->(cat3)
CREATE (f9)-[:BELONGS_TO]->(cat3)
CREATE (f10)-[:BELONGS_TO]->(cat3)
CREATE (f11)-[:BELONGS_TO]->(cat3)
CREATE (f12)-[:BELONGS_TO]->(cat3)

CREATE (f16)-[:BELONGS_TO]->(cat4)
CREATE (f17)-[:BELONGS_TO]->(cat5)
CREATE (f18)-[:BELONGS_TO]->(cat6)
CREATE (f19)-[:BELONGS_TO]->(cat7)
CREATE (f20)-[:BELONGS_TO]->(cat8)

// =====================================================
// 第六部分: 运动处方
// =====================================================

CREATE (ex1: Exercise {
    name: '快走',
    category: '有氧运动',
    intensity: '中等',
    duration: '30-60分钟',
    frequency: '每周5-7次',
    calories_per_hour: 280,
    indications: ['糖尿病', '高血压', '肥胖', '心脑血管疾病预防'],
    contraindications: ['严重心肺疾病', '急性感染', '糖尿病足'],
    recommendations: '维持心率在最大心率的50-70%'
});

CREATE (ex2: Exercise {
    name: '游泳',
    category: '有氧运动',
    intensity: '中等',
    duration: '30-45分钟',
    frequency: '每周3-5次',
    calories_per_hour: 350,
    indications: ['糖尿病', '高血压', '关节疾病', '肥胖'],
    contraindications: ['严重心脏病', '皮肤感染', '中耳炎'],
    recommendations: '水温适宜，避免空腹或饱餐后'
});

CREATE (ex3: Exercise {
    name: '骑自行车',
    category: '有氧运动',
    intensity: '中等',
    duration: '30-60分钟',
    frequency: '每周3-5次',
    calories_per_hour: 250,
    indications: ['糖尿病', '高血压', '肥胖', '膝关节疾病'],
    contraindications: ['严重心脏病', '高血压未控制'],
    recommendations: '选择合适自行车，注意安全'
});

CREATE (ex4: Exercise {
    name: '太极拳',
    category: '传统运动',
    intensity: '低-中等',
    duration: '30-60分钟',
    frequency: '每周3-5次',
    calories_per_hour: 180,
    indications: ['糖尿病', '高血压', '心脑血管疾病', '焦虑抑郁'],
    contraindications: ['急性心肌梗死', '严重心衰'],
    recommendations: '适合老年患者'
});

CREATE (ex5: Exercise {
    name: '力量训练',
    category: '抗阻运动',
    intensity: '中等',
    duration: '20-30分钟',
    frequency: '每周2-3次',
    calories_per_hour: 200,
    indications: ['糖尿病', '骨质疏松', '肌肉减少症'],
    contraindications: ['严重高血压', '视网膜病变', '心衰'],
    recommendations: '避免剧烈用力，监测血压'
});

// 运动与疾病的关系
CREATE (ex1)-[:TREATS]->(d)
CREATE (ex1)-[:TREATS]->(h)
CREATE (ex2)-[:TREATS]->(d)
CREATE (ex2)-[:TREATS]->(h)
CREATE (ex3)-[:TREATS]->(d)
CREATE (ex3)-[:TREATS]->(h)
CREATE (ex4)-[:TREATS]->(d)
CREATE (ex4)-[:TREATS]->(h)
CREATE (ex5)-[:TREATS]->(d)

// =====================================================
// 第七部分: 糖尿病食谱推荐
// =====================================================

CREATE (meal1: Meal {
    name: '糖尿病早餐推荐',
    type: '早餐',
    calories: 400,
    carbs: 50,
    description: '适合糖尿病患者的营养早餐',
    foods: ['全麦面包2片', '鸡蛋1个', '牛奶250ml', '黄瓜100g']
});

CREATE (meal2: Meal {
    name: '糖尿病午餐推荐',
    type: '午餐',
    calories: 600,
    carbs: 60,
    description: '适合糖尿病患者的均衡午餐',
    foods: ['糙米饭150g', '清蒸鸡胸肉100g', '西兰花200g', '番茄汤']
});

CREATE (meal3: Meal {
    name: '糖尿病晚餐推荐',
    type: '晚餐',
    calories: 500,
    carbs: 50,
    description: '适合糖尿病患者的清淡晚餐',
    foods: ['荞麦面100g', '三文鱼100g', '菠菜200g', '苹果1个']
});

CREATE (meal1)-[:RECOMMEND {preference: 'positive'}]->(d)
CREATE (meal2)-[:RECOMMEND {preference: 'positive'}]->(d)
CREATE (meal3)-[:RECOMMEND {preference: 'positive'}]->(d)

// =====================================================
// 提交事务
// =====================================================

COMMIT;
