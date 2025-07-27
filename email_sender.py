# email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import streamlit as st

# 환경변수 로드
load_dotenv()

def create_email_content(df):
    """DataFrame을 HTML 이메일 내용으로 변환"""
    if df.empty:
        return "<p>조건에 맞는 공모전이 없습니다.</p>"
    
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .header {{ 
                background: linear-gradient(-10deg, rgba(226,205,247, 0.8), rgba(202,202,202, 0.6));
                padding: 40px 30px;
                text-align: center;
                border-bottom: 3px solid rgba(224,217,236, 0.3);
            }}
            .header h1 {{ 
                font-size: 28px; 
                color: #2c3e50; 
                margin-bottom: 15px;
                font-weight: 700;
            }}
            .header-stats {{ 
                display: flex; 
                justify-content: center; 
                gap: 30px; 
                margin-top: 20px;
                flex-wrap: wrap;
            }}
            .stat-item {{ 
                background: rgba(255,255,255,0.9);
                padding: 15px 25px;
                border-radius: 50px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .stat-number {{ 
                font-size: 24px; 
                font-weight: bold; 
                color: #8224e3; 
                display: block;
            }}
            .stat-label {{ 
                font-size: 12px; 
                color: #666; 
                margin-top: 5px;
            }}
            .content {{ padding: 30px; }}
            .contest-card {{ 
                background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
                border: 1px solid rgba(224,217,236, 0.2);
                margin: 20px 0; 
                padding: 25px; 
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
                transition: transform 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .contest-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: linear-gradient(to bottom, #8224e3, #a058e9);
            }}
            .contest-title {{ 
                font-size: 20px; 
                font-weight: 700; 
                color: #2c3e50; 
                margin-bottom: 15px;
                line-height: 1.4;
                padding-left: 15px;
            }}
            .contest-info {{ 
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
                padding-left: 15px;
            }}
            .info-item {{ 
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 0;
            }}
            .info-icon {{ 
                font-size: 16px;
                width: 20px;
                text-align: center;
            }}
            .info-label {{ 
                font-weight: 600; 
                color: #555;
                min-width: 50px;
            }}
            .info-value {{ 
                color: #333;
                flex: 1;
            }}
            .contest-link {{ 
                display: inline-block;
                background: linear-gradient(135deg, #8224e3, #a058e9);
                color: white !important;
                text-decoration: none;
                padding: 12px 25px;
                border-radius: 25px;
                font-weight: 600;
                margin: 15px 0 0 15px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(130, 36, 227, 0.3);
            }}
            .contest-link:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(130, 36, 227, 0.4);
            }}
            .footer {{ 
                background: linear-gradient(-10deg, rgba(44, 62, 80, 0.9), rgba(52, 73, 94, 0.9));
                color: white;
                padding: 30px;
                text-align: center;
                margin-top: 30px;
            }}
            .footer p {{ 
                margin: 10px 0;
                opacity: 0.9;
            }}
            .footer a {{ 
                color: #a058e9 !important;
                text-decoration: none;
                font-weight: 600;
            }}
            @media (max-width: 600px) {{
                .contest-info {{ grid-template-columns: 1fr; }}
                .header-stats {{ flex-direction: column; align-items: center; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 공공데이터 공모전 뉴스레터</h1>
                <div class="header-stats">
                    <div class="stat-item">
                        <span class="stat-number">{len(df)}</span>
                        <div class="stat-label">총 공모전</div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{datetime.now().strftime('%m.%d')}</span>
                        <div class="stat-label">발송일</div>
                    </div>
                </div>
            </div>
            <div class="content">
    """
    
    for _, row in df.iterrows():
        deadline_str = row['마감일'].strftime('%Y.%m.%d') if pd.notna(row['마감일']) else '마감일 미정'
        period_info = row.get('기간', row.get('요약', '기간 정보 없음'))
        
        html_content += f"""
        <div class="contest-card">
            <div class="contest-title">{row['제목']}</div>
            <div class="contest-info">
                <div class="info-item">
                    <span class="info-icon">🏢</span>
                    <span class="info-label">주최</span>
                    <span class="info-value">{row['주최']}</span>
                </div>
                <div class="info-item">
                    <span class="info-icon">📅</span>
                    <span class="info-label">마감일</span>
                    <span class="info-value">{deadline_str}</span>
                </div>
                <div class="info-item" style="grid-column: 1 / -1;">
                    <span class="info-icon">⏰</span>
                    <span class="info-label">기간</span>
                    <span class="info-value">{period_info}</span>
                </div>
            </div>
            <a href="{row['링크']}" class="contest-link" target="_blank">공모전 바로가기 →</a>
        </div>
        """
    
    html_content += f"""
            </div>
            <div class="footer">
                <p>📧 이 이메일은 Wevity 공모전 크롤러를 통해 자동 발송되었습니다.</p>
                <p>더 많은 공모전 정보는 <a href="https://www.wevity.com">Wevity</a>에서 확인하세요.</p>
                <p style="font-size: 12px; opacity: 0.7; margin-top: 15px;">
                    발송시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_email(df, receiver_email):
    """공모전 데이터를 이메일로 발송"""
    try:
        # 환경변수에서 이메일 설정 가져오기
        smtp_server = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('EMAIL_PORT', '587'))
        sender_email = os.getenv('EMAIL')
        sender_password = os.getenv('PASSWORD')
        sender_name = os.getenv('SENDER_NAME', '공모전 알리미')
        
        if not all([sender_email, sender_password]):
            raise ValueError("이메일 설정이 완료되지 않았습니다. .env 파일을 확인해주세요.")
        
        # 이메일 메시지 생성
        message = MIMEMultipart('alternative')
        message['From'] = f"{sender_name} <{sender_email}>"
        message['To'] = receiver_email
        message['Subject'] = f"🏆 공공데이터 공모전 뉴스레터 - {datetime.now().strftime('%Y.%m.%d')}"
        
        # HTML 내용 생성
        html_content = create_email_content(df)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # SMTP 서버 연결 및 이메일 발송
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        return True, "이메일이 성공적으로 발송되었습니다."
        
    except Exception as e:
        error_msg = f"이메일 발송 중 오류가 발생했습니다: {str(e)}"
        return False, error_msg

# Streamlit에서 사용할 함수
def send_email_streamlit(df, receiver_email):
    """Streamlit에서 사용하는 이메일 발송 함수"""
    success, message = send_email(df, receiver_email)
    
    if success:
        st.success(f"✅ {message}")
    else:
        st.error(f"❌ {message}")
    
    return success