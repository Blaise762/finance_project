import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
from db_config import MYSQL_INFO, TITLE

# ===================== 极简数据库连接+数据获取 =====================
#1:连接数据库
def get_db_conn():
    try:
        conn = pymysql.connect(**MYSQL_INFO)
        return conn
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        st.stop()

#2:获取核心数据
def get_data(time_period_type, start_date=None, end_date=None):
    conn = get_db_conn()
    
    # 根据时间粒度构建查询条件
    if time_period_type == '年度':
        # 获取当前选中年份的所有数据
        year = start_date[:4]
        where_clause = f"b.record_date LIKE '{year}%'"
    elif time_period_type == '季度':
        # 获取当前选中季度的所有数据
        year = start_date[:4]
        month = int(start_date[5:7])
        quarter = (month - 1) // 3 + 1
        if quarter == 1:
            where_clause = f"b.record_date BETWEEN '{year}-01-01' AND '{year}-03-31'"
        elif quarter == 2:
            where_clause = f"b.record_date BETWEEN '{year}-04-01' AND '{year}-06-30'"
        elif quarter == 3:
            where_clause = f"b.record_date BETWEEN '{year}-07-01' AND '{year}-09-30'"
        else:
            where_clause = f"b.record_date BETWEEN '{year}-10-01' AND '{year}-12-31'"
    elif time_period_type == '月度':
        # 获取当前选中月份的所有数据
        month = start_date[:7]
        where_clause = f"b.record_date LIKE '{month}%'"
    else:  # 自定义
        where_clause = f"b.record_date BETWEEN '{start_date}' AND '{end_date}'"
    
    # 查询明细数据
    df_detail = pd.read_sql(f"""
        SELECT s.subject_name, s.subject_type, COALESCE(b.current_balance, 0) AS current_balance, b.remark, b.record_date
        FROM t_personal_balance b
        LEFT JOIN t_personal_subject s ON b.subject_id = s.subject_id
        WHERE {where_clause}
        ORDER BY b.record_date DESC
    """, conn)
    
    # 查汇总数据（总资产/总负债/净资产）
    df_sum = pd.read_sql(f"""
        SELECT
            COALESCE(SUM(CASE WHEN s.subject_type='资产' THEN b.current_balance ELSE 0 END), 0) AS 总资产,
            COALESCE(SUM(CASE WHEN s.subject_type='负债' THEN b.current_balance ELSE 0 END), 0) AS 总负债,
            COALESCE(SUM(CASE WHEN s.subject_type='资产' THEN b.current_balance ELSE 0 END) -
            SUM(CASE WHEN s.subject_type='负债' THEN b.current_balance ELSE 0 END), 0) AS 净资产
        FROM t_personal_balance b
        LEFT JOIN t_personal_subject s ON b.subject_id = s.subject_id
        WHERE {where_clause}
    """, conn)
    
    conn.close()
    
    # 确保数据完整性
    if df_sum.empty:
        # 如果没有数据，返回默认值
        df_sum_default = pd.Series({'总资产': 0, '总负债': 0, '净资产': 0})
        return df_detail, df_sum_default
    else:
        # 处理可能的None值，确保数值类型正确
        df_sum_filled = df_sum.iloc[0].fillna(0)
        return df_detail, df_sum_filled

