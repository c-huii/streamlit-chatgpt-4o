import streamlit as st
import openai
import plotly.graph_objects as go
import re

# OpenAI API 키
openai.api_key = "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"

# 제목
st.title("⚽ 둥근 AI - 축구 승률 예측 대시보드")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "경기 데이터를 입력하면 우승 확률, 점유율, 예상 스코어를 예측해드릴게요!"}]

# 사이드바 입력
st.sidebar.header("🔍 경기 정보 입력")
team_a = st.sidebar.text_input("팀 A 이름", value="팀 A")
team_b = st.sidebar.text_input("팀 B 이름", value="팀 B")

team_a_info = st.sidebar.text_area(f"{team_a}의 정보 입력", height=100)
team_b_info = st.sidebar.text_area(f"{team_b}의 정보 입력", height=100)
article_links = st.sidebar.text_area("📰 관련 기사 요약 또는 링크 (최대 10개)", height=150)

predict_btn = st.sidebar.button("예측하기")

# GPT 예측 함수
def get_prediction(team_a, team_b, info_a, info_b, articles):
    prompt = f"""
다음 팀 정보와 기사 요약을 바탕으로, 
- 각 팀의 우승 확률(%)
- 점유율(%)
- 예상 스코어(숫자)
- 승부차기 결과(숫자, 승자 표시)
를 각각 줄 단위로 표처럼 예측해줘.

예시:
- {team_a} 승률: 65%
- {team_b} 승률: 35%
- 점유율: {team_a} 58% / {team_b} 42%
- 예상 스코어: {team_a} 2 - 1 {team_b}
- 승부차기 예상: {team_a} 4 - 3 {team_b}, 승자 {team_a}

[{team_a}]
{info_a}

[{team_b}]
{info_b}

[기사 요약/링크]
{articles}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


# 예측 실행 및 시각화
if predict_btn:
    if not team_a.strip() or not team_b.strip():
        st.error("⚠️ 두 팀의 이름을 모두 입력해주세요.")
    else:
        with st.spinner("예측 중입니다..."):
            result = get_prediction(team_a, team_b, team_a_info, team_b_info, article_links)

        st.subheader("📊 예측 결과")
        st.markdown(result)

        # 승률 및 점유율 추출
        percent_match = re.findall(r"(\d+)%", result)
        team_a_score = team_b_score = None

        if len(percent_match) >= 4:
            a_win_rate = float(percent_match[0])
            b_win_rate = float(percent_match[1])
            a_possession = float(percent_match[2])
            b_possession = float(percent_match[3])

            # ✅ 점유율 파이차트
            st.markdown("### 🥧 점유율 파이차트")
            fig_pie = go.Figure(data=[go.Pie(
                labels=[team_a, team_b],
                values=[a_possession, b_possession],
                marker_colors=["blue", "red"],
                hole=0.4
            )])
            st.plotly_chart(fig_pie, use_container_width=True)

            # ✅ 게이지 차트 (파랑/빨강)
            st.markdown("### ⛽ 양 팀 우승 확률 게이지")
            fig_gauge = go.Figure()

            fig_gauge.add_trace(go.Indicator(
                mode="gauge+number",
                value=a_win_rate,
                title={'text': team_a},
                domain={'x': [0, 0.5], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "blue"},
                    'steps': [
                        {'range': [0, 50], 'color': "#FFCCCC"},
                        {'range': [50, 75], 'color': "#FFF2CC"},
                        {'range': [75, 100], 'color': "#CCFFCC"},
                    ]
                }
            ))

            fig_gauge.add_trace(go.Indicator(
                mode="gauge+number",
                value=b_win_rate,
                title={'text': team_b},
                domain={'x': [0.5, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "red"},
                    'steps': [
                        {'range': [0, 50], 'color': "#FFCCCC"},
                        {'range': [50, 75], 'color': "#FFF2CC"},
                        {'range': [75, 100], 'color': "#CCFFCC"},
                    ]
                }
            ))

            st.plotly_chart(fig_gauge, use_container_width=True)

        else:
            st.warning("⚠️ 승률 또는 점유율 정보를 정확히 추출할 수 없습니다.")

        # ✅ 스코어 추출
        score_match = re.search(r"(\d{1,2})\s*[-:~대]\s*(\d{1,2})", result)

        if score_match:
            team_a_score = score_match.group(1)
            team_b_score = score_match.group(2)
            score_text = f"🏁 예상 최종 스코어: **{team_a} {team_a_score} - {team_b_score} {team_b}**"
        else:
            score_text = "❓ 예상 스코어를 찾을 수 없습니다."

        st.markdown("### 🧾 최종 스코어")
        st.markdown(f"<h2 style='text-align: center;'>{score_text}</h2>", unsafe_allow_html=True)

        # ✅ 승부차기 결과 추출
        shootout_match = re.search(
            r"승부차기.*?(\d{1,2})\s*[-:~대]\s*(\d{1,2}).*?(" + re.escape(team_a) + "|" + re.escape(team_b) + ")",
            result
        )

        if shootout_match:
            s_a = shootout_match.group(1)
            s_b = shootout_match.group(2)
            winner = shootout_match.group(3)
            shootout_text = f"⚽ 승부차기 예상: **{team_a} {s_a} - {s_b} {team_b}**, 승자는 **{winner}**"
            st.markdown("### 🔚 승부차기 결과")
            st.markdown(f"<h3 style='text-align: center;'>{shootout_text}</h3>", unsafe_allow_html=True)

