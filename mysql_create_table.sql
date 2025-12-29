-- 1. 用户表
CREATE TABLE IF NOT EXISTS t_user (
  phone_number VARCHAR(11) NOT NULL COMMENT '手机号（唯一主键）',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 个人科目表（极简版，去掉冗余字段）
CREATE TABLE IF NOT EXISTS t_personal_subject (
  subject_id INT(11) NOT NULL AUTO_INCREMENT COMMENT '科目ID',
  subject_name VARCHAR(50) NOT NULL COMMENT '科目名称（如现金、房贷）',
  subject_type VARCHAR(10) NOT NULL COMMENT '资产/负债',
  PRIMARY KEY (subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人资产负债科目表';

-- 插入常用科目（不用分级，低代码简化）
INSERT INTO t_personal_subject (subject_name, subject_type) VALUES
('现金', '资产'),
('银行卡存款', '资产'),
('支付宝/微信余额', '资产'),
('理财/基金', '资产'),
('房产', '资产'),
('车辆', '资产'),
('信用卡欠款', '负债'),
('花呗/借呗欠款', '负债'),
('房贷', '负债'),
('车贷', '负债');

-- 3. 个人资产负债主表（极简版）
CREATE TABLE IF NOT EXISTS t_personal_balance (
  pb_id INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  phone_number VARCHAR(11) NOT NULL COMMENT '关联用户手机号',
  subject_id INT(11) NOT NULL COMMENT '关联科目ID',
  record_date DATE NOT NULL COMMENT '记录日期',
  current_balance DECIMAL(15,2) NOT NULL COMMENT '金额',
  remark VARCHAR(100) DEFAULT '' COMMENT '备注',
  PRIMARY KEY (pb_id),
  UNIQUE KEY idx_user_subject_date (phone_number, subject_id, record_date),
  FOREIGN KEY (subject_id) REFERENCES t_personal_subject(subject_id),
  FOREIGN KEY (phone_number) REFERENCES t_user(phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人资产负债数据表';

-- 插入示例用户
INSERT INTO t_user (phone_number) VALUES ('13800138000');

-- 插入示例数据（2025-12-31）
INSERT INTO t_personal_balance (phone_number, subject_id, record_date, current_balance, remark) VALUES
('13800138000', 1, '2025-12-31', 1500.00, '现金留存'),
('13800138000', 2, '2025-12-31', 55000.00, '12月工资'),
('13800138000', 3, '2025-12-31', 7500.00, '双十二消费500'),
('13800138000', 4, '2025-12-31', 20500.00, '基金收益500'),
('13800138000', 5, '2025-12-31', 1000000.00, '房产估值不变'),
('13800138000', 6, '2025-12-31', 148000.00, '车辆折旧2000'),
('13800138000', 7, '2025-12-31', 2000.00, '还款1000'),
('13800138000', 8, '2025-12-31', 0.00, '花呗已还清'),
('13800138000', 9, '2025-12-31', 795000.00, '房贷月供5000'),
('13800138000', 10, '2025-12-31', 48000.00, '车贷还款2000');