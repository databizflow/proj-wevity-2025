# wevity_dashboard.py - 깔끔한 공모전 검색 대시보드
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import base64
import traceback
import logging
from wevity_crawler import crawl_wevity
from email_sender import send_email_streamlit
import os
import io

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title=" 공모전 검색 대시보드",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
def init_session_state():
    """세션 상태 안전하게 초기화"""
    if 'search_results' not in st.session_state:
        st.session_state['search_results'] = pd.DataFrame()
    if 'search_in_progress' not in st.session_state:
        st.session_state['search_in_progress'] = False
    if 'selected_contests' not in st.session_state:
        st.session_state['selected_contests'] = set()
    if 'contest_data' not in st.session_state:
        st.session_state['contest_data'] = {}
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 1
    if 'selected_keyword' not in st.session_state:
        st.session_state['selected_keyword'] = '공공데이터'

# 세션 상태 초기화 실행
init_session_state()

def toggle_contest_selection(contest_key, contest):
    """체크박스 상태 변경 시 호출되는 콜백 함수"""
    # 세션 상태 안전하게 가져오기
    selected_contests = st.session_state.get('selected_contests', set())
    contest_data = st.session_state.get('contest_data', {})
    
    if contest_key in selected_contests:
        # 선택 해제
        selected_contests.remove(contest_key)
        if contest_key in contest_data:
            del contest_data[contest_key]
    else:
        # 선택 추가
        selected_contests.add(contest_key)
        contest_data[contest_key] = contest.to_dict()
    
    # 세션 상태 업데이트
    st.session_state['selected_contests'] = selected_contests
    st.session_state['contest_data'] = contest_data

def validate_inputs(keyword, from_date, to_date):
    """입력값 검증"""
    errors = []
    
    if not keyword.strip():
        errors.append("검색 키워드를 입력해주세요.")
    
    if from_date and to_date:
        if from_date > to_date:
            errors.append("시작일이 종료일보다 늦을 수 없습니다.")
        
        if to_date < datetime.now().date():
            errors.append("종료일이 오늘보다 이전일 수 없습니다.")
    
    return errors

def format_deadline(deadline):
    """마감일 포맷팅"""
    if deadline is None:
        return "마감일 미정"
    
    days_left = (deadline - datetime.now().date()).days
    if days_left < 0:
        return f"{deadline.strftime('%Y.%m.%d')} (마감)"
    elif days_left == 0:
        return f"{deadline.strftime('%Y.%m.%d')} (오늘 마감!)"
    elif days_left <= 7:
        return f"{deadline.strftime('%Y.%m.%d')} (D-{days_left})"
    else:
        return deadline.strftime('%Y.%m.%d')

