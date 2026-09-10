#!/usr/bin/env python3
"""
Helper script untuk auto-restart bot di GitHub Actions
"""

import os
import requests
import json
from datetime import datetime

class RestartHelper:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('GITHUB_REPOSITORY')
        self.run_id = os.getenv('GITHUB_RUN_ID')
        self.api_url = f"https://api.github.com/repos/{self.repository}" if self.repository else None
        
    def trigger_restart(self):
        """Trigger workflow restart via GitHub API"""
        if not self.github_token:
            print("⚠️ GITHUB_TOKEN not available, skipping restart")
            return False
        
        if not self.api_url:
            print("⚠️ GITHUB_REPOSITORY not available, skipping restart")
            return False
        
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'TradingBot-RestartHelper'
            }
            
            url = f"{self.api_url}/actions/workflows/trading-bot.yml/dispatches"
            data = {
                'ref': 'main',
                'inputs': {
                    'force_restart': 'true'
                }
            }
            
            print(f"🔄 Triggering restart for {self.repository}...")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 204:
                print(f"✅ Restart triggered successfully at {datetime.now()}")
                return True
            elif response.status_code == 404:
                print(f"❌ Workflow not found - check if trading-bot.yml exists")
                return False
            elif response.status_code == 403:
                print(f" Permission denied - check GITHUB_TOKEN permissions")
                print("   Go to Settings → Actions → General → Workflow permissions")
                print("   Set to 'Read and write permissions'")
                return False
            else:
                print(f"❌ Failed to trigger restart: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(" Request timeout")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Connection error")
            return False
        except Exception as e:
            print(f"❌ Exception in trigger_restart: {e}")
            return False
    
    def log_status(self):
        """Log current status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'run_id': self.run_id,
            'repository': self.repository,
            'action': 'restart_triggered'
        }
        
        os.makedirs('logs', exist_ok=True)
        with open('logs/restart_log.json', 'a') as f:
            f.write(json.dumps(status) + '\n')
        
        print(f"📝 Status logged: {json.dumps(status, indent=2)}")

def main():
    print("=" * 60)
    print("🔄 RESTART HELPER")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    helper = RestartHelper()
    helper.log_status()
    
    success = helper.trigger_restart()
    
    if success:
        print("\n✅ Bot will restart automatically")
        print("ℹ️ Next run should start within 1-2 minutes")
    else:
        print("\n⚠️ Restart failed, will retry on next schedule")
        print("ℹ️ Common issues:")
        print("   - Check Settings → Actions → General → Workflow permissions")
        print("   - Ensure 'Read and write permissions' is selected")
        print("   - Verify trading-bot.yml exists in .github/workflows/")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
