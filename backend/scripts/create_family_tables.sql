-- ============================================================
-- 康伴健康 - 亲情守护模块数据库表
-- 创建时间: 2026-05-14
-- 说明: 亲情账号、家庭成员、关怀消息、用户记忆、健康预警等功能表
-- ============================================================

-- ------------------------------------------------
-- 1. 家庭表 (families)
-- 存储家庭基本信息
-- ------------------------------------------------
DROP TABLE IF EXISTS `families`;
CREATE TABLE `families` (
    `id` VARCHAR(36) NOT NULL COMMENT '家庭唯一标识ID(UUID)',
    `name` VARCHAR(100) NOT NULL COMMENT '家庭名称，如：幸福一家',
    `owner_id` VARCHAR(36) NOT NULL COMMENT '户主用户ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_owner_id` (`owner_id`) COMMENT '户主ID索引，用于查询用户创建的家庭',
    INDEX `idx_created_at` (`created_at`) COMMENT '创建时间索引，用于排序和统计'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家庭信息表';


-- ------------------------------------------------
-- 2. 家庭成员表 (family_members)
-- 存储家庭成员信息
-- ------------------------------------------------
DROP TABLE IF EXISTS `family_members`;
CREATE TABLE `family_members` (
    `id` VARCHAR(36) NOT NULL COMMENT '成员唯一标识ID(UUID)',
    `family_id` VARCHAR(36) NOT NULL COMMENT '所属家庭ID',
    `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
    `user_name` VARCHAR(100) NOT NULL COMMENT '用户名称',
    `role` VARCHAR(20) NOT NULL COMMENT '角色：owner(户主)、parent(父母)、child(子女)',
    `relationship_type` VARCHAR(20) DEFAULT NULL COMMENT '关系：father(爸爸)、mother(妈妈)、son(儿子)、daughter(女儿)、self(本人)',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    `notification_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否接收通知：1=是，0=否',
    `patient_id` VARCHAR(36) DEFAULT NULL COMMENT '关联的患者ID（如为患者角色）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入家庭时间',
    PRIMARY KEY (`id`),
    INDEX `idx_family_id` (`family_id`) COMMENT '家庭ID索引，用于查询家庭成员列表',
    INDEX `idx_user_id` (`user_id`) COMMENT '用户ID索引，用于查询用户参与的家庭',
    INDEX `idx_patient_id` (`patient_id`) COMMENT '患者ID索引，用于查询患者关联的家庭',
    CONSTRAINT `fk_family_members_family` FOREIGN KEY (`family_id`) REFERENCES `families` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家庭成员表';


-- ------------------------------------------------
-- 3. 关怀消息表 (care_messages)
-- 存储家庭成员之间的关怀消息
-- ------------------------------------------------
DROP TABLE IF EXISTS `care_messages`;
CREATE TABLE `care_messages` (
    `id` VARCHAR(36) NOT NULL COMMENT '消息唯一标识ID(UUID)',
    `family_id` VARCHAR(36) NOT NULL COMMENT '所属家庭ID',
    `from_user_id` VARCHAR(36) NOT NULL COMMENT '发送者用户ID',
    `from_user_name` VARCHAR(100) DEFAULT NULL COMMENT '发送者名称',
    `to_user_id` VARCHAR(36) NOT NULL COMMENT '接收者用户ID',
    `to_user_name` VARCHAR(100) DEFAULT NULL COMMENT '接收者名称',
    `message_type` VARCHAR(20) NOT NULL DEFAULT 'manual' COMMENT '消息类型：manual(手动)、auto(自动)、alert(预警)、reminder(提醒)',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已读：1=是，0=否',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    PRIMARY KEY (`id`),
    INDEX `idx_family_id` (`family_id`) COMMENT '家庭ID索引',
    INDEX `idx_to_user_id` (`to_user_id`) COMMENT '接收者ID索引，用于查询用户收到的消息',
    INDEX `idx_to_user_is_read` (`to_user_id`, `is_read`) COMMENT '接收者+未读状态联合索引',
    INDEX `idx_created_at` (`created_at`) COMMENT '创建时间索引，用于消息排序',
    CONSTRAINT `fk_care_messages_family` FOREIGN KEY (`family_id`) REFERENCES `families` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关怀消息表';


-- ------------------------------------------------
-- 4. 用户记忆表 (user_memories)
-- 用于AI陪伴的记忆存储，支持上下文理解
-- ------------------------------------------------
DROP TABLE IF EXISTS `user_memories`;
CREATE TABLE `user_memories` (
    `id` VARCHAR(36) NOT NULL COMMENT '记忆唯一标识ID(UUID)',
    `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
    `memory_type` VARCHAR(20) NOT NULL COMMENT '记忆类型：conversation(对话)、health(健康)、preference(偏好)、emotion(情绪)、family(家庭)',
    `content` TEXT NOT NULL COMMENT '记忆内容',
    `importance` INT NOT NULL DEFAULT 5 COMMENT '重要性评分：1-10，数值越大越重要',
    `meta` JSON DEFAULT NULL COMMENT '元数据，如：来源、时间戳等',
    `embedding` TEXT DEFAULT NULL COMMENT '向量嵌入（可选，用于语义检索）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `last_accessed` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后访问时间',
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`) COMMENT '用户ID索引',
    INDEX `idx_memory_type` (`memory_type`) COMMENT '记忆类型索引',
    INDEX `idx_user_type_importance` (`user_id`, `memory_type`, `importance`) COMMENT '用户+类型+重要性联合索引',
    INDEX `idx_user_last_accessed` (`user_id`, `last_accessed`) COMMENT '用户+访问时间索引，用于近期记忆查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户记忆表';


-- ------------------------------------------------
-- 5. 健康预警表 (health_alerts)
-- 存储各类健康预警信息
-- ------------------------------------------------
DROP TABLE IF EXISTS `health_alerts`;
CREATE TABLE `health_alerts` (
    `id` VARCHAR(36) NOT NULL COMMENT '预警唯一标识ID(UUID)',
    `patient_id` VARCHAR(36) NOT NULL COMMENT '患者ID',
    `alert_type` VARCHAR(50) NOT NULL COMMENT '预警类型：data_abnormal(数据异常)、medication_missed(漏服药物)、follow_up(随访提醒)、general(一般)',
    `title` VARCHAR(200) DEFAULT NULL COMMENT '预警标题',
    `content` TEXT DEFAULT NULL COMMENT '预警详细内容',
    `severity` VARCHAR(20) NOT NULL DEFAULT 'medium' COMMENT '严重程度：low(低)、medium(中)、high(高)、urgent(紧急)',
    `vital_type` VARCHAR(50) DEFAULT NULL COMMENT '关联的指标类型：blood_pressure(血压)、blood_sugar(血糖)等',
    `vital_value` JSON DEFAULT NULL COMMENT '指标数值，如：{"systolic": 140, "diastolic": 90}',
    `is_resolved` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已解决：1=是，0=否',
    `resolved_at` DATETIME DEFAULT NULL COMMENT '解决时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '预警生成时间',
    PRIMARY KEY (`id`),
    INDEX `idx_patient_id` (`patient_id`) COMMENT '患者ID索引',
    INDEX `idx_alert_type` (`alert_type`) COMMENT '预警类型索引',
    INDEX `idx_severity` (`severity`) COMMENT '严重程度索引',
    INDEX `idx_is_resolved` (`is_resolved`) COMMENT '解决状态索引',
    INDEX `idx_patient_created` (`patient_id`, `created_at`) COMMENT '患者+时间联合索引',
    INDEX `idx_patient_unresolved` (`patient_id`, `is_resolved`, `created_at`) COMMENT '患者未处理预警查询索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康预警表';


-- ------------------------------------------------
-- 6. 增强版用药提醒表 (medication_reminders_enhanced)
-- 支持更复杂的用药提醒配置
-- ------------------------------------------------
DROP TABLE IF EXISTS `medication_reminders_enhanced`;
CREATE TABLE `medication_reminders_enhanced` (
    `id` VARCHAR(36) NOT NULL COMMENT '提醒唯一标识ID(UUID)',
    `patient_id` VARCHAR(36) NOT NULL COMMENT '患者ID',
    `drug_name` VARCHAR(100) NOT NULL COMMENT '药品名称',
    `dosage` VARCHAR(50) DEFAULT NULL COMMENT '单次用量，如：1片、2粒',
    `frequency` VARCHAR(50) DEFAULT NULL COMMENT '用药频率，如：每日3次、每周1次',
    `times` JSON NOT NULL COMMENT '具体时间点列表，如：["08:00", "12:00", "20:00"]',
    `start_date` DATETIME NOT NULL COMMENT '开始日期',
    `end_date` DATETIME DEFAULT NULL COMMENT '结束日期（为空表示长期）',
    `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1=是，0=否',
    `notify_children` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否通知家属：1=是，0=否',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_patient_id` (`patient_id`) COMMENT '患者ID索引',
    INDEX `idx_enabled` (`enabled`) COMMENT '启用状态索引',
    INDEX `idx_patient_enabled` (`patient_id`, `enabled`) COMMENT '患者启用状态联合索引',
    INDEX `idx_start_date` (`start_date`) COMMENT '开始日期索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='增强版用药提醒表';


-- ------------------------------------------------
-- 7. 增强版服药记录表 (medication_records_enhanced)
-- 记录患者实际服药情况
-- ------------------------------------------------
DROP TABLE IF EXISTS `medication_records_enhanced`;
CREATE TABLE `medication_records_enhanced` (
    `id` VARCHAR(36) NOT NULL COMMENT '记录唯一标识ID(UUID)',
    `patient_id` VARCHAR(36) NOT NULL COMMENT '患者ID',
    `reminder_id` VARCHAR(36) NOT NULL COMMENT '关联的提醒ID',
    `drug_name` VARCHAR(100) DEFAULT NULL COMMENT '药品名称',
    `dosage` VARCHAR(50) DEFAULT NULL COMMENT '实际用量',
    `scheduled_time` DATETIME NOT NULL COMMENT '计划服药时间',
    `taken_time` DATETIME DEFAULT NULL COMMENT '实际服药时间',
    `status` VARCHAR(20) NOT NULL COMMENT '状态：taken(已服)、missed(漏服)、skipped(跳过)',
    `skip_reason` VARCHAR(200) DEFAULT NULL COMMENT '跳过原因（如有）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_patient_id` (`patient_id`) COMMENT '患者ID索引',
    INDEX `idx_reminder_id` (`reminder_id`) COMMENT '提醒ID索引',
    INDEX `idx_status` (`status`) COMMENT '状态索引',
    INDEX `idx_patient_scheduled` (`patient_id`, `scheduled_time`) COMMENT '患者计划时间联合索引',
    INDEX `idx_patient_status` (`patient_id`, `status`, `scheduled_time`) COMMENT '患者状态时间联合索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='增强版服药记录表';


-- ------------------------------------------------
-- 8. 家庭菜谱表 (family_recipes)
-- 存储家庭共享的健康菜谱
-- ------------------------------------------------
DROP TABLE IF EXISTS `family_recipes`;
CREATE TABLE `family_recipes` (
    `id` VARCHAR(36) NOT NULL COMMENT '菜谱唯一标识ID(UUID)',
    `family_id` VARCHAR(36) NOT NULL COMMENT '所属家庭ID',
    `creator_id` VARCHAR(36) DEFAULT NULL COMMENT '创建者用户ID',
    `creator_name` VARCHAR(100) DEFAULT NULL COMMENT '创建者名称',
    `title` VARCHAR(200) NOT NULL COMMENT '菜谱标题',
    `description` TEXT DEFAULT NULL COMMENT '菜谱描述',
    `ingredients` JSON DEFAULT NULL COMMENT '食材列表，如：[{"name": "鸡蛋", "amount": "2个"}, ...]',
    `steps` JSON DEFAULT NULL COMMENT '烹饪步骤，如：[{"step": 1, "description": "...", "tip": "..."}, ...]',
    `cooking_time` INT DEFAULT NULL COMMENT '烹饪时间（分钟）',
    `difficulty` VARCHAR(20) DEFAULT NULL COMMENT '难度：easy(简单)、medium(中等)、hard(困难)',
    `nutrition` JSON DEFAULT NULL COMMENT '营养成分，如：{"calories": 200, "protein": 10, "fat": 5}',
    `tags` JSON DEFAULT NULL COMMENT '标签列表，如：["低糖", "高蛋白"]',
    `is_legacy` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否传承菜谱：1=是，0=否',
    `is_shared` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否家庭共享：1=是，0=否',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_family_id` (`family_id`) COMMENT '家庭ID索引',
    INDEX `idx_creator_id` (`creator_id`) COMMENT '创建者索引',
    INDEX `idx_difficulty` (`difficulty`) COMMENT '难度索引',
    INDEX `idx_cooking_time` (`cooking_time`) COMMENT '烹饪时间索引',
    INDEX `idx_created_at` (`created_at`) COMMENT '创建时间索引',
    CONSTRAINT `fk_family_recipes_family` FOREIGN KEY (`family_id`) REFERENCES `families` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家庭菜谱表';


-- ------------------------------------------------
-- 9. 菜谱评论表 (recipe_comments)
-- 存储家庭成员对菜谱的评价
-- ------------------------------------------------
DROP TABLE IF EXISTS `recipe_comments`;
CREATE TABLE `recipe_comments` (
    `id` VARCHAR(36) NOT NULL COMMENT '评论唯一标识ID(UUID)',
    `recipe_id` VARCHAR(36) NOT NULL COMMENT '所属菜谱ID',
    `user_id` VARCHAR(36) DEFAULT NULL COMMENT '评论者用户ID',
    `user_name` VARCHAR(100) DEFAULT NULL COMMENT '评论者名称',
    `content` TEXT NOT NULL COMMENT '评论内容',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    PRIMARY KEY (`id`),
    INDEX `idx_recipe_id` (`recipe_id`) COMMENT '菜谱ID索引',
    INDEX `idx_user_id` (`user_id`) COMMENT '用户ID索引',
    INDEX `idx_created_at` (`created_at`) COMMENT '评论时间索引',
    CONSTRAINT `fk_recipe_comments_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `family_recipes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜谱评论表';


-- ============================================================
-- 初始化数据
-- ============================================================

-- 插入测试数据（可选）
-- INSERT INTO `families` (`id`, `name`, `owner_id`, `created_at`) VALUES
-- ('family-test-001', '幸福一家', 'user-test-001', NOW());

-- INSERT INTO `family_members` (`id`, `family_id`, `user_id`, `user_name`, `role`, `relationship_type`, `created_at`) VALUES
-- ('member-test-001', 'family-test-001', 'user-test-001', '张三', 'owner', 'self', NOW());
