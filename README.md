# 🏆 공공데이터 공모전 뉴스레터

Wevity에서 공공데이터 관련 공모전 정보를 자동으로 수집하고 이메일로 발송하는 Streamlit 대시보드입니다.

## ✨ 주요 기능

- 🔍 **키워드 검색**: 원하는 주제의 공모전을 검색
- 📅 **기간 필터링**: 마감일 기준으로 공모전 필터링
- 📧 **이메일 발송**: 검색 결과를 HTML 이메일로 발송
- 💾 **데이터 다운로드**: CSV 파일로 결과 저장
- 🎨 **직관적인 UI**: Streamlit 기반의 사용자 친화적 인터페이스

## 🚀 빠른 시작

### 1. 필수 요구사항

- Python 3.8 이상
- Chrome 브라우저 (크롤링용)

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd wevity-contest-newsletter

# 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
# 환경변수 파일 생성
cp .env.example .env

# .env 파일 편집 (이메일 설정)
# EMAIL=your_email@gmail.com
# PASSWORD=your_app_password
```

### 4. 실행

```bash
# 대시보드 실행
python run_dashboard.py

# 또는 직접 실행
streamlit run wevity_dashboard.py
```


## 🧪 테스트

크롤러가 정상 작동하는지 테스트:

```bash
python test_crawler.py
```

## 📁 프로젝트 구조

```
wevity-contest-newsletter/
├── wevity_crawler.py      # 크롤링 로직
├── wevity_dashboard.py    # Streamlit 대시보드
├── email_sender.py        # 이메일 발송 기능
├── run_dashboard.py       # 실행 스크립트
├── test_crawler.py        # 테스트 스크립트
├── requirements.txt       # 패키지 의존성
├── .env.example          # 환경변수 템플릿
├── .gitignore           # Git 무시 파일
└── README.md            # 프로젝트 설명
```

## ⚙️ 설정

### 이메일 설정

Gmail을 사용하는 경우:

1. Google 계정에서 2단계 인증 활성화
2. 앱 비밀번호 생성
3. `.env` 파일에 설정:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL=your_email@gmail.com
PASSWORD=your_app_password
SENDER_NAME=공모전 알리미
```

### 크롤링 설정

`wevity_crawler.py`에서 다음 설정을 조정할 수 있습니다:

- `max_pages`: 검색할 최대 페이지 수
- `headless`: 브라우저 표시 여부
- CSS 선택자: 웹사이트 구조 변경 시 수정

## 🎯 사용법

### 1. 기본 검색

1. 사이드바에서 검색 키워드 입력
2. 검색 페이지 수 설정
3. 기간 설정 (시작일, 종료일)
4. "공모전 검색하기" 버튼 클릭

### 2. 결과 확인

- 검색된 공모전 목록 확인
- 마감일별 정렬 가능
- 긴급 마감 공모전 하이라이트

### 3. 이메일 발송

1. 받을 이메일 주소 입력
2. "이메일 발송" 버튼 클릭
3. HTML 형식의 이메일 수신

### 4. 데이터 다운로드

- "엑셀 파일로 다운로드" 버튼으로 결과 저장

## 🔧 문제 해결

### 크롤링 실패

1. Chrome 브라우저 설치 확인
2. 인터넷 연결 상태 확인
3. Wevity 웹사이트 접속 가능 여부 확인
4. CSS 선택자 업데이트 필요 여부 확인

### 이메일 발송 실패

1. `.env` 파일 설정 확인
2. Gmail 앱 비밀번호 확인
3. 방화벽/보안 프로그램 확인

### 패키지 설치 오류

```bash
# 가상환경 사용 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## ⚠️ 주의사항

- 이 도구는 교육 및 개인 사용 목적으로 제작되었습니다
- 웹 크롤링 시 해당 웹사이트의 이용약관을 준수하세요
- 과도한 요청으로 서버에 부하를 주지 않도록 주의하세요
- 개인정보 보호를 위해 `.env` 파일을 공유하지 마세요

## 📞 지원

문제가 발생하거나 개선 사항이 있다면 이슈를 등록해주세요.

---

**Happy Coding! 🎉**
