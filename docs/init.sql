-- =====================================================
-- 康伴(WellHealth) 慢病管理平台 - 数据库初始化脚本
-- 数据库: MySQL 8.0+
-- 作者: WellHealth Team
-- 描述: 包含所有表结构定义和初始化数据
-- =====================================================

-- -----------------------------------------------------
-- 创建数据库
-- -----------------------------------------------------
CREATE DATABASE IF NOT EXISTS wellhealth 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE wellhealth;

-- 禁用外键检查（允许删除有关联数据的表）
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------
-- 1. 用户表
-- -----------------------------------------------------
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(50) COMMENT '真实姓名',
    role ENUM('patient', 'doctor', 'nurse', 'admin') DEFAULT 'patient' COMMENT '角色',
    phone VARCHAR(20) COMMENT '手机号',
    email VARCHAR(100) COMMENT '邮箱',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login_at DATETIME COMMENT '最后登录时间',
    INDEX idx_username (username),
    INDEX idx_phone (phone),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- -----------------------------------------------------
-- 2. 患者表
-- -----------------------------------------------------
DROP TABLE IF EXISTS patients;
CREATE TABLE patients (
    id VARCHAR(36) PRIMARY KEY COMMENT '患者ID',
    user_id VARCHAR(36) COMMENT '关联用户ID',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    age INT COMMENT '年龄',
    gender ENUM('male', 'female', 'other') COMMENT '性别',
    phone VARCHAR(20) COMMENT '电话',
    id_card VARCHAR(18) COMMENT '身份证号',
    address VARCHAR(255) COMMENT '地址',
    emergency_contact VARCHAR(50) COMMENT '紧急联系人',
    emergency_phone VARCHAR(20) COMMENT '紧急联系电话',
    blood_type ENUM('A', 'B', 'AB', 'O', 'unknown') DEFAULT 'unknown' COMMENT '血型',
    height DECIMAL(5,2) COMMENT '身高(cm)',
    weight DECIMAL(5,1) COMMENT '体重(kg)',
    allergies TEXT COMMENT '过敏史(JSON数组)',
    family_history TEXT COMMENT '家族史(JSON数组)',
    lifestyle TEXT COMMENT '生活习惯(JSON对象)',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_id_card (id_card),
    INDEX idx_phone (phone),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者表';

-- -----------------------------------------------------
-- 3. 医生表
-- -----------------------------------------------------
DROP TABLE IF EXISTS doctors;
CREATE TABLE doctors (
    id VARCHAR(36) PRIMARY KEY COMMENT '医生ID',
    user_id VARCHAR(36) COMMENT '关联用户ID',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    title VARCHAR(50) COMMENT '职称',
    department VARCHAR(50) COMMENT '科室',
    hospital VARCHAR(100) COMMENT '医院',
    specialty VARCHAR(255) COMMENT '专长',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    bio TEXT COMMENT '简介',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_department (department),
    INDEX idx_hospital (hospital)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医生表';

-- -----------------------------------------------------
-- 4. 疾病记录表
-- -----------------------------------------------------
DROP TABLE IF EXISTS disease_records;
CREATE TABLE disease_records (
    id VARCHAR(36) PRIMARY KEY COMMENT '疾病记录ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    disease_name VARCHAR(100) NOT NULL COMMENT '疾病名称',
    disease_type ENUM('acute', 'chronic', 'other') DEFAULT 'chronic' COMMENT '疾病类型',
    icd_code VARCHAR(20) COMMENT 'ICD编码',
    diagnosed_date DATE COMMENT '确诊日期',
    status ENUM('active', 'recovered', 'controlled') DEFAULT 'active' COMMENT '状态',
    severity ENUM('mild', 'moderate', 'severe') DEFAULT 'moderate' COMMENT '严重程度',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_disease_name (disease_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病记录表';

-- -----------------------------------------------------
-- 5. 用药记录表
-- -----------------------------------------------------
DROP TABLE IF EXISTS medication_records;
CREATE TABLE medication_records (
    id VARCHAR(36) PRIMARY KEY COMMENT '用药记录ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    drug_name VARCHAR(100) NOT NULL COMMENT '药品名称',
    specification VARCHAR(100) COMMENT '规格',
    dosage VARCHAR(50) COMMENT '剂量',
    frequency VARCHAR(50) COMMENT '频次',
    route VARCHAR(50) COMMENT '给药途径',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    prescribing_doctor VARCHAR(50) COMMENT '开药医生',
    hospital VARCHAR(100) COMMENT '开药医院',
    prescription_no VARCHAR(50) COMMENT '处方号',
    status ENUM('active', 'stopped', 'completed') DEFAULT 'active' COMMENT '状态',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_drug_name (drug_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药记录表';

-- -----------------------------------------------------
-- 6. 体征记录表
-- -----------------------------------------------------
DROP TABLE IF EXISTS vital_records;
CREATE TABLE vital_records (
    id VARCHAR(36) PRIMARY KEY COMMENT '体征记录ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    vital_type VARCHAR(50) NOT NULL COMMENT '体征类型',
    value DECIMAL(10,2) NOT NULL COMMENT '数值',
    unit VARCHAR(20) COMMENT '单位',
    reference_min DECIMAL(10,2) COMMENT '参考最小值',
    reference_max DECIMAL(10,2) COMMENT '参考最大值',
    status ENUM('normal', 'low', 'high', 'critical') DEFAULT 'normal' COMMENT '状态',
    recorded_at DATETIME NOT NULL COMMENT '记录时间',
    source ENUM('manual', 'device', 'import') DEFAULT 'manual' COMMENT '数据来源',
    device_id VARCHAR(50) COMMENT '设备ID',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_vital_type (vital_type),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体征记录表';

-- -----------------------------------------------------
-- 7. 用药提醒表
-- -----------------------------------------------------
DROP TABLE IF EXISTS medication_reminders;
CREATE TABLE medication_reminders (
    id VARCHAR(36) PRIMARY KEY COMMENT '提醒ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    drug_name VARCHAR(100) NOT NULL COMMENT '药品名称',
    dosage VARCHAR(50) COMMENT '剂量',
    frequency VARCHAR(50) COMMENT '频次',
    times JSON NOT NULL COMMENT '服药时间点(JSON数组)',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    reminder_enabled TINYINT(1) DEFAULT 1 COMMENT '是否开启提醒',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药提醒表';

-- -----------------------------------------------------
-- 8. 服药记录表
-- -----------------------------------------------------
DROP TABLE IF EXISTS medication_logs;
CREATE TABLE medication_logs (
    id VARCHAR(36) PRIMARY KEY COMMENT '服药记录ID',
    reminder_id VARCHAR(36) NOT NULL COMMENT '提醒ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    scheduled_time DATETIME NOT NULL COMMENT '计划服药时间',
    taken_time DATETIME COMMENT '实际服药时间',
    status ENUM('pending', 'taken', 'missed', 'skipped') DEFAULT 'pending' COMMENT '状态',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (reminder_id) REFERENCES medication_reminders(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_reminder_id (reminder_id),
    INDEX idx_patient_id (patient_id),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='服药记录表';

-- -----------------------------------------------------
-- 9. 体检报告表
-- -----------------------------------------------------
DROP TABLE IF EXISTS reports;
CREATE TABLE reports (
    id VARCHAR(36) PRIMARY KEY COMMENT '报告ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    title VARCHAR(100) NOT NULL COMMENT '报告标题',
    report_type ENUM('annual', 'special', 'followup', 'manual') DEFAULT 'annual' COMMENT '报告类型',
    hospital VARCHAR(100) COMMENT '体检医院',
    exam_date DATE NOT NULL COMMENT '体检日期',
    file_url VARCHAR(500) COMMENT '文件URL',
    status ENUM('pending', 'analyzed', 'archived') DEFAULT 'pending' COMMENT '状态',
    ai_analysis TEXT COMMENT 'AI分析结果',
    ai_recommendations TEXT COMMENT 'AI建议(JSON数组)',
    risk_alerts TEXT COMMENT '风险提示(JSON数组)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    analyzed_at DATETIME COMMENT '分析时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_exam_date (exam_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体检报告表';

-- -----------------------------------------------------
-- 10. 体检项目明细表
-- -----------------------------------------------------
DROP TABLE IF EXISTS report_items;
CREATE TABLE report_items (
    id VARCHAR(36) PRIMARY KEY COMMENT '项目ID',
    report_id VARCHAR(36) NOT NULL COMMENT '报告ID',
    item_name VARCHAR(100) NOT NULL COMMENT '项目名称',
    value DECIMAL(10,2) COMMENT '数值',
    unit VARCHAR(20) COMMENT '单位',
    reference_min DECIMAL(10,2) COMMENT '参考最小值',
    reference_max DECIMAL(10,2) COMMENT '参考最大值',
    status ENUM('normal', 'low', 'high', 'critical') DEFAULT 'normal' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    INDEX idx_report_id (report_id),
    INDEX idx_item_name (item_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体检项目明细表';

-- -----------------------------------------------------
-- 11. 处方表
-- -----------------------------------------------------
DROP TABLE IF EXISTS prescriptions;
CREATE TABLE prescriptions (
    id VARCHAR(36) PRIMARY KEY COMMENT '处方ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    prescription_no VARCHAR(50) NOT NULL COMMENT '处方号',
    hospital VARCHAR(100) NOT NULL COMMENT '医院',
    department VARCHAR(50) COMMENT '科室',
    doctor VARCHAR(50) COMMENT '医生',
    prescription_date DATE NOT NULL COMMENT '开方日期',
    valid_until DATE COMMENT '有效期至',
    prescription_type ENUM('western', 'chinese', 'mixed') DEFAULT 'western' COMMENT '处方类型',
    diagnosis TEXT COMMENT '诊断',
    diagnosis_code VARCHAR(20) COMMENT '诊断编码',
    total_amount DECIMAL(10,2) COMMENT '处方金额',
    status ENUM('valid', 'expired', 'used', 'cancelled') DEFAULT 'valid' COMMENT '状态',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_prescription_no (prescription_no),
    INDEX idx_hospital (hospital),
    INDEX idx_prescription_date (prescription_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='处方表';

-- -----------------------------------------------------
-- 12. 处方药品明细表
-- -----------------------------------------------------
DROP TABLE IF EXISTS prescription_items;
CREATE TABLE prescription_items (
    id VARCHAR(36) PRIMARY KEY COMMENT '明细ID',
    prescription_id VARCHAR(36) NOT NULL COMMENT '处方ID',
    drug_name VARCHAR(100) NOT NULL COMMENT '药品名称',
    specification VARCHAR(100) COMMENT '规格',
    quantity DECIMAL(10,2) COMMENT '数量',
    unit VARCHAR(20) COMMENT '单位',
    dosage VARCHAR(50) COMMENT '剂量',
    `usage` VARCHAR(255) COMMENT '用法',
    price DECIMAL(10,2) COMMENT '单价',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE,
    INDEX idx_prescription_id (prescription_id),
    INDEX idx_drug_name (drug_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='处方药品明细表';

-- -----------------------------------------------------
-- 13. 购药记录表
-- -----------------------------------------------------
DROP TABLE IF EXISTS medication_purchases;
CREATE TABLE medication_purchases (
    id VARCHAR(36) PRIMARY KEY COMMENT '购药记录ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    pharmacy VARCHAR(100) NOT NULL COMMENT '药店',
    pharmacy_address VARCHAR(255) COMMENT '药店地址',
    drug_name VARCHAR(100) NOT NULL COMMENT '药品名称',
    drug_specification VARCHAR(100) COMMENT '规格',
    manufacturer VARCHAR(100) COMMENT '生产厂家',
    quantity INT NOT NULL COMMENT '数量',
    unit_price DECIMAL(10,2) NOT NULL COMMENT '单价',
    total_amount DECIMAL(10,2) NOT NULL COMMENT '总金额',
    purchase_date DATE NOT NULL COMMENT '购药日期',
    prescription_no VARCHAR(50) COMMENT '处方号',
    payment_method VARCHAR(50) COMMENT '支付方式',
    invoice_no VARCHAR(50) COMMENT '发票号',
    pharmacist VARCHAR(50) COMMENT '药师',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id),
    INDEX idx_pharmacy (pharmacy),
    INDEX idx_drug_name (drug_name),
    INDEX idx_purchase_date (purchase_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='购药记录表';

-- -----------------------------------------------------
-- 14. AI Agent表
-- -----------------------------------------------------
DROP TABLE IF EXISTS agents;
CREATE TABLE agents (
    id VARCHAR(36) PRIMARY KEY COMMENT 'Agent ID',
    name VARCHAR(100) NOT NULL COMMENT 'Agent名称',
    type VARCHAR(50) NOT NULL COMMENT 'Agent类型',
    description TEXT COMMENT '描述',
    system_prompt TEXT COMMENT '系统提示词',
    version VARCHAR(20) DEFAULT '1.0.0' COMMENT '版本',
    status ENUM('active', 'inactive', 'testing') DEFAULT 'inactive' COMMENT '状态',
    capabilities JSON COMMENT '能力列表',
    parameters JSON COMMENT '参数配置',
    metrics JSON COMMENT '性能指标',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_type (type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent表';

-- -----------------------------------------------------
-- 15. 对话会话表
-- -----------------------------------------------------
DROP TABLE IF EXISTS chat_sessions;
CREATE TABLE chat_sessions (
    id VARCHAR(36) PRIMARY KEY COMMENT '会话ID',
    patient_id VARCHAR(36) COMMENT '患者ID',
    agent_type VARCHAR(50) COMMENT 'Agent类型',
    title VARCHAR(100) COMMENT '会话标题',
    status ENUM('active', 'closed') DEFAULT 'active' COMMENT '状态',
    message_count INT DEFAULT 0 COMMENT '消息数',
    duration INT DEFAULT 0 COMMENT '持续时间(秒)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    closed_at DATETIME COMMENT '关闭时间',
    INDEX idx_patient_id (patient_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表';

-- -----------------------------------------------------
-- 16. 对话消息表
-- -----------------------------------------------------
DROP TABLE IF EXISTS chat_messages;
CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY COMMENT '消息ID',
    session_id VARCHAR(36) NOT NULL COMMENT '会话ID',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
    content TEXT NOT NULL COMMENT '内容',
    agent_type VARCHAR(50) COMMENT 'Agent类型',
    sources JSON COMMENT '引用来源',
    safety_level VARCHAR(20) COMMENT '安全等级',
    metadata JSON COMMENT '元数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话消息表';

-- -----------------------------------------------------
-- 17. 评估记录表
-- -----------------------------------------------------
DROP TABLE IF EXISTS evaluations;
CREATE TABLE evaluations (
    id VARCHAR(36) PRIMARY KEY COMMENT '评估ID',
    agent_type VARCHAR(50) NOT NULL COMMENT 'Agent类型',
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending' COMMENT '状态',
    total_cases INT DEFAULT 0 COMMENT '总用例数',
    passed_cases INT DEFAULT 0 COMMENT '通过数',
    failed_cases INT DEFAULT 0 COMMENT '失败数',
    pass_rate DECIMAL(5,4) COMMENT '通过率',
    avg_response_time DECIMAL(10,2) COMMENT '平均响应时间',
    results JSON COMMENT '详细结果',
    issues JSON COMMENT '问题列表',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at DATETIME COMMENT '完成时间',
    INDEX idx_agent_type (agent_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评估记录表';

-- -----------------------------------------------------
-- 18. 知识库表
-- -----------------------------------------------------
DROP TABLE IF EXISTS knowledge_base;
CREATE TABLE knowledge_base (
    id VARCHAR(36) PRIMARY KEY COMMENT '知识ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    type ENUM('disease', 'drug', 'food', 'exercise', 'guideline', 'nursing', 'other') DEFAULT 'other' COMMENT '类型',
    tags JSON COMMENT '标签列表',
    source VARCHAR(200) COMMENT '来源',
    author VARCHAR(50) COMMENT '作者',
    embedding TEXT COMMENT '向量嵌入(JSON格式)',
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft' COMMENT '状态',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    helpful_count INT DEFAULT 0 COMMENT '点赞次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    published_at DATETIME COMMENT '发布时间',
    INDEX idx_type (type),
    INDEX idx_status (status),
    FULLTEXT INDEX ft_title_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

-- -----------------------------------------------------
-- 19. 干预方案表
-- -----------------------------------------------------
DROP TABLE IF EXISTS interventions;
CREATE TABLE interventions (
    id VARCHAR(36) PRIMARY KEY COMMENT '方案ID',
    name VARCHAR(100) NOT NULL COMMENT '方案名称',
    type VARCHAR(50) NOT NULL COMMENT '方案类型',
    target_disease VARCHAR(100) COMMENT '目标疾病',
    description TEXT COMMENT '描述',
    duration_days INT COMMENT '持续天数',
    effectiveness DECIMAL(5,2) COMMENT '有效率(%)',
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'low' COMMENT '风险等级',
    contraindications TEXT COMMENT '禁忌症',
    precautions TEXT COMMENT '注意事项',
    parameters JSON COMMENT '参数配置',
    evidence TEXT COMMENT '证据来源',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_type (type),
    INDEX idx_target_disease (target_disease),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='干预方案表';

-- -----------------------------------------------------
-- 20. 系统配置表
-- -----------------------------------------------------
DROP TABLE IF EXISTS system_config;
CREATE TABLE system_config (
    id VARCHAR(36) PRIMARY KEY COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(50) DEFAULT 'string' COMMENT '配置类型',
    description VARCHAR(255) COMMENT '描述',
    is_public TINYINT(1) DEFAULT 0 COMMENT '是否公开',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';


-- =====================================================
-- 初始化数据
-- =====================================================

-- 插入管理员用户
INSERT INTO users (id, username, password_hash, real_name, role, status) VALUES
('u001', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYGCpFdC0FUm', '系统管理员', 'admin', 'active');

-- 插入医生
INSERT INTO doctors (id, user_id, name, title, department, hospital, specialty, status) VALUES
('d001', NULL, '李主任', '主任医师', '内分泌科', '北京协和医院', '糖尿病、甲状腺疾病', 'active'),
('d002', NULL, '王主任', '主任医师', '心内科', '北京宣武医院', '高血压、冠心病', 'active'),
('d003', NULL, '赵主任', '副主任医师', '内分泌科', '北京同仁医院', '糖尿病、骨质疏松', 'active');

-- 插入患者
INSERT INTO patients (id, user_id, name, age, gender, phone, id_card, address, emergency_contact, emergency_phone, allergies, family_history, lifestyle, status) VALUES
('p001', NULL, '张三', 65, 'male', '13800138001', '110101196001011234', '北京市东城区和平里', '张妻', '13800138002', '["无"]', '["高血压家族史"]', '{"smoking": "无", "drinking": "偶尔", "exercise": "每周3次"}', 'active'),
('p002', NULL, '李四', 58, 'female', '13800138003', '110101196601011234', '北京市西城区', '李夫', '13800138004', '["青霉素"]', '["糖尿病家族史"]', '{"smoking": "无", "drinking": "从不", "exercise": "每周2次"}', 'active'),
('p003', NULL, '王五', 72, 'male', '13800138005', '110101195201011234', '北京市海淀区', '王某', '13800138006', '["无"]', '["冠心病家族史"]', '{"smoking": "已戒烟", "drinking": "偶尔", "exercise": "每周1次"}', 'active');

-- 插入疾病记录
INSERT INTO disease_records (id, patient_id, disease_name, disease_type, diagnosed_date, status, severity, notes) VALUES
('dr001', 'p001', '2型糖尿病', 'chronic', '2020-03-15', 'active', 'moderate', '血糖控制良好'),
('dr002', 'p001', '高血压2级', 'chronic', '2019-08-20', 'active', 'moderate', '间断服药'),
('dr003', 'p002', '2型糖尿病', 'chronic', '2021-05-10', 'active', 'mild', '新确诊'),
('dr004', 'p002', '高血脂', 'chronic', '2021-05-10', 'active', 'mild', '新确诊'),
('dr005', 'p003', '高血压3级', 'chronic', '2018-01-15', 'active', 'severe', '联合用药'),
('dr006', 'p003', '冠心病', 'chronic', '2020-06-20', 'active', 'moderate', '支架术后');

-- 插入用药记录
INSERT INTO medication_records (id, patient_id, drug_name, specification, dosage, frequency, route, start_date, prescribing_doctor, hospital, status) VALUES
('mr001', 'p001', '二甲双胍片', '0.5g*20片', '0.5g', '每日2次', '口服', '2020-03-15', '李主任', '北京协和医院', 'active'),
('mr002', 'p001', '厄贝沙坦片', '150mg*7片', '150mg', '每日1次', '口服', '2019-08-20', '王主任', '北京宣武医院', 'active'),
('mr003', 'p002', '阿卡波糖片', '50mg*30片', '50mg', '每日3次', '口服', '2021-05-10', '赵主任', '北京同仁医院', 'active'),
('mr004', 'p003', '苯磺酸氨氯地平片', '5mg*7片', '5mg', '每日1次', '口服', '2018-01-15', '王主任', '北京宣武医院', 'active'),
('mr005', 'p003', '阿托伐他汀钙片', '20mg*7片', '20mg', '每晚1次', '口服', '2020-06-20', '王主任', '北京宣武医院', 'active');

-- 插入体征记录
INSERT INTO vital_records (id, patient_id, vital_type, value, unit, reference_min, reference_max, status, recorded_at, source) VALUES
('vr001', 'p001', 'blood_sugar', 6.5, 'mmol/L', 3.9, 6.1, 'high', '2024-03-15 08:00:00', 'manual'),
('vr002', 'p001', 'blood_pressure_systolic', 135, 'mmHg', 90, 120, 'high', '2024-03-15 08:30:00', 'manual'),
('vr003', 'p001', 'blood_pressure_diastolic', 85, 'mmHg', 60, 80, 'high', '2024-03-15 08:30:00', 'manual'),
('vr004', 'p001', 'heart_rate', 72, 'bpm', 60, 100, 'normal', '2024-03-15 08:30:00', 'manual'),
('vr005', 'p002', 'blood_sugar', 7.2, 'mmol/L', 3.9, 6.1, 'high', '2024-03-14 08:00:00', 'manual'),
('vr006', 'p003', 'blood_pressure_systolic', 158, 'mmHg', 90, 120, 'high', '2024-03-15 09:00:00', 'manual'),
('vr007', 'p003', 'blood_pressure_diastolic', 95, 'mmHg', 60, 80, 'high', '2024-03-15 09:00:00', 'manual');

-- 插入用药提醒
INSERT INTO medication_reminders (id, patient_id, drug_name, dosage, frequency, times, start_date, enabled) VALUES
('mer001', 'p001', '二甲双胍片', '0.5g', '每日2次', '["08:00", "18:00"]', '2020-03-15', 1),
('mer002', 'p001', '厄贝沙坦片', '150mg', '每日1次', '["08:00"]', '2019-08-20', 1),
('mer003', 'p002', '阿卡波糖片', '50mg', '每日3次', '["07:30", "12:00", "18:00"]', '2021-05-10', 1),
('mer004', 'p003', '苯磺酸氨氯地平片', '5mg', '每日1次', '["07:00"]', '2018-01-15', 1);

-- 插入AI Agent
INSERT INTO agents (id, name, type, description, status, capabilities, version) VALUES
('agent_diabetes', '糖尿病专科助手', 'diabetes', '专注于糖尿病管理，提供血糖监测、用药指导、饮食建议', 'active', '["血糖咨询", "用药指导", "饮食建议", "并发症筛查"]', '1.0.0'),
('agent_hypertension', '高血压专科助手', 'hypertension', '专注于高血压管理，提供血压监测、生活方式干预、用药指导', 'active', '["血压咨询", "用药指导", "运动建议", "限盐指导"]', '1.0.0'),
('agent_nutrition', '营养师助手', 'nutrition', '提供个性化营养方案，GI/GL计算，饮食记录分析', 'active', '["营养咨询", "GI计算", "食谱推荐", "膳食分析"]', '1.0.0'),
('agent_coach', '运动康复师', 'coach', '制定个性化运动处方，跟踪运动数据，提供康复指导', 'active', '["运动处方", "康复指导", "运动监测", "体能评估"]', '1.0.0');

-- 插入干预方案
INSERT INTO interventions (id, name, type, target_disease, description, duration_days, effectiveness, risk_level) VALUES
('int001', '糖尿病饮食干预', 'diet', '2型糖尿病', '通过控制碳水化合物摄入量，采用低GI饮食方案', 90, 75.0, 'low'),
('int002', '高血压运动处方', 'exercise', '高血压', '有氧运动为主，每周150分钟中等强度运动', 180, 70.0, 'low'),
('int003', '糖尿病运动干预', 'exercise', '2型糖尿病', '快走、游泳等有氧运动结合抗阻训练', 180, 68.0, 'low'),
('int004', '限盐饮食干预', 'diet', '高血压', '每日钠摄入量控制在1500mg以下', 90, 65.0, 'low');

-- 插入系统配置
INSERT INTO system_config (id, config_key, config_value, config_type, description, is_public) VALUES
('cfg001', 'app_name', '康伴(WellHealth)', 'string', '应用名称', 1),
('cfg002', 'app_version', '1.0.0', 'string', '应用版本', 1),
('cfg003', 'system_maintenance', 'false', 'boolean', '系统维护模式', 1),
('cfg004', 'llm_provider', 'openai', 'string', 'LLM提供商', 0),
('cfg005', 'rag_top_k', '5', 'int', 'RAG检索返回数量', 0),
('cfg006', 'safety_check_enabled', 'true', 'boolean', '安全检查开关', 0);

-- 插入体检报告
INSERT INTO reports (id, patient_id, title, report_type, hospital, exam_date, status) VALUES
('rep001', 'p001', '年度体检报告', 'annual', '北京协和医院', '2024-03-15', 'analyzed'),
('rep002', 'p001', '糖尿病专项检查', 'special', '北京协和医院', '2024-01-20', 'analyzed'),
('rep003', 'p002', '年度体检报告', 'annual', '北京同仁医院', '2024-02-10', 'analyzed');

-- 插入报告项目
INSERT INTO report_items (id, report_id, item_name, value, unit, reference_min, reference_max, status) VALUES
('ri001', 'rep001', '空腹血糖', 6.8, 'mmol/L', 3.9, 6.1, 'high'),
('ri002', 'rep001', '糖化血红蛋白', 6.5, '%', 4.0, 6.0, 'high'),
('ri003', 'rep001', '总胆固醇', 5.8, 'mmol/L', 3.1, 5.7, 'high'),
('ri004', 'rep001', '甘油三酯', 1.9, 'mmol/L', 0.4, 1.7, 'high'),
('ri005', 'rep001', '收缩压', 135, 'mmHg', 90, 120, 'high'),
('ri006', 'rep001', '舒张压', 85, 'mmHg', 60, 80, 'high'),
('ri007', 'rep001', '体重指数', 26.5, 'BMI', 18.5, 24.0, 'high');

-- 插入处方
INSERT INTO prescriptions (id, patient_id, prescription_no, hospital, department, doctor, prescription_date, valid_until, prescription_type, diagnosis, total_amount, status) VALUES
('pre001', 'p001', 'P202403150001', '北京协和医院', '内分泌科', '李主任', '2024-03-15', '2024-04-15', 'western', '2型糖尿病', 156.80, 'valid'),
('pre002', 'p001', 'P202403200002', '北京协和医院', '心内科', '王主任', '2024-03-20', '2024-04-20', 'western', '高血压2级', 289.60, 'valid'),
('pre003', 'p002', 'P202402100003', '北京同仁医院', '内分泌科', '赵主任', '2024-02-10', '2024-03-10', 'western', '糖尿病视网膜病变', 168.00, 'expired');

-- 插入处方明细
INSERT INTO prescription_items (id, prescription_id, drug_name, specification, quantity, unit, dosage, `usage`, price) VALUES
('pi001', 'pre001', '二甲双胍片', '0.5g*20片', 2, '盒', '0.5g', '口服，每日2次，餐后服用', 28.50),
('pi002', 'pre001', '阿卡波糖片', '50mg*30片', 1, '盒', '50mg', '口服，每日3次，与第一口饭同服', 65.80),
('pi003', 'pre002', '厄贝沙坦片', '150mg*7片', 4, '盒', '150mg', '口服，每日1次', 32.40),
('pi004', 'pre002', '苯磺酸氨氯地平片', '5mg*7片', 4, '盒', '5mg', '口服，每日1次', 40.00);

-- 插入购药记录
INSERT INTO medication_purchases (id, patient_id, pharmacy, pharmacy_address, drug_name, drug_specification, manufacturer, quantity, unit_price, total_amount, purchase_date, prescription_no, payment_method, invoice_no, pharmacist) VALUES
('mp001', 'p001', '国大药房(北京旗舰店)', '北京市东城区和平里街道和平里东街18号', '二甲双胍片', '0.5g*20片/盒', '中美上海施贵宝制药有限公司', 2, 28.50, 57.00, '2024-03-16', 'P202403150001', '医保卡', 'INV20240316001', '王药师'),
('mp002', 'p001', '国大药房(北京旗舰店)', '北京市东城区和平里街道和平里东街18号', '阿卡波糖片', '50mg*30片/盒', '拜耳医药保健有限公司', 1, 65.80, 65.80, '2024-03-16', 'P202403150001', '医保卡', 'INV20240316002', '王药师'),
('mp003', 'p001', '华润医药连锁(和平里店)', '北京市东城区和平里西街1号', '厄贝沙坦片', '150mg*7片/盒', '赛诺菲(杭州)制药有限公司', 4, 32.40, 129.60, '2024-03-21', 'P202403200002', '医保卡', 'INV20240321001', '李药师');

-- 插入知识库数据 (40条)
INSERT INTO knowledge_base (id, title, content, type, tags, status) VALUES
-- 糖尿病相关 (1-15)
('kb001', '糖尿病饮食指南', '糖尿病患者应该控制碳水化合物摄入，选择低GI食物，如全谷物、蔬菜等。建议每天摄入碳水化合物占总热量的45-60%。', 'disease', '["糖尿病", "饮食", "血糖"]', 'published'),
('kb002', '血糖监测建议', '建议糖尿病患者每天监测空腹血糖，空腹血糖目标值为4.4-7.0 mmol/L。餐后2小时血糖应控制在10.0 mmol/L以下。', 'disease', '["糖尿病", "血糖监测"]', 'published'),
('kb003', '糖尿病并发症筛查', '糖尿病并发症筛查建议：眼底检查每年1次，尿蛋白/肌酐比每年1次，足部检查每半年1次，HbA1c每3个月1次。', 'disease', '["糖尿病", "并发症", "筛查"]', 'published'),
('kb004', '低血糖处理', '低血糖处理：当血糖<3.9 mmol/L时，轻度可口服葡萄糖15-20g，重度需静脉注射葡萄糖。常见症状：出汗、颤抖、心慌、饥饿感。', 'disease', '["糖尿病", "低血糖", "急救"]', 'published'),
('kb005', '糖尿病足护理', '糖尿病足护理：每天检查足部，保持清洁干燥，穿合适鞋子，避免赤脚走路，及时处理伤口。定期进行足部神经和血管检查。', 'nursing', '["糖尿病", "足部", "护理"]', 'published'),
('kb006', 'HbA1c控制目标', '糖化血红蛋白(HbA1c)控制目标：一般患者<7%，年轻、病程短、无并发症者可<6.5%，老年、并发症多者可<8%。', 'disease', '["糖尿病", "HbA1c", "控制目标"]', 'published'),
('kb007', '糖尿病视网膜病变', '糖尿病视网膜病变是最常见微血管并发症，早期无明显症状。控制血糖、血压、血脂是预防关键。眼底检查是主要筛查方法。', 'disease', '["糖尿病", "视网膜", "并发症"]', 'published'),
('kb008', '糖尿病肾病', '糖尿病肾病是主要微血管并发症，早期表现为微量白蛋白尿。控制血糖、血压（<130/80 mmHg），使用ACEI/ARB类药物可延缓进展。', 'disease', '["糖尿病", "肾病", "并发症"]', 'published'),
('kb009', 'GI食物表', '低GI食物(<55)：全麦面包、燕麦、苹果、梨、牛奶。中GI食物(55-70)：白面包、蜂蜜、西瓜。高GI食物(>70)：白米饭、土豆、西瓜。', 'food', '["食物", "GI", "升糖指数"]', 'published'),
('kb010', 'GL食物表', 'GL=GI×碳水化合物含量÷100。低GL食物(<10)：苹果、梨。中GL食物(11-19)：香蕉、葡萄。高GL食物(>20)：米饭、馒头。', 'food', '["食物", "GL", "血糖负荷"]', 'published'),
('kb011', '糖尿病运动处方', '糖尿病运动处方：每周至少150分钟中等强度有氧运动，分5天进行。每次30分钟，运动后心率达到最大心率的50-70%。', 'exercise', '["糖尿病", "运动", "处方"]', 'published'),
('kb012', '二甲双胍用药指南', '二甲双胍是2型糖尿病一线用药，餐中或餐后服用以减少胃肠道反应。常见副作用：恶心、腹泻、腹胀。肝肾功能不全者禁用。', 'drug', '["糖尿病", "二甲双胍", "用药"]', 'published'),
('kb013', '胰岛素存储', '胰岛素存储：未开封2-8°C冷藏，开封后可室温(<30°C)保存30天。避免冷冻、阳光直射、剧烈摇晃。外出携带使用保温包。', 'drug', '["糖尿病", "胰岛素", "存储"]', 'published'),
('kb014', '糖尿病患者水果选择', '糖尿病患者可适量食用低GI水果：草莓、蓝莓、樱桃、苹果、梨、橙子。建议在两餐之间食用，每天200g以内。', 'food', '["糖尿病", "水果", "饮食"]', 'published'),
('kb015', '糖尿病酮症酸中毒', '糖尿病酮症酸中毒(DKA)是严重急性并发症，常见于1型糖尿病。症状：口渴、多尿、恶心呕吐、腹痛、呼气有烂苹果味。需立即就医。', 'disease', '["糖尿病", "酮症酸中毒", "急症"]', 'published'),
-- 高血压相关 (16-25)
('kb016', '高血压诊断标准', '高血压诊断标准：收缩压≥140 mmHg或舒张压≥90 mmHg。正常血压：收缩压<120 mmHg且舒张压<80 mmHg。', 'disease', '["高血压", "诊断", "血压"]', 'published'),
('kb017', '高血压生活方式干预', '高血压生活方式干预包括：限盐（<6g/天）、控制体重（BMI<24）、戒烟限酒、适量运动、保持心理平衡。', 'disease', '["高血压", "生活方式"]', 'published'),
('kb018', '血压控制目标', '血压控制目标：一般高血压患者<140/90 mmHg，糖尿病患者<130/80 mmHg，老年患者(≥65岁)<150/90 mmHg。', 'disease', '["高血压", "控制目标"]', 'published'),
('kb019', '高血压药物选择', '常用降压药：利尿剂（氢氯噻嗪）、钙通道阻滞剂（氨氯地平）、ACEI（培哚普利）、ARB（厄贝沙坦）、β受体阻滞剂（美托洛尔）。', 'drug', '["高血压", "降压药", "用药"]', 'published'),
('kb020', '清晨高血压', '清晨高血压指清晨醒后1小时内血压≥140/90 mmHg。建议使用长效降压药，睡前服用，可监测动态血压评估。', 'disease', '["高血压", "清晨血压"]', 'published'),
('kb021', '盐敏感性高血压', '盐敏感性高血压患者限盐降压效果明显。建议每日食盐<3g，可使用低钠富钾盐替代。', 'disease', '["高血压", "限盐"]', 'published'),
('kb022', '高血压急症', '高血压急症：血压≥180/120 mmHg伴靶器官损害。症状：胸痛，呼吸困难、头痛、视力模糊、意识障碍。需立即就医。', 'disease', '["高血压", "急症"]', 'published'),
('kb023', '运动与高血压', '高血压运动处方：有氧运动为主，快走、慢跑、游泳、骑自行车，每周5-7次，每次30-60分钟。运动强度达到中等，RPE 12-14。', 'exercise', '["高血压", "运动"]', 'published'),
('kb024', 'DASH饮食', 'DASH饮食：富含水果、蔬菜、全谷物、低脂奶制品、坚果。钠摄入<1500mg/天，可降低血压8-14 mmHg。', 'food', '["高血压", "DASH", "饮食"]', 'published'),
('kb025', '高血压心血管风险评估', '高血压心血管风险评估因素：年龄、性别、吸烟、总胆固醇、糖尿病、心血管病家族史、左心室肥厚、蛋白尿等。', 'disease', '["高血压", "心血管", "风险"]', 'published'),
-- 高血脂相关 (26-29)
('kb026', '血脂检查项目', '血脂检查项目：总胆固醇(TC)、甘油三酯(TG)、低密度脂蛋白(LDL-C)、高密度脂蛋白(HDL-C)。LDL-C是首要治疗目标。', 'disease', '["高血脂", "血脂", "检查"]', 'published'),
('kb027', '血脂控制目标', '血脂控制目标：极高危(ASCVD)<1.8 mmol/L，高危<2.6 mmol/L，中危<3.4 mmol/L。HDL-C>1.0 mmol/L(男)/1.2 mmol/L(女)。', 'disease', '["高血脂", "控制目标"]', 'published'),
('kb028', '他汀类药物', '他汀类药物是降脂一线用药：阿托伐他汀、瑞舒伐他汀、辛伐他汀等。主要副作用：肝酶升高、肌肉疼痛。定期监测肌酸激酶。', 'drug', '["高血脂", "他汀", "用药"]', 'published'),
('kb029', '饮食降脂', '降脂饮食：减少饱和脂肪(动物油、肥肉)、反式脂肪(油炸食品)摄入。增加膳食纤维(燕麦、苹果)、植物甾醇(坚果)。', 'food', '["高血脂", "饮食"]', 'published'),
-- 慢病综合 (30-35)
('kb030', '慢性病运动处方', '慢性病患者运动建议：每周至少150分钟中等强度有氧运动，如快走、游泳、骑自行车。运动前后监测血压和心率。', 'exercise', '["运动", "处方", "慢性病"]', 'published'),
('kb031', '药物服用时间', '不同药物服用时间：二甲双胍餐中或餐后服用，阿司匹林肠溶片空腹服用，他汀类药物晚上服用效果更好。', 'drug', '["药物", "服用时间"]', 'published'),
('kb032', '慢性病心理支持', '慢性病患者常见心理问题：焦虑、抑郁。应对方法：保持社交活动，培养兴趣爱好、必要时寻求专业心理帮助。', 'nursing', '["心理", "慢性病", "情绪"]', 'published'),
('kb033', '慢病患者体重管理', '体重管理：超重或肥胖患者减轻5-10%体重可显著改善血糖、血压、血脂。目标BMI 18.5-24。', 'disease', '["体重", "管理", "肥胖"]', 'published'),
('kb034', '戒烟对慢病的好处', '戒烟好处：降低心血管病风险，改善血压、血脂、肺功能。戒烟后1年冠心病风险下降50%，5年后接近非吸烟者。', 'nursing', '["戒烟", "心血管"]', 'published'),
('kb035', '慢病随访计划', '慢病随访：糖尿病每3个月复查HbA1c，每半年全面检查。高血压每月复查，病情稳定可延长间隔。定期评估并发症。', 'nursing', '["随访", "慢性病"]', 'published'),
-- 营养知识 (36-40)
('kb036', '蛋白质摄入建议', '蛋白质摄入：慢性肾病患者需限制(0.6-0.8g/kg/天)，一般患者1.0-1.2g/kg/天。优质蛋白占50%以上：鱼、蛋、奶、豆制品。', 'food', '["营养", "蛋白质"]', 'published'),
('kb037', '膳食纤维摄入', '膳食纤维摄入建议：25-30g/天。可降低血糖、血脂，改善便秘。来源：全谷物、蔬菜、水果、豆类。', 'food', '["营养", "膳食纤维"]', 'published'),
('kb038', '钠钾摄入平衡', '钠钾平衡：钠<2000mg/天，钾3600mg/天(男)/2700mg/天(女)。高钾食物：香蕉、橙子、土豆、菠菜。肾功能不全者需注意。', 'food', '["营养", "钠", "钾"]', 'published'),
('kb039', '慢病患者饮酒建议', '饮酒建议：糖尿病患者限制饮酒，女性<15g/天，男性<25g/天，每周不超过2次。高血压患者最好戒酒。', 'food', '["饮酒", "糖尿病", "高血压"]', 'published'),
('kb040', '维生素D与慢病', '维生素D与慢病：缺乏增加糖尿病、高血压、骨质疏松风险。建议晒太阳15-30分钟/天，或补充400-800IU/天。', 'nursing', '["维生素D", "营养"]', 'published');

-- 插入评估记录
INSERT INTO evaluations (id, agent_type, status, total_cases, passed_cases, failed_cases, pass_rate, avg_response_time, created_at, completed_at) VALUES
('eval001', 'diabetes', 'completed', 100, 92, 8, 0.92, 1.2, '2024-03-10 10:00:00', '2024-03-10 10:15:00'),
('eval002', 'hypertension', 'completed', 100, 88, 12, 0.88, 1.5, '2024-03-12 10:00:00', '2024-03-12 10:18:00');

-- =====================================================
-- 完成
-- =====================================================
SELECT '数据库初始化完成！' AS message;

-- =====================================================
-- 慢病管理扩展表 - 食物库、血糖记录、食谱
-- =====================================================

-- -----------------------------------------------------
-- 21. 食物GI/GL数据库
-- -----------------------------------------------------
DROP TABLE IF EXISTS food_database;
CREATE TABLE food_database (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    name VARCHAR(100) NOT NULL COMMENT '食物名称',
    category VARCHAR(50) NOT NULL COMMENT '分类',
    gi INT NOT NULL COMMENT '升糖指数',
    carbs_per_100g DECIMAL(5,1) NOT NULL COMMENT '每100g碳水(g)',
    serving_size DECIMAL(6,1) DEFAULT 100 COMMENT '常见份量(g)',
    calories INT DEFAULT 0 COMMENT '热量(kcal)',
    fiber DECIMAL(5,1) DEFAULT 0 COMMENT '膳食纤维(g)',
    protein DECIMAL(5,1) DEFAULT 0 COMMENT '蛋白质(g)',
    fat DECIMAL(5,1) DEFAULT 0 COMMENT '脂肪(g)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_category (category),
    INDEX idx_gi (gi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食物GI/GL数据库';

-- -----------------------------------------------------
-- 22. 患者血糖记录
-- -----------------------------------------------------
DROP TABLE IF EXISTS glucose_records;
CREATE TABLE glucose_records (
    id VARCHAR(36) PRIMARY KEY COMMENT '记录ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    glucose_value DECIMAL(4,1) NOT NULL COMMENT '血糖值(mmol/L)',
    glucose_type ENUM('fasting', 'postprandial', 'random', 'bedtime') NOT NULL COMMENT '测量类型',
    measurement_time DATETIME NOT NULL COMMENT '测量时间',
    device VARCHAR(100) COMMENT '测量设备',
    meal_info VARCHAR(255) COMMENT '餐食信息',
    exercise_info VARCHAR(255) COMMENT '运动信息',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_time (patient_id, measurement_time),
    INDEX idx_glucose_type (glucose_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='血糖记录表';

-- -----------------------------------------------------
-- 23. 患者食谱记录
-- -----------------------------------------------------
DROP TABLE IF EXISTS meal_plans;
CREATE TABLE meal_plans (
    id VARCHAR(36) PRIMARY KEY COMMENT '食谱ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack') NOT NULL COMMENT '餐次',
    plan_date DATE NOT NULL COMMENT '计划日期',
    target_carbs DECIMAL(5,1) COMMENT '目标碳水(g)',
    actual_carbs DECIMAL(5,1) COMMENT '实际碳水(g)',
    total_calories INT COMMENT '总热量',
    gl_value DECIMAL(5,1) COMMENT 'GL值',
    food_details JSON COMMENT '食物详情(JSON)',
    recommendations TEXT COMMENT '建议',
    status ENUM('planned', 'completed', 'cancelled') DEFAULT 'planned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_date (patient_id, plan_date),
    INDEX idx_meal_type (meal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者食谱表';

-- -----------------------------------------------------
-- 24. 胰岛素使用记录
-- -----------------------------------------------------
DROP TABLE IF EXISTS insulin_records;
CREATE TABLE insulin_records (
    id VARCHAR(36) PRIMARY KEY COMMENT '记录ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    insulin_type VARCHAR(50) NOT NULL COMMENT '胰岛素类型',
    dose DECIMAL(4,1) NOT NULL COMMENT '剂量(U)',
    injection_time DATETIME NOT NULL COMMENT '注射时间',
    injection_site VARCHAR(50) COMMENT '注射部位',
    pre_meal_glucose DECIMAL(4,1) COMMENT '注射前血糖',
    total_daily_insulin DECIMAL(5,1) COMMENT '当日总胰岛素',
    icr DECIMAL(5,1) COMMENT '碳水比',
    isf DECIMAL(5,1) COMMENT '敏感因子',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_time (patient_id, injection_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='胰岛素使用记录';

-- -----------------------------------------------------
-- 25. 血糖分析报告
-- -----------------------------------------------------
DROP TABLE IF EXISTS glucose_analysis_reports;
CREATE TABLE glucose_analysis_reports (
    id VARCHAR(36) PRIMARY KEY COMMENT '报告ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    analysis_type ENUM('daily', 'weekly', 'monthly') NOT NULL COMMENT '分析类型',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '结束日期',
    average_glucose DECIMAL(4,1) COMMENT '平均血糖',
    std_deviation DECIMAL(4,1) COMMENT '标准差',
    tir DECIMAL(5,2) COMMENT '时间范围内占比(%)',
    trend ENUM('rising', 'stable', 'falling') COMMENT '趋势',
    volatility ENUM('low', 'moderate', 'high') COMMENT '波动性',
    patterns JSON COMMENT '检测到的模式',
    anomalies JSON COMMENT '异常记录',
    recommendations TEXT COMMENT '建议',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_date (patient_id, start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='血糖分析报告';

-- -----------------------------------------------------
-- 26. 患者健康目标
-- -----------------------------------------------------
DROP TABLE IF EXISTS health_goals;
CREATE TABLE health_goals (
    id VARCHAR(36) PRIMARY KEY COMMENT '目标ID',
    patient_id VARCHAR(36) NOT NULL COMMENT '患者ID',
    goal_type VARCHAR(50) NOT NULL COMMENT '目标类型',
    target_value DECIMAL(6,2) NOT NULL COMMENT '目标值',
    current_value DECIMAL(6,2) COMMENT '当前值',
    unit VARCHAR(20) COMMENT '单位',
    start_date DATE NOT NULL COMMENT '开始日期',
    target_date DATE NOT NULL COMMENT '目标日期',
    status ENUM('active', 'achieved', 'cancelled') DEFAULT 'active',
    progress DECIMAL(5,2) DEFAULT 0 COMMENT '完成进度(%)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_type (patient_id, goal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者健康目标';

-- 插入慢病管理初始化数据

-- 插入食物数据
INSERT INTO food_database (name, category, gi, carbs_per_100g, serving_size, calories, fiber, protein, fat) VALUES
-- 主食类 (22种)
('白米饭', '主食', 73, 28.2, 150, 174, 0.4, 2.6, 0.3),
('糙米饭', '主食', 68, 23.5, 150, 152, 1.8, 2.7, 0.8),
('黑米饭', '主食', 55, 23.0, 150, 151, 1.7, 2.8, 0.9),
('燕麦片', '主食', 55, 12.0, 40, 150, 4.0, 5.0, 2.5),
('燕麦粥', '主食', 55, 11.0, 250, 68, 1.5, 2.0, 1.5),
('全麦面包', '主食', 50, 41.0, 30, 81, 2.4, 4.0, 1.1),
('白面包', '主食', 75, 49.0, 30, 79, 0.7, 2.7, 1.0),
('荞麦面', '主食', 59, 25.0, 150, 172, 2.4, 5.1, 1.6),
('意面(白)', '主食', 49, 31.0, 180, 220, 1.8, 8.0, 1.3),
('意面(全麦)', '主食', 48, 26.5, 180, 185, 3.5, 7.5, 1.2),
('米粉', '主食', 61, 28.0, 150, 170, 0.5, 2.5, 0.5),
('粉丝', '主食', 65, 26.0, 150, 150, 0.3, 0.5, 0.1),
('挂面', '主食', 55, 28.0, 150, 170, 0.8, 4.5, 1.2),
('馒头', '主食', 85, 47.0, 100, 223, 1.0, 3.2, 1.0),
('花卷', '主食', 88, 45.6, 100, 215, 0.9, 3.0, 1.1),
('烙饼', '主食', 80, 51.0, 100, 266, 1.2, 3.5, 3.5),
('油条', '主食', 75, 50.0, 100, 316, 0.9, 3.5, 12.0),
('包子(肉)', '主食', 70, 28.0, 100, 223, 1.0, 7.5, 8.5),
('包子(素)', '主食', 70, 32.0, 100, 224, 1.5, 5.0, 6.0),
('饺子(肉)', '主食', 70, 25.0, 100, 215, 1.2, 8.5, 8.5),
('饺子(素)', '主食', 70, 28.0, 100, 225, 1.8, 6.0, 7.0),
-- 蔬菜类 (20种)
('土豆', '蔬菜', 62, 17.0, 100, 77, 2.0, 2.0, 0.1),
('红薯', '蔬菜', 54, 20.0, 100, 86, 3.0, 1.6, 0.1),
('南瓜', '蔬菜', 65, 5.0, 100, 26, 0.8, 1.0, 0.1),
('山药', '蔬菜', 51, 12.0, 100, 56, 2.4, 1.9, 0.2),
('芋头', '蔬菜', 48, 13.0, 100, 56, 1.0, 1.5, 0.1),
('莲藕', '蔬菜', 38, 11.0, 100, 47, 2.2, 1.2, 0.1),
('胡萝卜', '蔬菜', 39, 8.0, 100, 41, 2.8, 0.9, 0.2),
('白萝卜', '蔬菜', 26, 4.0, 100, 20, 1.6, 0.7, 0.1),
('番茄', '蔬菜', 15, 3.0, 100, 15, 1.2, 0.9, 0.2),
('黄瓜', '蔬菜', 15, 2.0, 100, 12, 0.5, 0.8, 0.2),
('茄子', '蔬菜', 15, 3.0, 100, 15, 1.0, 1.0, 0.1),
('青椒', '蔬菜', 15, 4.0, 100, 18, 1.5, 0.9, 0.2),
('西葫芦', '蔬菜', 15, 3.0, 100, 14, 0.8, 0.8, 0.1),
('菠菜', '蔬菜', 15, 2.0, 100, 14, 2.2, 2.9, 0.4),
('生菜', '蔬菜', 15, 2.0, 100, 12, 1.0, 1.0, 0.2),
('白菜', '蔬菜', 15, 2.0, 100, 14, 1.2, 1.0, 0.1),
('油菜', '蔬菜', 15, 2.0, 100, 14, 1.5, 1.2, 0.3),
('西兰花', '蔬菜', 15, 3.0, 100, 24, 2.6, 2.8, 0.4),
('菜花', '蔬菜', 15, 3.0, 100, 21, 2.0, 1.9, 0.2),
('豆角', '蔬菜', 15, 4.0, 100, 20, 2.0, 2.5, 0.2),
-- 水果类 (20种)
('苹果', '水果', 36, 14.0, 200, 104, 2.4, 0.5, 0.3),
('梨', '水果', 38, 13.0, 200, 100, 3.0, 0.4, 0.2),
('桃', '水果', 42, 12.0, 200, 96, 2.0, 0.9, 0.2),
('橙子', '水果', 43, 12.0, 200, 88, 2.4, 1.2, 0.2),
('柚子', '水果', 25, 9.0, 200, 72, 1.8, 1.2, 0.2),
('葡萄', '水果', 46, 17.0, 100, 69, 0.9, 0.7, 0.2),
('葡萄柚', '水果', 25, 8.0, 200, 82, 1.6, 1.0, 0.2),
('草莓', '水果', 40, 8.0, 150, 45, 1.5, 1.0, 0.3),
('蓝莓', '水果', 53, 14.0, 100, 57, 2.4, 0.7, 0.3),
('猕猴桃', '水果', 50, 14.0, 100, 61, 2.6, 1.1, 0.5),
('菠萝', '水果', 66, 13.0, 100, 50, 1.4, 0.5, 0.1),
('芒果', '水果', 51, 15.0, 100, 65, 1.6, 0.8, 0.4),
('西瓜', '水果', 72, 6.0, 200, 60, 0.8, 0.6, 0.2),
('哈密瓜', '水果', 70, 8.0, 200, 66, 0.8, 0.5, 0.2),
('香蕉', '水果', 51, 23.0, 100, 89, 2.6, 1.1, 0.3),
('火龙果', '水果', 50, 13.0, 100, 55, 2.0, 1.1, 0.2),
('荔枝', '水果', 57, 16.0, 100, 70, 1.2, 0.9, 0.2),
('龙眼', '水果', 53, 17.0, 100, 71, 1.1, 1.0, 0.2),
('樱桃', '水果', 22, 10.0, 100, 63, 1.6, 1.1, 0.2),
('杏', '水果', 57, 10.0, 100, 48, 2.0, 1.2, 0.3),
-- 奶类 (6种)
('牛奶', '奶类', 27, 5.0, 250, 135, 0, 8.0, 8.0),
('酸奶', '奶类', 48, 12.0, 200, 118, 0, 6.0, 4.0),
('低脂牛奶', '奶类', 26, 5.0, 250, 122, 0, 8.5, 5.0),
('豆奶', '奶类', 34, 6.0, 250, 75, 0.8, 6.0, 2.5),
('奶粉', '奶类', 31, 5.0, 30, 151, 0, 8.5, 8.0),
('奶酪', '奶类', 31, 4.0, 30, 120, 0, 7.5, 9.5),
-- 坚果类 (7种)
('花生', '坚果', 14, 4.0, 30, 170, 2.0, 8.0, 14.0),
('杏仁', '坚果', 15, 5.0, 30, 173, 3.5, 6.0, 15.0),
('核桃', '坚果', 15, 4.0, 30, 185, 2.0, 4.3, 18.5),
('腰果', '坚果', 25, 8.0, 30, 175, 1.0, 5.0, 14.0),
('榛子', '坚果', 15, 5.0, 30, 179, 3.5, 5.5, 16.0),
('开心果', '坚果', 15, 5.0, 30, 159, 3.0, 5.5, 13.0),
('巴西坚果', '坚果', 10, 4.0, 30, 186, 2.0, 4.0, 19.0),
-- 豆类 (6种)
('黄豆', '豆类', 15, 6.0, 30, 51, 3.0, 8.0, 2.0),
('黑豆', '豆类', 15, 8.0, 30, 55, 3.5, 8.0, 1.5),
('红豆', '豆类', 26, 12.0, 30, 52, 3.0, 5.0, 0.5),
('绿豆', '豆类', 27, 12.0, 30, 52, 3.0, 6.0, 0.5),
('豆腐', '豆类', 15, 2.0, 100, 76, 0.3, 8.1, 3.7),
('豆浆', '豆类', 34, 6.0, 250, 75, 0.8, 6.0, 2.5),
-- 蛋白质类 (6种)
('鸡蛋', '蛋白质', 0, 1.0, 50, 78, 0, 6.3, 5.3),
('鸡胸肉', '蛋白质', 0, 0, 100, 165, 0, 31.0, 3.6),
('鱼肉', '蛋白质', 0, 0, 100, 113, 0, 20.4, 2.1),
('虾', '蛋白质', 0, 1.0, 100, 99, 0, 24.0, 0.2),
('牛肉', '蛋白质', 0, 0, 100, 250, 0, 26.0, 15.0),
('猪肉', '蛋白质', 0, 0, 100, 143, 0, 27.0, 3.5),
-- 饮料类 (4种)
('可乐', '饮料', 60, 11.0, 330, 140, 0, 0, 0),
('橙汁', '饮料', 50, 10.0, 250, 110, 0.5, 1.0, 0.5),
('苹果汁', '饮料', 41, 11.0, 250, 114, 0.5, 0.5, 0.3),
('奶茶', '饮料', 41, 10.0, 350, 266, 0.5, 6.0, 10.0),
-- 甜点/零食 (6种)
('冰淇淋', '甜点', 51, 24.0, 100, 207, 0.5, 3.5, 11.0),
('巧克力', '甜点', 49, 60.0, 30, 170, 2.0, 2.0, 9.0),
('饼干', '甜点', 72, 70.0, 30, 155, 1.0, 2.0, 5.0),
('蛋糕', '甜点', 73, 58.0, 50, 224, 0.5, 3.0, 8.0),
('蜂蜜', '甜点', 61, 75.0, 20, 64, 0, 0.1, 0),
('白砂糖', '甜点', 65, 100.0, 10, 39, 0, 0, 0),
-- 点心类 (4种)
('汤圆', '点心', 87, 44.0, 100, 280, 1.0, 4.5, 8.0),
('月饼', '点心', 52, 40.0, 100, 411, 2.0, 5.0, 20.0),
('麻团', '点心', 75, 44.0, 100, 311, 1.5, 4.0, 12.0),
('粽子', '点心', 87, 44.0, 100, 232, 1.2, 5.0, 2.5);

-- 插入患者血糖记录
INSERT INTO glucose_records (id, patient_id, glucose_value, glucose_type, measurement_time, device, notes) VALUES
('gl001', 'p001', 6.5, 'fasting', '2024-03-15 08:00:00', '罗氏血糖仪', '空腹血糖'),
('gl002', 'p001', 8.2, 'postprandial', '2024-03-15 11:30:00', '罗氏血糖仪', '早餐后2小时'),
('gl003', 'p001', 7.8, 'postprandial', '2024-03-15 18:30:00', '罗氏血糖仪', '晚餐后2小时'),
('gl004', 'p001', 6.2, 'bedtime', '2024-03-15 22:00:00', '罗氏血糖仪', '睡前'),
('gl005', 'p002', 7.8, 'fasting', '2024-03-15 07:30:00', '强生血糖仪', '空腹血糖'),
('gl006', 'p002', 9.5, 'postprandial', '2024-03-15 12:00:00', '强生血糖仪', '午餐后2小时');

-- 插入患者健康目标
INSERT INTO health_goals (id, patient_id, goal_type, target_value, current_value, unit, start_date, target_date, status, progress) VALUES
('hg001', 'p001', 'weight', 70.0, 82.5, 'kg', '2024-01-01', '2024-12-31', 'active', 24.0),
('hg002', 'p001', 'hba1c', 6.5, 6.8, '%', '2024-01-01', '2024-12-31', 'active', 50.0),
('hg003', 'p001', 'blood_sugar_fasting', 6.0, 6.5, 'mmol/L', '2024-01-01', '2024-12-31', 'active', 0.0),
('hg004', 'p002', 'weight', 65.0, 78.0, 'kg', '2024-01-01', '2024-12-31', 'active', 33.8),
('hg005', 'p002', 'hba1c', 6.5, 7.2, '%', '2024-01-01', '2024-12-31', 'active', 42.9);

-- 插入食谱计划
INSERT INTO meal_plans (id, patient_id, meal_type, plan_date, target_carbs, actual_carbs, total_calories, gl_value, food_details, recommendations, status) VALUES
('mp001', 'p001', 'breakfast', '2024-03-15', 50, 45, 350, 12, '[{"name":"全麦面包","weight":60,"carbs":25},{"name":"鸡蛋","weight":50,"carbs":0.5},{"name":"牛奶","weight":200,"carbs":10}]', '低GL早餐，适合血糖控制', 'completed'),
('mp002', 'p001', 'lunch', '2024-03-15', 70, 65, 520, 18, '[{"name":"糙米饭","weight":150,"carbs":35},{"name":"鸡胸肉","weight":100,"carbs":0},{"name":"西兰花","weight":150,"carbs":4.5},{"name":"番茄","weight":100,"carbs":3}]', '营养均衡，适量摄入', 'completed'),
('mp003', 'p001', 'dinner', '2024-03-15', 60, 55, 420, 15, '[{"name":"糙米饭","weight":120,"carbs":28},{"name":"鱼肉","weight":100,"carbs":0},{"name":"土豆","weight":100,"carbs":17},{"name":"菠菜","weight":100,"carbs":2}]', '晚餐不宜过饱', 'completed');

-- 慢病管理扩展表初始化完成
SELECT '慢病管理扩展表初始化完成！' AS message;

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;
