# wevity_crawler_improved.py - 개선된 크롤러
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import logging
from typing import Optional, List, Dict
import requests
from urllib.parse import urljoin

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WevityCrawler:
    """Wevity 공모전 크롤러 클래스 - 개선 버전"""
    
    def __init__(self, headless=True, timeout=30):
        self.base_url = "https://www.wevity.com"
        self.timeout = timeout
        self.driver = None
        self.headless = headless
        self.session = requests.Session()
        
        # User-Agent 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session.headers.update(self.headers)
        
    def _setup_driver(self):
        """Chrome 드라이버 설정 - 개선된 버전"""
        options = Options()
        
        # 기본 옵션
        if self.headless:
            options.add_argument('--headless=new')  # 새로운 headless 모드
        
        # 안정성 개선 옵션들
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # 이미지 로딩 비활성화로 속도 개선
        options.add_argument('--window-size=1920,1080')
        
        # User-Agent 설정
        options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
        
        # 자동화 감지 방지
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 페이지 로딩 전략
        options.page_load_strategy = 'eager'  # DOM이 준비되면 바로 진행
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 자동화 감지 방지 스크립트
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 타임아웃 설정
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome 드라이버가 성공적으로 설정되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"드라이버 설정 실패: {e}")
            return False
    
    def _extract_deadline(self, text: str) -> Optional[datetime]:
        """텍스트에서 마감일 추출 - 개선된 정규식"""
        if not text:
            return None
            
        # 텍스트 정리
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 마감된 공모전 키워드 체크 (먼저 체크해서 빠르게 제외)
        if any(keyword in text.lower() for keyword in ['마감됨', '접수마감', '종료됨', '완료됨']):
            return datetime(2020, 1, 1)  # 과거 날짜로 설정하여 필터링되도록
        
        # 1. 접수기간 형태 패턴들
        period_patterns = [
            # 2025.01.01 ~ 2025.03.15
            r'(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})\s*[~\-까지]\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            # 25.01.01 ~ 25.03.15
            r'(\d{2}[.\-/]\d{1,2}[.\-/]\d{1,2})\s*[~\-까지]\s*(\d{2}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            # 1월 1일 ~ 3월 15일
            r'(\d{1,2})월\s*(\d{1,2})일\s*[~\-까지]\s*(\d{1,2})월\s*(\d{1,2})일',
            # 2025년 1월 1일 ~ 2025년 3월 15일
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*[~\-까지]\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
        ]
        
        for pattern in period_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '년' in pattern:  # 2025년 1월 1일 형태
                        end_year = int(match.group(4))
                        end_month = int(match.group(5))
                        end_day = int(match.group(6))
                        return datetime(end_year, end_month, end_day)
                    elif '월' in pattern:  # 한글 날짜 형태
                        end_month = int(match.group(3))
                        end_day = int(match.group(4))
                        current_year = datetime.now().year
                        return datetime(current_year, end_month, end_day)
                    else:
                        end_date_str = match.group(2)
                        return self._parse_date_string(end_date_str)
                except (ValueError, IndexError):
                    continue
        
        # 2. 단일 마감일 형태
        single_patterns = [
            r'마감\s*:?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            r'까지\s*:?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            r'(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})\s*마감',
            r'접수마감\s*:?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            r'(\d{1,2})월\s*(\d{1,2})일\s*마감',
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*마감',
            r'마감일\s*:?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
        ]
        
        for pattern in single_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if '년' in pattern:
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        return datetime(year, month, day)
                    elif '월' in pattern:
                        month = int(match.group(1))
                        day = int(match.group(2))
                        current_year = datetime.now().year
                        return datetime(current_year, month, day)
                    else:
                        return self._parse_date_string(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # 3. D-day 형태
        d_match = re.search(r'D[－\-](\d+)', text)
        if d_match:
            days_left = int(d_match.group(1))
            return datetime.now() + timedelta(days=days_left)
        
        # 4. 단순 날짜 형태 (마지막에 체크)
        simple_date_patterns = [
            r'(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            r'(\d{2}[.\-/]\d{1,2}[.\-/]\d{1,2})',
        ]
        
        for pattern in simple_date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 여러 날짜가 있으면 가장 늦은 날짜를 마감일로 간주
                dates = []
                for match in matches:
                    parsed = self._parse_date_string(match)
                    if parsed and parsed.year >= datetime.now().year:
                        dates.append(parsed)
                
                if dates:
                    return max(dates)
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열을 datetime 객체로 변환"""
        if not date_str:
            return None
            
        # 구분자 통일
        date_str = re.sub(r'[.\-/]', '.', date_str)
        
        # 날짜 형식들
        formats = [
            '%Y.%m.%d',
            '%y.%m.%d',
            '%Y.%m.%d',
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # 2자리 연도를 4자리로 변환
                if parsed_date.year < 2000:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                return parsed_date
            except ValueError:
                continue
        
        return None
    
    def _get_page_with_requests(self, url: str) -> Optional[BeautifulSoup]:
        """requests를 사용하여 페이지 가져오기 (빠른 방법)"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.warning(f"requests로 페이지 가져오기 실패: {e}")
            return None
    
    def _extract_contest_info_new_structure(self, item) -> Optional[Dict]:
        """새로운 HTML 구조에 맞는 정보 추출"""
        try:
            # 다양한 제목 선택자 시도
            title_selectors = [
                ".tit a", ".title a", "h3 a", "h4 a", 
                ".subject a", ".contest-title a", "a[href*='?c=find&']"
            ]
            
            title_element = None
            for selector in title_selectors:
                title_element = item.select_one(selector)
                if title_element:
                    break
            
            if not title_element:
                # 텍스트만 있는 경우
                title_text = item.get_text(strip=True)
                if len(title_text) > 10:  # 최소 길이 체크
                    # 링크 찾기
                    link_element = item.select_one("a[href]")
                    if link_element:
                        return {
                            "제목": title_text[:100],  # 제목 길이 제한
                            "주최": "주최자 정보 없음",
                            "기간": "기간 정보 없음",
                            "마감일": None,
                            "링크": urljoin(self.base_url, link_element.get('href', ''))
                        }
                return None
            
            title = title_element.get_text(strip=True)
            href = title_element.get('href', '')
            
            # URL 정규화
            if href.startswith('http'):
                url = href
            else:
                url = urljoin(self.base_url, href)
            
            # 주최자 정보 추출
            host_selectors = [".organ", ".host", ".organizer", ".company"]
            host = "주최자 정보 없음"
            
            for selector in host_selectors:
                host_element = item.select_one(selector)
                if host_element:
                    host = host_element.get_text(strip=True)
                    break
            
            # 기간 정보 추출 - 더 많은 선택자 시도
            period_selectors = [".day", ".period", ".date", ".deadline", ".time", ".dday"]
            period = "기간 정보 없음"
            deadline = None
            
            # 전체 텍스트에서도 날짜 찾기
            full_text = item.get_text(strip=True)
            deadline = self._extract_deadline(full_text)
            
            for selector in period_selectors:
                period_element = item.select_one(selector)
                if period_element:
                    period_text = period_element.get_text(strip=True)
                    if period_text:
                        period = period_text
                        # 더 정확한 마감일 추출 시도
                        extracted_deadline = self._extract_deadline(period_text)
                        if extracted_deadline:
                            deadline = extracted_deadline
                        break
            
            # 디버깅 로그 추가
            if deadline:
                logger.debug(f"추출된 마감일: {deadline.date()} - {title[:50]}")
            else:
                logger.debug(f"마감일 없음: {title[:50]} - 기간: {period}")
            
            # 상금 정보 추출 - 1등 상금 우선
            prize = "상금 정보 없음"
            
            # 1. 특정 위치의 1등 상금 찾기 (XPath 기반)
            # li[7]/span 위치의 상금 정보 (1등 상금)
            prize_elements = item.select("li span")
            if len(prize_elements) >= 7:
                first_prize_element = prize_elements[6]  # 7번째 요소 (0-based index)
                prize_text = first_prize_element.get_text(strip=True)
                if prize_text and any(char in prize_text for char in ['원', '만', '억', '$']):
                    prize = f"1등: {prize_text}"
            
            # 2. 일반적인 상금 선택자들
            if prize == "상금 정보 없음":
                prize_selectors = [".prize", ".reward", ".money", ".won", ".award"]
                for selector in prize_selectors:
                    prize_element = item.select_one(selector)
                    if prize_element:
                        prize_text = prize_element.get_text(strip=True)
                        if prize_text and any(char in prize_text for char in ['원', '만', '억', '$']):
                            prize = prize_text
                            break
            
            # 3. 전체 텍스트에서 1등 상금 패턴 찾기
            if prize == "상금 정보 없음":
                first_prize_patterns = [
                    r'1등\s*:?\s*(\d+(?:,\d+)*(?:만|억)?원?)',
                    r'대상\s*:?\s*(\d+(?:,\d+)*(?:만|억)?원?)',
                    r'최우수상\s*:?\s*(\d+(?:,\d+)*(?:만|억)?원?)',
                    r'금상\s*:?\s*(\d+(?:,\d+)*(?:만|억)?원?)',
                ]
                
                for pattern in first_prize_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        prize = f"1등: {match.group(1)}"
                        break
            
            # 4. 일반적인 상금 패턴 찾기
            if prize == "상금 정보 없음":
                general_prize_patterns = [
                    r'상금\s*:?\s*(\d+(?:,\d+)*(?:만|억)?원?)',
                    r'총\s*상금\s*(\d+(?:,\d+)*(?:만|억)?원?)',
                    r'(\d+(?:,\d+)*)\s*만원',
                    r'(\d+(?:,\d+)*)\s*억원',
                ]
                
                for pattern in general_prize_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        prize = match.group(0)
                        break
            
            return {
                "제목": title,
                "주최": host,
                "기간": period,
                "마감일": deadline.date() if deadline else None,
                "상금": prize,
                "링크": url
            }
            
        except Exception as e:
            logger.debug(f"공모전 정보 추출 실패: {e}")
            return None
    
    def _wait_for_page_load(self):
        """페이지 로딩 완료 대기"""
        try:
            # JavaScript 실행 완료 대기
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 추가 대기 (동적 콘텐츠 로딩)
            time.sleep(2)
            
            # 공모전 목록이 있는지 확인
            selectors_to_check = [
                "ul.list", ".list", ".contest_list", 
                "[class*='list']", "[class*='item']"
            ]
            
            for selector in selectors_to_check:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"페이지 로딩 대기 중 오류: {e}")
            return False
    
    def crawl(self, keyword="공공데이터", max_pages=5, from_date=None, to_date=None) -> pd.DataFrame:
        """공모전 정보 크롤링 - 개선된 버전"""
        
        # 먼저 requests로 시도
        logger.info("requests를 사용하여 크롤링을 시도합니다...")
        df_requests = self._crawl_with_requests(keyword, max_pages, from_date, to_date)
        
        if not df_requests.empty:
            logger.info(f"requests로 {len(df_requests)}개 공모전을 수집했습니다.")
            return df_requests
        
        # requests 실패 시 Selenium 사용
        logger.info("Selenium을 사용하여 크롤링을 시도합니다...")
        return self._crawl_with_selenium(keyword, max_pages, from_date, to_date)
    
    def _crawl_with_requests(self, keyword, max_pages, from_date, to_date) -> pd.DataFrame:
        """requests를 사용한 크롤링 (빠른 방법)"""
        results = []
        seen_urls = set()
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.wevity.com/?c=find&s=1&gp={page}&sp=contents&sw={keyword}"
                
                soup = self._get_page_with_requests(url)
                if not soup:
                    continue
                
                # 공모전 목록 찾기
                items = self._find_contest_items(soup)
                
                if not items:
                    logger.warning(f"페이지 {page}: 공모전 목록을 찾을 수 없습니다.")
                    continue
                
                page_count = 0
                for item in items:
                    contest_info = self._extract_contest_info_new_structure(item)
                    
                    if not contest_info or contest_info['링크'] in seen_urls:
                        continue
                    
                    seen_urls.add(contest_info['링크'])
                    
                    # 날짜 필터링
                    if self._filter_by_date(contest_info, from_date, to_date):
                        results.append(contest_info)
                        page_count += 1
                
                logger.info(f"페이지 {page}: {page_count}개 공모전 수집")
                
                if page_count == 0 and page > 1:
                    break
                    
                time.sleep(1)  # 요청 간격
                
        except Exception as e:
            logger.error(f"requests 크롤링 중 오류: {e}")
        
        return pd.DataFrame(results)
    
    def _crawl_with_selenium(self, keyword, max_pages, from_date, to_date) -> pd.DataFrame:
        """Selenium을 사용한 크롤링 (백업 방법)"""
        if not self._setup_driver():
            return pd.DataFrame()
        
        results = []
        seen_urls = set()
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://www.wevity.com/?c=find&s=1&gp={page}&sp=contents&sw={keyword}"
                logger.info(f"페이지 {page} 크롤링 중: {url}")
                
                self.driver.get(url)
                
                if not self._wait_for_page_load():
                    logger.warning(f"페이지 {page} 로딩 실패")
                    continue
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                items = self._find_contest_items(soup)
                
                if not items:
                    logger.warning(f"페이지 {page}: 공모전 목록을 찾을 수 없습니다.")
                    continue
                
                page_count = 0
                for item in items:
                    contest_info = self._extract_contest_info_new_structure(item)
                    
                    if not contest_info or contest_info['링크'] in seen_urls:
                        continue
                    
                    seen_urls.add(contest_info['링크'])
                    
                    if self._filter_by_date(contest_info, from_date, to_date):
                        results.append(contest_info)
                        page_count += 1
                
                logger.info(f"페이지 {page}: {page_count}개 공모전 수집")
                
                if page_count == 0 and page > 1:
                    break
                    
        except Exception as e:
            logger.error(f"Selenium 크롤링 중 오류: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return pd.DataFrame(results)
    
    def _find_contest_items(self, soup):
        """공모전 아이템 찾기 - 다양한 선택자 시도"""
        selectors = [
            "ul.list li",
            ".list li", 
            ".contest_list li",
            ".board_list tr",
            "tr",
            ".item",
            "div[class*='item']",
            "div[class*='contest']",
            "li[class*='list']"
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            # 유효한 아이템 수 체크 (헤더 제외)
            valid_items = [item for item in items if self._is_valid_contest_item(item)]
            
            if len(valid_items) > 0:
                logger.info(f"선택자 '{selector}': {len(valid_items)}개 유효한 아이템 발견")
                return valid_items
        
        return []
    
    def _is_valid_contest_item(self, item):
        """유효한 공모전 아이템인지 확인"""
        text = item.get_text(strip=True)
        
        # 너무 짧은 텍스트는 제외
        if len(text) < 10:
            return False
        
        # 헤더나 광고 요소 제외
        classes = item.get('class', [])
        if any(cls in ['header', 'top', 'ad', 'banner', 'notice'] for cls in classes):
            return False
        
        # 링크가 있는지 확인
        if not item.select_one('a[href]'):
            return False
        
        return True
    
    def _filter_by_date(self, contest_info, from_date, to_date):
        """날짜 필터링 및 불필요한 공모전 제외"""
        deadline = contest_info['마감일']
        today = datetime.now().date()
        title = contest_info['제목'][:50]
        full_title = contest_info['제목'].lower()
        
        # 1. 불필요한 키워드가 포함된 공모전 제외
        exclude_keywords = [
            '모집', '채용', '무료', '멘토링', 'special', '스페셜',
            '교육', '강의', '세미나', '워크샵', '설명회', '상담',
            '지원자', '참가자', '수강생', '인턴', '아르바이트',
            '봉사', '자원봉사', '기부', '후원', '협찬'
        ]
        
        for keyword in exclude_keywords:
            if keyword in full_title:
                logger.debug(f"제외 키워드 '{keyword}'로 인해 제외: {title}")
                return False
        
        # 2. 마감일이 있는 경우
        if deadline:
            # 마감일이 오늘보다 이전이면 제외 (마감된 공모전)
            if deadline < today:
                logger.debug(f"마감일 지남으로 제외: {deadline} - {title}")
                return False
            
            # 사용자가 설정한 날짜 범위 체크
            if from_date and deadline < from_date:
                logger.debug(f"시작일 이전으로 제외: {deadline} - {title}")
                return False
            if to_date and deadline > to_date:
                logger.debug(f"종료일 이후로 제외: {deadline} - {title}")
                return False
            
            logger.debug(f"날짜 필터 통과: {deadline} - {title}")
        else:
            # 마감일이 없는 경우 - 기간 텍스트에서 "마감" 키워드 체크
            period_text = contest_info.get('기간', '').lower()
            if any(keyword in period_text for keyword in ['마감', '종료', '완료']):
                logger.debug(f"마감 키워드로 제외: {period_text} - {title}")
                return False
            
            logger.debug(f"마감일 없음으로 포함: {title}")
        
        return True
    
    def __del__(self):
        """소멸자"""
        if self.driver:
            self.driver.quit()

# 편의 함수
def crawl_wevity(keyword="공공데이터", max_pages=5, from_date=None, to_date=None) -> pd.DataFrame:
    """Wevity 공모전 크롤링 편의 함수"""
    crawler = WevityCrawler()
    try:
        return crawler.crawl(keyword, max_pages, from_date, to_date)
    except Exception as e:
        logger.error(f"크롤링 실패: {e}")
        return pd.DataFrame()

# 테스트 함수
def test_crawler():
    """크롤러 테스트"""
    print("🧪 Wevity 크롤러 테스트 시작...")
    
    df = crawl_wevity(keyword="공공데이터", max_pages=2)
    
    if df.empty:
        print("❌ 크롤링 결과가 없습니다.")
    else:
        print(f"✅ {len(df)}개의 공모전을 수집했습니다.")
        print("\n📋 수집된 데이터 샘플:")
        print(df.head().to_string())

if __name__ == "__main__":
    test_crawler()