def display_contest_card(contest, index):
    """공모전 카드 표시 - 깔끔한 카드 형태"""
    # 제목 길이 제한
    title = contest['제목']
    if len(title) > 60:
        title = title[:60] + "..."
    
    # 마감일 정보
    deadline_text = format_deadline(contest['마감일'])
    
    # 고유한 키 생성 (링크 기반)
    contest_key = f"contest_{hash(contest['링크'])}"
    
    # 상금 정보
    prize = contest.get('상금', '상금 정보 없음')
    
    # 카드 전체를 하나의 스타일된 컨테이너로
    st.markdown(f"""
    <div style="
        background: linear-gradient(-10deg, rgba(226,205,247, 0.2), rgba(202,202,202, 0.3));
        border: 1px solid rgba(224,217,236, 0.2);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    ">
        <h3 style="margin: 0 0 0 0; color: #2c3e50;">
            {title}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 2x2 그리드로 정보 배치
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    # 첫 번째 행
    with row1_col1:
        st.write(f"🏢 **주최:** {contest['주최'][:30]}{'...' if len(contest['주최']) > 30 else ''}")
    
    with row1_col2:
        # 마감일 색상 처리 (세련된 블루-그린 팔레트)
        if contest['마감일'] and (contest['마감일'] - datetime.now().date()).days <= 7:
            st.markdown(f"📅 **마감일:** <span style='color: #dc2626; font-weight: bold;'>{deadline_text}</span>", unsafe_allow_html=True)
        elif contest['마감일']:
            st.markdown(f"📅 **마감일:** <span style='color: #10b981; font-weight: bold;'>{deadline_text}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"📅 **마감일:** <span style='color: #6b7280; font-weight: bold;'>{deadline_text}</span>", unsafe_allow_html=True)
    
    # 두 번째 행
    with row2_col1:
        st.write(f"⏰ **기간:** {contest['기간'][:40]}{'...' if len(contest['기간']) > 40 else ''}")
    
    with row2_col2:
        # 액션 버튼들
        action_col1, action_col2 = st.columns(2)
        
        with action_col1:
            # 체크박스 표시 (더 예쁜 라벨)
            is_selected = st.checkbox(
                "📂 담기", 
                value=contest_key in st.session_state.get('selected_contests', set()),
                key=f"cb_{contest_key}",
                on_change=toggle_contest_selection,
                args=(contest_key, contest)
            )
        
        with action_col2:
            # 링크 버튼 (더 눈에 띄게)
            st.markdown("""
            <style>
            .stLinkButton > a {
                background: linear-gradient(45deg, #3b82f6, #1d4ed8) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 0.5rem 1rem !important;
                font-weight: 500 !important;
                box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3) !important;
                transition: all 0.3s ease !important;
            }
            .stLinkButton > a:hover {
                background: linear-gradient(45deg, #10b981, #059669) !important;
                box-shadow: 0 4px 8px rgba(16, 185, 129, 0.4) !important;
                transform: translateY(-1px) !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.link_button(
                "🚀 바로가기",
                contest['링크'],
                use_container_width=True
            )
    
    # 상금 정보 (있는 경우만)
    if prize != "상금 정보 없음" and prize:
        st.markdown(f"💰 **상금:** <span style='color: #10b981; font-weight: bold;'>{prize}</span>", unsafe_allow_html=True)
    


def display_statistics(df):
    """통계 정보 표시"""
    if df.empty:
        return
    
    total_count = len(df)
    urgent_count = len(df[df['마감일'].notna() & 
                       (df['마감일'] <= datetime.now().date() + timedelta(days=7))])
    upcoming_count = len(df[df['마감일'].notna() & 
                         (df['마감일'] > datetime.now().date() + timedelta(days=7))])
    
    # 메트릭 카드 스타일링
    st.markdown("""
    <style>
    .metric-card {
        border-radius: 100px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid rgba(224,217,236, 0.1);
    }
    .metric-title {
        font-size: 1.2em;
        margin-bottom: 8px;
        font-weight: 500;
    }
    .metric-value {
        font-size: 3em;
        font-weight: bold;
    }
    .gray { background: linear-gradient(-10deg, rgba(202,202,202, 0.4), rgba(220,220,220, 0.7)); }
    .gray .metric-title { color: #2c3e50; }
    .gray .metric-value { color: #666666; }
    
    .orange { background: linear-gradient(-10deg, rgba(221,153,51, 0.2), rgba(221,153,51, 0.4)); }
    .orange .metric-title { color: #dd9933; }
    .orange .metric-value { color: #dc7832; }
    
    .purple { background: linear-gradient(-10deg, rgba(226,205,247, 0.4), rgba(226,205,247, 0.7)); }
    .purple .metric-title { color: #8224e3; }
    .purple .metric-value { color: #a058e9; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card gray">
            <div class="metric-title">총 공모전</div>
            <div class="metric-value">{total_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card orange">
            <div class="metric-title">일주일 내 마감</div>
            <div class="metric-value">{urgent_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card purple">
            <div class="metric-title">여유있는 공모전</div>
            <div class="metric-value">{upcoming_count}</div>
        </div>
        """, unsafe_allow_html=True)

def safe_crawl_with_progress(keyword, max_pages, from_date, to_date):
    """안전한 크롤링 with 진행상황 표시"""
    progress_placeholder = st.empty()
    
    try:
        with progress_placeholder.container():
            st.info("🔄 크롤링을 시작합니다... 잠시만 기다려주세요.")
        
        # 실제 크롤링 실행
        df = crawl_wevity(
            keyword=keyword,
            max_pages=max_pages,
            from_date=from_date,
            to_date=to_date
        )
        
        progress_placeholder.empty()
        return df, None
        
    except Exception as e:
        progress_placeholder.empty()
        error_msg = f"크롤링 중 오류 발생: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return pd.DataFrame(), error_msg

def extract_prize_amount(prize_text):
    """상금 텍스트에서 1등 상금액 추출"""
    if not prize_text or prize_text == "상금 정보 없음":
        return 0
    
    import re
    
    # 1등, 대상, 최우수상 등의 키워드와 함께 나오는 상금 우선 추출
    first_prize_patterns = [
        r'(?:1등|대상|최우수상|금상|우승).*?(\d+(?:,\d+)*)\s*만원',
        r'(?:1등|대상|최우수상|금상|우승).*?(\d+(?:,\d+)*)\s*억원',
        r'(?:1등|대상|최우수상|금상|우승).*?(\d+(?:,\d+)*)\s*원',
    ]
    
    for pattern in first_prize_patterns:
        match = re.search(pattern, prize_text)
        if match:
            amount = float(match.group(1).replace(',', ''))
            if '만원' in pattern:
                return amount * 10000
            elif '억원' in pattern:
                return amount * 100000000
            else:
                return amount
    
    # 1등 상금이 명시되지 않은 경우, 가장 큰 금액 추출
    amounts = []
    
    # 억원 단위
    for match in re.finditer(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*억원?', prize_text):
        amounts.append(float(match.group(1).replace(',', '')) * 100000000)
    
    # 만원 단위
    for match in re.finditer(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*만원?', prize_text):
        amounts.append(float(match.group(1).replace(',', '')) * 10000)
    
    # 원 단위 (큰 금액만)
    for match in re.finditer(r'(\d+(?:,\d+)*)\s*원', prize_text):
        amount = float(match.group(1).replace(',', ''))
        if amount >= 100000:  # 10만원 이상만
            amounts.append(amount)
    
    # 가장 큰 금액 반환 (1등 상금일 가능성이 높음)
    return max(amounts) if amounts else 0

def main():
    # 헤더
    st.title("🏆 '위비티' 공모전 검색 대시보드")
    st.markdown("원하는 키워드와 기간으로 공모전 정보를 검색하고 관리하세요")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("🔍 검색 설정")
        
        # 키워드 입력
        keyword = st.text_input(
            "검색 키워드", 
            value='공공데이터',
            help="검색하고 싶은 키워드를 입력하세요 (예: AI, 빅데이터, 디자인)",
            disabled=st.session_state.get('search_in_progress', False),
            key="search_keyword"
        )
        
        # 페이지 수 설정
        max_pages = st.slider(
            "검색 페이지 수", 
            min_value=1, 
            max_value=5, 
            value=2,
            help="1-2페이지 권장 (빠른 검색), 3-5페이지 (상세 검색)",
            disabled=st.session_state.get('search_in_progress', False),
            key="max_pages_slider"
        )
        
        st.subheader("📅 기간 설정")
        
        # 기간 설정 옵션
        use_date_filter = st.checkbox(
            "검색 날짜 설정", 
            value=True,
            help="체크하면 특정 기간의 공모전만 검색합니다",
            key="use_date_filter_checkbox"
        )
        
        if use_date_filter:
            # 기본 날짜 설정 (더 넉넉하게)
            today = datetime.today().date()
            default_start = today
            default_end = today + timedelta(days=100)  # 100일 후까지
            
            # 날짜 입력
            from_date = st.date_input(
                "시작일", 
                value=default_start,
                help="이 날짜 이후 마감인 공모전만 검색합니다",
                disabled=st.session_state.get('search_in_progress', False),
                key="from_date_input"
            )
            
            to_date = st.date_input(
                "종료일", 
                value=default_end,
                help="이 날짜 이전 마감인 공모전만 검색합니다",
                disabled=st.session_state.get('search_in_progress', False),
                key="to_date_input"
            )
        else:
            # 기간 제한 없음 (모든 공모전)
            from_date = None
            to_date = None
            st.info("💡 모든 기간의 공모전을 검색합니다")
        
        # 입력값 검증 (기간 설정이 있을 때만)
        if use_date_filter:
            errors = validate_inputs(keyword, from_date, to_date)
        else:
            errors = []
            if not keyword.strip():
                errors.append("검색 키워드를 입력해주세요.")
        
        # 검색 버튼
        search_button = st.button(
            "🔎 공모전 검색하기", 
            type="primary",
            use_container_width=True,
            disabled=len(errors) > 0 or st.session_state.get('search_in_progress', False),
            key="search_button"
        )
        
        # 에러 메시지 표시
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        
        # 선택된 공모전 관리 (사이드바에서)
        selected_count = len(st.session_state.get('selected_contests', set()))
        
        if selected_count > 0:
            st.success(f"✅ {selected_count}개 선택됨")
            
            # 이메일 발송
            st.subheader("📧 이메일 발송")
            receiver_email = st.text_input(
                "이메일 주소",
                placeholder="example@email.com",
                help=f"선택된 {selected_count}개 공모전을 받을 이메일"
            )
            
            if st.button(f" {selected_count}개 발송", use_container_width=True):
                if receiver_email and '@' in receiver_email:
                    selected_df = pd.DataFrame(list(st.session_state['contest_data'].values()))
                    with st.spinner(" 이메일 발송 중..."):
                        send_email_streamlit(selected_df, receiver_email)
                else:
                    st.error("올바른 이메일을 입력하세요")
            
            # Excel 다운로드
            st.subheader("📊 Excel 다운로드")
            try:
                selected_df = pd.DataFrame(list(st.session_state['contest_data'].values()))
                excel_buffer = io.BytesIO()
                selected_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    label=f" {selected_count}개 다운로드",
                    data=excel_data,
                    file_name=f"선택된_공모전_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Excel 생성 오류: {e}")
        else:
            st.info("📂 공모전을 선택하면 이메일 발송 및 Excel 다운로드가 가능합니다")
        
        # 도움말
        with st.expander("💡 사용 팁"):
            st.markdown("""
            **검색 팁:**
            - 키워드: '공공데이터', 'AI', '빅데이터', '스타트업' 등
            - 기간: 마감일 기준으로 필터링됩니다
            - 페이지: 2-3페이지 검색을 권장합니다
            
            **자동 필터링:**
            - 마감일이 지난 공모전 자동 제외
            - '모집', '무료', '멘토링' 등 비공모전 키워드 제외
            """)

    # 메인 컨텐츠
    if search_button and not errors:
        st.session_state['search_in_progress'] = True
        
        # 검색 실행
        df, error = safe_crawl_with_progress(keyword, max_pages, from_date, to_date)
        
        st.session_state['search_in_progress'] = False
        
        if error:
            st.error(f"❌ 검색 실패: {error}")
            st.info("잠시 후 다시 시도하거나, 다른 키워드로 검색해보세요.")
        else:
            # 세션 상태에 결과 저장
            st.session_state['search_results'] = df
            st.session_state['input_keyword'] = keyword
            st.session_state['search_date'] = datetime.now()
            
            st.success(f"✅ 검색 완료! 총 {len(df)}개의 공모전을 찾았습니다.")
    
    # 검색 결과 표시
    if not st.session_state['search_results'].empty:
        df = st.session_state['search_results']
        keyword = st.session_state.get('input_keyword', '공공데이터')
        search_date = st.session_state.get('search_date', datetime.now())
        
        # 결과 헤더
        st.subheader("📊 검색 결과")
        st.info(f"키워드: **{keyword}** | 검색시간: {search_date.strftime('%Y-%m-%d %H:%M')} | 총 {len(df)}건")
        
        # 통계 정보
        display_statistics(df)
        
        # 정렬 옵션
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_options = ["마감 임박순", "신규 등록순", "제목 순"]
            
            sort_option = st.selectbox(
                "정렬 기준",
                sort_options,
                key="sort_option_select"
            )
        
        # 데이터 정렬
        if sort_option == "마감 임박순":
            # 마감일이 가까운 순으로 정렬 (오늘에 가까운 것부터)
            df_sorted = df.sort_values('마감일', na_position='last')
        elif sort_option == "신규 등록순":
            # 마감일이 먼 순으로 정렬 (최근 등록된 것들이 보통 마감일이 멀음)
            df_sorted = df.sort_values('마감일', ascending=False, na_position='first')
        else:
            df_sorted = df.sort_values('제목')
        
        # 페이지네이션 설정
        items_per_page = 10
        total_pages = (len(df_sorted) - 1) // items_per_page + 1
        
        if total_pages > 1:
            current_page = st.session_state.get('current_page', 1)
            start_idx = (current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            df_page = df_sorted.iloc[start_idx:end_idx]
            
            # 현재 페이지 정보 표시
            st.info(f"📄 {current_page}/{total_pages} 페이지 ({start_idx + 1}-{min(end_idx, len(df_sorted))}번째 공모전)")
        else:
            df_page = df_sorted
            st.info(f"📄 전체 {len(df_sorted)}개 공모전")
        
        # 공모전 목록 표시
        for idx, (_, contest) in enumerate(df_page.iterrows()):
            display_contest_card(contest, idx)
        
        # 페이지네이션 (이전/다음 버튼)
        if total_pages > 1:
            st.markdown("---")
            # 페이지 버튼들 (중앙 정렬)
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
            
            with col2:
                if st.button("◀️ 이전", disabled=st.session_state['current_page'] <= 1, key="prev_page_button"):
                    st.session_state['current_page'] -= 1
                    st.rerun()
            
            with col3:
                st.write(f"**{st.session_state['current_page']} / {total_pages}**")
            
            with col4:
                if st.button("다음 ▶️", disabled=st.session_state['current_page'] >= total_pages, key="next_page_button"):
                    st.session_state['current_page'] += 1
                    st.rerun()
        
        # 선택된 공모전 관리 (간단하게)
        selected_count = len(st.session_state.get('selected_contests', set()))
        
        if selected_count > 0:
            st.success(f"✅ {selected_count}개 공모전이 선택되었습니다")
            
            # 전체 선택/해제 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔲 전체 선택", key="select_all_button"):
                    selected_contests = st.session_state.get('selected_contests', set())
                    contest_data = st.session_state.get('contest_data', {})
                    
                    for idx, (_, contest) in enumerate(df_page.iterrows()):
                        contest_key = f"contest_{hash(contest['링크'])}"
                        selected_contests.add(contest_key)
                        contest_data[contest_key] = contest.to_dict()
                    
                    st.session_state['selected_contests'] = selected_contests
                    st.session_state['contest_data'] = contest_data
                    st.rerun()
            
            with col2:
                if st.button("⬜ 전체 해제", key="clear_all_button"):
                    st.session_state['selected_contests'] = set()
                    st.session_state['contest_data'] = {}
                    st.rerun()
        else:
            st.info("🎯 관심있는 공모전을 '📌 담기'로 선택하면 이메일 발송이나 Excel 다운로드가 가능해요!")
    
    else:
        # 초기 화면
        st.info("🚀 왼쪽 사이드바에서 검색 조건을 설정하고 '공모전 검색하기' 버튼을 클릭하세요.")
        
        st.subheader("✨ 주요 기능")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - 🔍 **키워드 검색**: 원하는 주제의 공모전 검색
            - 📅 **기간 필터**: 마감일 기준 맞춤 필터링
            - 🎯 **정렬 옵션**: 마감임박순, 신규등록순, 제목순            
            """)
        
        with col2:
            st.markdown("""
            - 📧 **이메일 발송**: 선택한 공모전을 이메일로 받기
            - 💾 **Excel 다운로드**: 선택한 공모전 데이터 저장            
            - 📊 **실시간 통계**: 검색 결과 한눈에 보기
            """)
        
        st.subheader("🎯 추천 키워드")
        st.caption("실제 위비티에서 검색 결과가 많이 나오는 키워드들입니다")
        
        # 더 실용적이고 유의미한 키워드들
        keywords = [
            "공공데이터", "AI", "빅데이터", "스타트업", 
            "디자인", "영상", "사진", "아이디어",
            "창업", "대학생", "청년", "혁신"
        ]
        
        cols = st.columns(4)
        for i, kw in enumerate(keywords):
            col = cols[i % 4]
            with col:
                if st.button(f"🏷️ {kw}", key=f"keyword_{i}"):
                    st.session_state['selected_keyword'] = kw
                    st.rerun()

if __name__ == "__main__":
    main()