#3:获取趋势数据（近3个时间单位）
def get_trend_data(time_period_type, current_start_date):
    conn = get_db_conn()
    trend_data = []
    
    # 根据时间粒度计算近3个时间单位的范围
    if time_period_type == '年度':
        current_year = int(current_start_date[:4])
        # 计算近3年的年份（包括当前年）
        years = [current_year - 2, current_year - 1, current_year]
        for year in years:
            where_clause = f"b.record_date LIKE '{year}%'"
            df = pd.read_sql(f"""
                SELECT
                    '{year}' AS period,
                    COALESCE(SUM(CASE WHEN s.subject_type='资产' THEN b.current_balance ELSE 0 END), 0) AS 总资产,
                    COALESCE(SUM(CASE WHEN s.subject_type='负债' THEN b.current_balance ELSE 0 END), 0) AS 总负债
                FROM t_personal_balance b
                LEFT JOIN t_personal_subject s ON b.subject_id = s.subject_id
                WHERE {where_clause}
            """, conn)
            if not df.empty:
                trend_data.append(df.iloc[0])
    
    elif time_period_type == '季度':
        current_year = int(current_start_date[:4])
        current_month = int(current_start_date[5:7])
        current_quarter = (current_month - 1) // 3 + 1
        
        # 计算近3个季度的开始和结束日期
        quarters = []
        for i in range(2, -1, -1):
            q_ago = current_quarter - i
            if q_ago <= 0:
                quarter_year = current_year - 1
                quarter_num = q_ago + 4
            else:
                quarter_year = current_year
                quarter_num = q_ago
            
            if quarter_num == 1:
                q_start = f"{quarter_year}-01-01"
                q_end = f"{quarter_year}-03-31"
                period_label = f"{quarter_year}Q{quarter_num}"
            elif quarter_num == 2:
                q_start = f"{quarter_year}-04-01"
                q_end = f"{quarter_year}-06-30"
                period_label = f"{quarter_year}Q{quarter_num}"
            elif quarter_num == 3:
                q_start = f"{quarter_year}-07-01"
                q_end = f"{quarter_year}-09-30"
                period_label = f"{quarter_year}Q{quarter_num}"
            else:
                q_start = f"{quarter_year}-10-01"
                q_end = f"{quarter_year}-12-31"
                period_label = f"{quarter_year}Q{quarter_num}"
            
            quarters.append((period_label, q_start, q_end))
        
        # 按时间顺序查询数据
        for period_label, q_start, q_end in quarters:
            where_clause = f"b.record_date BETWEEN '{q_start}' AND '{q_end}'"
            df = pd.read_sql(f"""
                SELECT
                    '{period_label}' AS period,
                    COALESCE(SUM(CASE WHEN s.subject_type='资产' THEN b.current_balance ELSE 0 END), 0) AS 总资产,
                    COALESCE(SUM(CASE WHEN s.subject_type='负债' THEN b.current_balance ELSE 0 END), 0) AS 总负债
                FROM t_personal_balance b
                LEFT JOIN t_personal_subject s ON b.subject_id = s.subject_id
                WHERE {where_clause}
            """, conn)
            if not df.empty:
                trend_data.append(df.iloc[0])
    
    elif time_period_type == '月度':
        current_year = int(current_start_date[:4])
        current_month = int(current_start_date[5:7])
        
        # 计算近3个月的年月
        months = []
        for i in range(2, -1, -1):
            m_ago = current_month - i
            if m_ago <= 0:
                month_year = current_year - 1
                month_num = m_ago + 12
            else:
                month_year = current_year
                month_num = m_ago
            
            month_str = f"{month_year}-{month_num:02d}"
            period_label = month_str
            months.append((period_label, month_str))
        
        # 按时间顺序查询数据
        for period_label, month_str in months:
            where_clause = f"b.record_date LIKE '{month_str}%'"
            df = pd.read_sql(f"""
                SELECT
                    '{period_label}' AS period,
                    COALESCE(SUM(CASE WHEN s.subject_type='资产' THEN b.current_balance ELSE 0 END), 0) AS 总资产,
                    COALESCE(SUM(CASE WHEN s.subject_type='负债' THEN b.current_balance ELSE 0 END), 0) AS 总负债
                FROM t_personal_balance b
                LEFT JOIN t_personal_subject s ON b.subject_id = s.subject_id
                WHERE {where_clause}
            """, conn)
            if not df.empty:
                trend_data.append(df.iloc[0])
    
    conn.close()
    
    # 转换为DataFrame
    if trend_data:
        trend_df = pd.DataFrame(trend_data)
        return trend_df
    else:
        # 如果没有数据，返回空DataFrame
        return pd.DataFrame(columns=['period', '总资产', '总负债'])

