import pandas as pd
import pymysql
from db_config import MYSQL_INFO

# 测试数据：模拟Excel中的数据
test_data = {
    '日期': ['2026-01-07', '2026-01-07'],
    '科目名称': ['银行卡存款【浦发】', '银行卡存款【浦发】'],
    '科目类型': ['资产', '资产'],
    '金额': [350000.00, 5558.64],
    '备注': ['卖房剩余', '']
}

test_df = pd.DataFrame(test_data)
print("测试数据:")
print(test_df)

# 模拟修改后的导入逻辑
print("\n模拟处理过程:")

# 连接数据库获取科目信息
try:
    conn = pymysql.connect(**MYSQL_INFO)
    query = "SELECT * FROM t_personal_subject"
    subjects_df = pd.read_sql(query, conn)
    conn.close()
    print("\n数据库中的科目信息:")
    print(subjects_df)
    
    # 创建科目名称到ID列表的映射
    subject_map = {}
    for _, row in subjects_df.iterrows():
        name = row['subject_name']
        if name not in subject_map:
            subject_map[name] = []
        subject_map[name].append(row['subject_id'])
    
    print("\n科目映射:")
    print(subject_map)
    
    # 处理测试数据
    test_df['subject_id'] = None
    
    # 为每个相同科目名称的行分配不同的ID
    for name, ids in subject_map.items():
        name_rows = test_df[test_df['科目名称'] == name]
        if not name_rows.empty:
            for i, (idx, row) in enumerate(name_rows.iterrows()):
                test_df.at[idx, 'subject_id'] = ids[i % len(ids)]
    
    print("\n处理后的数据:")
    print(test_df)
    
    # 验证是否成功分配了不同的ID
    if '银行卡存款【浦发】' in test_df['科目名称'].values:
        pufa_rows = test_df[test_df['科目名称'] == '银行卡存款【浦发】']
        print("\n浦发银行相关行:")
        print(pufa_rows)
        
        if len(pufa_rows) == 2 and len(pufa_rows['subject_id'].unique()) == 2:
            print("\n✅ 测试成功：相同科目名称的两条数据分配了不同的ID")
        else:
            print("\n❌ 测试失败：没有为相同科目名称的两条数据分配不同的ID")
    
    conn.close()
except Exception as e:
    print(f"\n❌ 测试失败: {e}")