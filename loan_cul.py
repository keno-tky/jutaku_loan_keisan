import streamlit as st
import pandas as pd
import numpy as np
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots

def calculate_monthly_payment(principal, annual_rate, years, bonus_principal=0, bonus_frequency=2):
    """
    元利均等返済方式での月々返済額を計算（賞与返済対応）
    """
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    
    # 賞与返済分を除いた月々返済分の元本
    monthly_principal = principal - bonus_principal
    
    if monthly_rate == 0:
        monthly_payment = monthly_principal / num_payments
        bonus_payment = bonus_principal / (years * bonus_frequency) if bonus_principal > 0 else 0
        return monthly_payment, bonus_payment
    
    # 月々返済額
    monthly_payment = monthly_principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    # 賞与返済額（賞与返済分の元本に対する返済額）
    if bonus_principal > 0:
        bonus_payments_total = years * bonus_frequency
        bonus_payment = bonus_principal * (monthly_rate * bonus_frequency * (1 + monthly_rate * bonus_frequency)**years) / ((1 + monthly_rate * bonus_frequency)**years - 1)
    else:
        bonus_payment = 0
    
    return monthly_payment, bonus_payment

def calculate_amortization_schedule(principal, annual_rate, years, bonus_principal=0, bonus_frequency=2):
    """
    返済予定表を作成（賞与返済対応）
    """
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    monthly_payment, bonus_payment = calculate_monthly_payment(principal, annual_rate, years, bonus_principal, bonus_frequency)
    
    schedule = []
    remaining_balance = principal
    bonus_remaining = bonus_principal
    monthly_remaining = principal - bonus_principal
    
    # 賞与返済月の判定（6月と12月）
    bonus_months = []
    if bonus_frequency == 2:
        bonus_months = [6, 12]  # 6月、12月
    elif bonus_frequency == 1:
        bonus_months = [12]  # 12月のみ
    
    for month in range(1, num_payments + 1):
        is_bonus_month = (month % 12) in bonus_months
        
        # 月々返済分の利息計算
        monthly_interest = monthly_remaining * monthly_rate
        monthly_principal_payment = monthly_payment - monthly_interest
        
        # 賞与返済分の処理
        bonus_interest = 0
        bonus_principal_payment = 0
        bonus_payment_this_month = 0
        
        if is_bonus_month and bonus_remaining > 0:
            bonus_interest = bonus_remaining * monthly_rate
            bonus_principal_payment = min(bonus_payment - bonus_interest, bonus_remaining)
            bonus_payment_this_month = bonus_interest + bonus_principal_payment
            bonus_remaining -= bonus_principal_payment
        
        # 残高更新
        monthly_remaining -= monthly_principal_payment
        total_payment = monthly_payment + bonus_payment_this_month
        total_interest = monthly_interest + bonus_interest
        total_principal_payment = monthly_principal_payment + bonus_principal_payment
        remaining_balance = monthly_remaining + bonus_remaining
        
        schedule.append({
            '回数': month,
            '返済額': total_payment,
            '月々返済': monthly_payment,
            '賞与返済': bonus_payment_this_month,
            '元金': total_principal_payment,
            '利息': total_interest,
            '残高': max(0, remaining_balance)
        })
    
    return pd.DataFrame(schedule)

