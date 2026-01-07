import pymysql
import pandas as pd
from db_config import MYSQL_INFO

# 连接数据库
try:
    conn = pymysql.connect(**MYSQL_INFO)
    print("数据库连接成功")
    
    # 查询科目表
    query = "SELECT * FROM t_personal_subject WHERE subject_name LIKE '%浦发%'"
    df_subjects = pd.read_sql(query, conn)
    
    print("浦发相关科目:")
    print(df_subjects)
    
    # 查询所有科目
    query_all = "SELECT * FROM t_personal_subject ORDER BY subject_id"
    df_all_subjects = pd.read_sql(query_all, conn)
    
    print("\n所有科目:")
    print(df_all_subjects)
    
    conn.close()
except Exception as e:
    print(f"数据库操作失败: {e}")