# ===================== Streamlit可视化 =====================
# 1. 网页基础设置
st.set_page_config(page_title=TITLE, page_icon="💰", layout="wide")

# 自定义标题样式：调小字体并改为深蓝色
st.markdown(f"""
<style>
/* 标题样式 */
h1 {{ font-size: 30px !important; color: #1a5276 !important; }}

/* 直接定位Streamlit生成的指标组件，为其添加边框 */
[data-testid="metric-container"] {{ 
    padding: 1rem !important; 
    border-radius: 0.5rem !important; 
    border: 1px solid #e0e0e0 !important; 
    background-color: white !important; 
    width: 100% !important; 
    box-sizing: border-box !important; 
    margin: 0 !important; 
}}

/* 确保在移动端正常显示 */
@media (max-width: 768px) {{
    [data-testid="metric-container"] {{ 
        padding: 0.5rem !important; 
    }}
}}
</style>
""", unsafe_allow_html=True)

# 使用markdown显示标题，避免st.title的默认样式
st.markdown(f"<h1>{TITLE}</h1>", unsafe_allow_html=True)

# 2. 时间选择控件
st.sidebar.subheader("时间范围选择")
time_period = st.sidebar.selectbox("选择时间粒度", ["年度", "季度", "月度", "自定义"])

# 初始化日期变量
start_date = None
end_date = None

# 根据选择的时间粒度显示不同的控件
if time_period == "年度":
    selected_year = st.sidebar.selectbox("选择年份", [2023, 2024, 2025, 2026], index=2)  # 默认2025年
    start_date = f"{selected_year}-01-01"
    end_date = f"{selected_year}-12-31"
elif time_period == "季度":
    selected_year = st.sidebar.selectbox("选择年份", [2023, 2024, 2025, 2026], index=2)  # 默认2025年
    selected_quarter = st.sidebar.selectbox("选择季度", [1, 2, 3, 4])
    if selected_quarter == 1:
        start_date = f"{selected_year}-01-01"
        end_date = f"{selected_year}-03-31"
    elif selected_quarter == 2:
        start_date = f"{selected_year}-04-01"
        end_date = f"{selected_year}-06-30"
    elif selected_quarter == 3:
        start_date = f"{selected_year}-07-01"
        end_date = f"{selected_year}-09-30"
    else:
        start_date = f"{selected_year}-10-01"
        end_date = f"{selected_year}-12-31"
elif time_period == "月度":
    selected_year = st.sidebar.selectbox("选择年份", [2023, 2024, 2025, 2026], index=2)  # 默认2025年
    selected_month = st.sidebar.selectbox("选择月份", range(1, 13), index=11)  # 默认12月
    start_date = f"{selected_year}-{selected_month:02d}-01"
    if selected_month == 12:
        end_date = f"{selected_year}-{selected_month}-31"
    else:
        next_month = selected_month + 1
        end_date = f"{selected_year}-{next_month:02d}-01"  # 这里可以优化为获取当月最后一天
else:  # 自定义
    # 设置默认结束日期为当天
    default_end_date = pd.to_datetime("today")
    # 设置默认开始日期为结束日期的前一年
    default_start_date = default_end_date - pd.DateOffset(years=1)
    
    start_date = st.sidebar.date_input("开始日期", value=default_start_date).strftime("%Y-%m-%d")
    end_date = st.sidebar.date_input("结束日期", value=default_end_date).strftime("%Y-%m-%d")

# 3. 加载数据
df_detail, df_sum = get_data(time_period, start_date, end_date)

# 4. 核心指标卡片
c1, c2, c3 = st.columns(3)

