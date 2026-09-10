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
        self.api_url = f"https://api.github.com/repos/{self.repository}"
        
    def trigger_restart(self):
        """Trigger workflow restart via GitHub API"""
        if not self.github_token:
            print("⚠️ GITHUB_TOKEN not available, skipping restart")
            return False
        
        try:
            # Create dispatch event
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Trigger workflow_dispatch
            url = f"{self.api_url}/actions/workflows/trading-bot.yml/dispatches"
            data = {
                'ref': 'main',
                'inputs': {
                    'force_restart': 'true'
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 204:
                print(f"✅ Restart triggered successfully at {datetime.now()}")
                return True
            else:
                print(f"❌ Failed to trigger restart: {response.status_code}")
                print(f"Response: {response.text}")
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
        
        print(f"📝 Status logged: {status}")

def main():
    print("=" * 60)
    print("🔄 RESTART HELPER")
    print("=" * 60)
    
    helper = RestartHelper()
    helper.log_status()
    
    success = helper.trigger_restart()
    
    if success:
        print("✅ Bot will restart automatically")
    else:
        print("⚠️ Restart failed, will retry on next schedule")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
