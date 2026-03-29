"""
Monitoring Setup Script
Configures Sentry, logging, and health checks

Run after deployment to set up monitoring infrastructure
"""

import os
from pathlib import Path

def setup_sentry():
    """Generate Sentry configuration"""
    sentry_config = """
# Add to backend/main.py (top of file)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    environment=os.getenv('ENV', 'production'),
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of profiles
    integrations=[
        FastApiIntegration(),
    ],
)

# Add to frontend/src/main.tsx
import * as Sentry from "@sentry/react"

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay(),
  ],
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
})
"""
    print("📝 Sentry Configuration:")
    print(sentry_config)
    
    print("\n📦 Install Sentry:")
    print("Backend: pip install sentry-sdk[fastapi]")
    print("Frontend: npm install @sentry/react")
    
    print("\n🔑 Get Sentry DSN:")
    print("1. Sign up: https://sentry.io")
    print("2. Create project: 'foodberg'")
    print("3. Copy DSN from settings")
    print("4. Add to .env files:")
    print("   Backend: SENTRY_DSN=your_dsn")
    print("   Frontend: VITE_SENTRY_DSN=your_dsn")

def setup_uptime_robot():
    """Instructions for Uptime Robot setup"""
    print("\n🤖 Uptime Robot Setup:")
    print("=" * 60)
    print("1. Sign up: https://uptimerobot.com (FREE)")
    print("\n2. Add Frontend Monitor:")
    print("   Type: HTTP(s)")
    print("   Name: Foodberg Frontend")
    print("   URL: https://foodberg.org")
    print("   Interval: 5 minutes")
    print("\n3. Add Backend Monitor:")
    print("   Type: HTTP(s)")
    print("   Name: Foodberg API")
    print("   URL: https://api.foodberg.org/api/health")
    print("   Interval: 5 minutes")
    print("\n4. Configure Alerts:")
    print("   Email: your_email@example.com")
    print("   Alert when: Monitor goes DOWN")
    print("   Alert when: Monitor goes UP (recovery)")

def setup_plausible():
    """Instructions for Plausible Analytics"""
    print("\n📊 Plausible Analytics Setup (Optional - $9/month):")
    print("=" * 60)
    print("1. Sign up: https://plausible.io")
    print("\n2. Add site: foodberg.org")
    print("\n3. Add script to frontend/index.html (before </head>):")
    print('   <script defer data-domain="foodberg.org" src="https://plausible.io/js/script.js"></script>')
    print("\n4. Or self-host (FREE):")
    print("   docker run -d -p 8001:8000 -v plausible-db:/var/lib/postgresql/data plausible/analytics")

def create_health_check_script():
    """Create automated health check script"""
    script = """#!/usr/bin/env python3
\"\"\"
Health Check Script
Runs periodic checks on Foodberg services

Run via cron: */5 * * * * python health_check.py
\"\"\"

import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def check_frontend():
    try:
        response = requests.get('https://foodberg.org', timeout=10)
        return response.status_code == 200
    except:
        return False

def check_backend():
    try:
        response = requests.get('https://api.foodberg.org/api/health', timeout=10)
        return response.status_code == 200 and response.json()['status'] == 'healthy'
    except:
        return False

def check_websocket():
    try:
        import websocket
        ws = websocket.create_connection('wss://api.foodberg.org/ws/prices')
        ws.close()
        return True
    except:
        return False

def send_alert(service, status):
    msg = MIMEText(f'{service} is {status} at {datetime.now()}')
    msg['Subject'] = f'⚠️ Foodberg Alert: {service} {status}'
    msg['From'] = 'alerts@foodberg.org'
    msg['To'] = 'admin@foodberg.org'
    
    # Configure SMTP
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # server.login('alerts@foodberg.org', 'password')
    # server.send_message(msg)
    # server.quit()
    
    print(f"Alert: {msg['Subject']}")

def main():
    checks = {
        'Frontend': check_frontend(),
        'Backend API': check_backend(),
        'WebSocket': check_websocket()
    }
    
    for service, healthy in checks.items():
        if not healthy:
            send_alert(service, 'DOWN')
        print(f'{service}: {'✅ UP' if healthy else '❌ DOWN'}')

if __name__ == '__main__':
    main()
"""
    
    output_path = Path(__file__).parent / 'health_check.py'
    with open(output_path, 'w') as f:
        f.write(script)
    
    print(f"\n✅ Created: {output_path}")
    print("\n🔄 Set up cron job (Linux/Mac):")
    print("   crontab -e")
    print("   */5 * * * * cd /path/to/foodberg/backend/monitoring && python health_check.py")

def main():
    print("=" * 60)
    print("  FOODBERG MONITORING SETUP")
    print("=" * 60)
    
    setup_sentry()
    print("\n")
    setup_uptime_robot()
    print("\n")
    setup_plausible()
    print("\n")
    create_health_check_script()
    
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)
    print("\n✅ Next Steps:")
    print("1. Sign up for Sentry and Uptime Robot (both FREE)")
    print("2. Add API keys to environment variables")
    print("3. Deploy updated code")
    print("4. Verify monitoring dashboards")
    print("\n📊 Monitor at:")
    print("   Sentry: https://sentry.io/organizations/your-org/projects/foodberg/")
    print("   Uptime Robot: https://uptimerobot.com/dashboard")
    print("   Render Metrics: https://dashboard.render.com")

if __name__ == "__main__":
    main()