# 确保数值不为None，使用0代替
total_assets = df_sum['总资产'] if df_sum['总资产'] is not None else 0
total_liabilities = df_sum['总负债'] if df_sum['总负债'] is not None else 0
net_assets = df_sum['净资产'] if df_sum['净资产'] is not None else 0

# 创建自定义指标卡片函数
def create_metric_card(label, value):
    return f"""
    <div style="
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        background-color: white;
        width: 100%;
        box-sizing: border-box;
        text-align: center;
    ">
        <div style="font-size: 14px; color: #666; margin-bottom: 0.5rem;">{label}</div>
        <div style="font-size: 24px; font-weight: bold;">{value}</div>
    </div>
    """

# 添加自定义指标卡片
with c1:
    st.markdown(create_metric_card("总资产 💰", f"¥{total_assets:,.2f}"), unsafe_allow_html=True)

with c2:
    st.markdown(create_metric_card("总负债 💳", f"¥{total_liabilities:,.2f}"), unsafe_allow_html=True)

with c3:
    st.markdown(create_metric_card("净资产 💎", f"¥{net_assets:,.2f}"), unsafe_allow_html=True)

# 5. 趋势折线图（近3个时间单位的总资产/负债变化）
st.subheader("总资产负债趋势")
if time_period != "自定义":  # 自定义时间粒度不显示趋势图
    # 获取趋势数据
    trend_df = get_trend_data(time_period, start_date)
    
    if not trend_df.empty:
        # 生成图表标题
        if time_period == "年度":
            # 提取年份并生成标题
            years = sorted(trend_df['period'].astype(int))
            title = f"{years[0]}-{years[-1]}年总资产/负债趋势"
        elif time_period == "季度":
            # 提取季度并生成标题
            quarters = sorted(trend_df['period'])
            title = f"{quarters[0]}-{quarters[-1]}总资产/负债趋势"
        else:  # 月度
            # 提取月份并生成标题
            months = sorted(trend_df['period'])
            title = f"{months[0]}～{months[-1]}月总资产/负债趋势"
        
        # 绘制折线图，设置颜色：总负债为红色
        fig = px.line(trend_df, x='period', y=['总资产', '总负债'], 
                     title=title, 
                     markers=True, 
                     labels={'value': '金额（元）', 'period': '时间', 'variable': '指标'}, 
                     color_discrete_map={'总资产': 'blue', '总负债': 'red'})
        # 设置颜色和样式
        fig.update_traces(line=dict(width=3))
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=430  # 设置合适的图表高度，减少垂直空间占用
        )
        
        st.plotly_chart(fig, use_container_width=True, key="trend_line")
    else:
        st.info("没有足够的历史数据生成趋势图")
else:
    st.info("自定义时间范围不支持趋势图展示")

# 6. 饼图（资产+负债）
c1, c2 = st.columns(2)
# 资产饼图
asset_df = df_detail[df_detail['subject_type']=='资产']
c1.subheader("资产构成")
if not asset_df.empty:
    c1.plotly_chart(px.pie(asset_df, values="current_balance", names="subject_name", hole=0.3), use_container_width=True, key="asset_pie")
else:
    c1.info("当前时间范围内没有资产数据")
# 负债饼图
debt_df = df_detail[df_detail["subject_type"]=="负债"]
c2.subheader("负债构成")
if not debt_df.empty:
    c2.plotly_chart(px.pie(debt_df, values="current_balance", names="subject_name", hole=0.3), use_container_width=True, key="debt_pie")
else:
    c2.info("当前时间范围内没有负债数据")

# 7. 明细表格（一键显示，带格式化）
st.subheader("资产负债明细")
if not df_detail.empty:
    df_show = df_detail[["subject_name", "subject_type", "current_balance", "remark"]]
    df_show.columns = ["科目", "类型", "金额", "备注"]
    # 金额格式化
    df_show["金额"] = df_show["金额"].apply(lambda x: f"¥{x:,.2f}")
    st.dataframe(df_show, use_container_width=True)
else:
    st.info("当前时间范围内没有数据")