def main():
    st.set_page_config(
        page_title="住宅ローン返済額計算",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 住宅ローン返済額計算")
    st.write("住宅ローンの月々返済額と返済予定を計算します")
    
    # サイドバーで入力パラメータを設定
    st.sidebar.header("ローン条件")
    
    # 借入金額
    principal = st.sidebar.number_input(
        "借入金額（万円）",
        min_value=100,
        max_value=10000,
        value=2000,
        step=100
    ) * 10000  # 万円を円に変換
    
    # 年利
    annual_rate = st.sidebar.number_input(
        "年利（%）",
        min_value=0.1,
        max_value=10.0,
        value=1.05,
        step=0.05
    )
    
    # 返済期間
    years = st.sidebar.number_input(
        "返済期間（年）",
        min_value=1,
        max_value=50,
        value=25,
        step=1
    )
    
    # 賞与返済設定
    st.sidebar.header("賞与返済")
    
    use_bonus = st.sidebar.checkbox("賞与返済を利用する")
    
    bonus_principal = 0
    bonus_frequency = 2
    
    if use_bonus:
        bonus_principal = st.sidebar.number_input(
            "賞与返済元本（万円）",
            min_value=0,
            max_value=int(principal/10000),
            value=500,
            step=50
        ) * 10000
        
        bonus_frequency = st.sidebar.selectbox(
            "賞与回数",
            options=[1, 2],
            index=1,
            format_func=lambda x: f"年{x}回"
        )
    
    # 管理費・修繕積立金
    st.sidebar.header("管理費・修繕積立金")
    
    management_fee = st.sidebar.number_input(
        "管理費（月額・円）",
        min_value=0,
        max_value=50000,
        value=10000,
        step=1000
    )
    
    repair_reserve = st.sidebar.number_input(
        "修繕積立金（月額・円）",
        min_value=0,
        max_value=50000,
        value=8000,
        step=1000
    )
    
    total_monthly_cost = management_fee + repair_reserve
    
    # 計算実行
    monthly_payment, bonus_payment = calculate_monthly_payment(principal, annual_rate, years, bonus_principal, bonus_frequency)
    
    # 年間賞与返済額
    annual_bonus_payment = bonus_payment * bonus_frequency if use_bonus else 0
    
    # 総返済額計算
    total_monthly_payments = monthly_payment * years * 12
    total_bonus_payments = annual_bonus_payment * years
    total_loan_payment = total_monthly_payments + total_bonus_payments
    total_interest = total_loan_payment - principal
    
    # 月々の総支払額（ローン返済 + 管理費等）
    monthly_total_payment = monthly_payment + total_monthly_cost
    
    # 結果表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="月々ローン返済額",
            value=f"¥{monthly_payment:,.0f}",
            help="元利均等返済での月々のローン返済額"
        )
    
    with col2:
        st.metric(
            label="月々総支払額",
            value=f"¥{monthly_total_payment:,.0f}",
            help="ローン返済額 + 管理費 + 修繕積立金"
        )
    
    with col3:
        st.metric(
            label="賞与返済額",
            value=f"¥{bonus_payment:,.0f}" if use_bonus else "¥0",
            help=f"年{bonus_frequency}回の賞与返済額（1回あたり）"
        )
    
    with col4:
        st.metric(
            label="総返済額",
            value=f"¥{total_loan_payment:,.0f}",
            help="返済期間全体でのローン総返済額"
        )
    
    # 追加情報表示
    st.write("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**総利息額：** ¥{total_interest:,.0f}")
    
    with col2:
        if use_bonus:
            st.info(f"**年間賞与返済額：** ¥{annual_bonus_payment:,.0f}")
        else:
            st.info("**賞与返済：** なし")
    
    with col3:
        st.info(f"**管理費等月額：** ¥{total_monthly_cost:,.0f}")
    
    # 返済内訳の表示
    if use_bonus:
        st.write("### 返済内訳")
        breakdown_col1, breakdown_col2 = st.columns(2)
        
        with breakdown_col1:
            st.write("**月々返済分**")
            st.write(f"- 元本: ¥{(principal - bonus_principal):,.0f}")
            st.write(f"- 月々返済額: ¥{monthly_payment:,.0f}")
        
        with breakdown_col2:
            st.write("**賞与返済分**")
            st.write(f"- 元本: ¥{bonus_principal:,.0f}")
            st.write(f"- 1回あたり: ¥{bonus_payment:,.0f}")
            st.write(f"- 年間: ¥{annual_bonus_payment:,.0f}")
    
    # 返済予定表の作成
    schedule_df = calculate_amortization_schedule(principal, annual_rate, years, bonus_principal, bonus_frequency)
    
    # # グラフ表示
    # st.header("返済推移グラフ")
    
    # # 元金と利息の推移グラフ
    # fig = make_subplots(
    #     rows=2, cols=1,
    #     subplot_titles=('月々の元金・利息推移', '残高推移'),
    #     vertical_spacing=0.1
    # )
    
    # # 元金と利息の積み上げグラフ
    # fig.add_trace(
    #     go.Scatter(
    #         x=schedule_df['回数'],
    #         y=schedule_df['元金'],
    #         mode='lines',
    #         name='元金',
    #         fill='tonexty',
    #         fillcolor='rgba(0, 100, 80, 0.3)',
    #         line=dict(color='rgb(0, 100, 80)')
    #     ),
    #     row=1, col=1
    # )
    
    # fig.add_trace(
    #     go.Scatter(
    #         x=schedule_df['回数'],
    #         y=schedule_df['利息'],
    #         mode='lines',
    #         name='利息',
    #         fill='tozeroy',
    #         fillcolor='rgba(255, 100, 80, 0.3)',
    #         line=dict(color='rgb(255, 100, 80)')
    #     ),
    #     row=1, col=1
    # )
    
    # # 賞与返済がある場合は賞与返済も表示
    # if use_bonus:
    #     fig.add_trace(
    #         go.Scatter(
    #             x=schedule_df['回数'],
    #             y=schedule_df['賞与返済'],
    #             mode='markers',
    #             name='賞与返済',
    #             marker=dict(color='rgb(255, 165, 0)', size=6),
    #             showlegend=True
    #         ),
    #         row=1, col=1
    #     )
    
    # # 残高推移
    # fig.add_trace(
    #     go.Scatter(
    #         x=schedule_df['回数'],
    #         y=schedule_df['残高'],
    #         mode='lines',
    #         name='残高',
    #         line=dict(color='rgb(50, 50, 200)', width=2)
    #     ),
    #     row=2, col=1
    # )
    
    # fig.update_layout(
    #     height=600,
    #     title_text="返済シミュレーション",
    #     showlegend=True
    # )
    
    # fig.update_xaxes(title_text="返済回数（月）", row=2, col=1)
    # fig.update_yaxes(title_text="金額（円）", row=1, col=1)
    # fig.update_yaxes(title_text="残高（円）", row=2, col=1)
    
    # st.plotly_chart(fig, use_container_width=True)
    
    # 返済予定表の表示
    st.header("返済予定表")
    
    # 年次サマリー
    st.subheader("年次サマリー")
    yearly_summary = []
    for year in range(1, years + 1):
        year_data = schedule_df[(schedule_df['回数'] > (year-1)*12) & (schedule_df['回数'] <= year*12)]
        yearly_summary.append({
            '年': year,
            '年間返済額': year_data['返済額'].sum(),
            '月々返済': year_data['月々返済'].sum(),
            '賞与返済': year_data['賞与返済'].sum(),
            '年間元金': year_data['元金'].sum(),
            '年間利息': year_data['利息'].sum(),
            '年末残高': year_data['残高'].iloc[-1] if not year_data.empty else 0
        })
    
    yearly_df = pd.DataFrame(yearly_summary)
    
    # 数値フォーマット
    for col in ['年間返済額', '月々返済', '賞与返済', '年間元金', '年間利息', '年末残高']:
        yearly_df[col] = yearly_df[col].apply(lambda x: f"¥{x:,.0f}")
    
    st.dataframe(yearly_df, use_container_width=True)
    
    # 詳細な月次返済予定表（最初の12ヶ月と最後の12ヶ月を表示）
    st.subheader("月次返済予定表（抜粋）")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**最初の12ヶ月**")
        first_12 = schedule_df.head(12).copy()
        for col in ['返済額', '月々返済', '賞与返済', '元金', '利息', '残高']:
            first_12[col] = first_12[col].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(first_12, use_container_width=True)
    
    with col2:
        st.write("**最後の12ヶ月**")
        last_12 = schedule_df.tail(12).copy()
        for col in ['返済額', '月々返済', '賞与返済', '元金', '利息', '残高']:
            last_12[col] = last_12[col].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(last_12, use_container_width=True)
    
    # # CSVダウンロード
    # st.subheader("データダウンロード")
    
    # # フォーマットされていないデータでCSV作成
    # csv_data = schedule_df.to_csv(index=False, encoding='utf-8-sig')
    # bonus_text = f"_賞与{bonus_principal//10000}万円" if use_bonus else ""
    # st.download_button(
    #     label="返済予定表をCSVでダウンロード",
    #     data=csv_data,
    #     file_name=f"返済予定表_{principal//10000}万円_{annual_rate}%_{years}年{bonus_text}.csv",
    #     mime="text/csv"
    # )
    
    # 計算式の説明
    with st.expander("計算式について"):
        st.write("""
        **元利均等返済方式の計算式：**
        
        月々返済額 = 借入金額 × (月利 × (1 + 月利)^返済回数) ÷ ((1 + 月利)^返済回数 - 1)
        
        - 月利 = 年利 ÷ 12
        - 返済回数 = 返済年数 × 12
        
        **賞与返済がある場合：**
        - 借入金額を月々返済分と賞与返済分に分割
        - それぞれに対して上記計算式を適用
        - 賞与返済は年1回または年2回で計算
        
        **各月の内訳：**
        - 利息 = 前月残高 × 月利
        - 元金 = 月々返済額 - 利息
        - 残高 = 前月残高 - 元金
        
        **月々総支払額：**
        - ローン返済額 + 管理費 + 修繕積立金
        """)
    
    # 注意事項
    with st.expander("ご利用上の注意"):
        st.write("""
        - この計算は概算です。実際の返済額は金融機関により異なる場合があります
        - 管理費・修繕積立金は変動する可能性があります
        - 賞与返済は一般的に6月・12月に設定されることが多いです
        - 火災保険料、固定資産税等の費用は含まれていません
        - 実際の借入前には金融機関にご相談ください
        """)

if __name__ == "__main__":
    main()