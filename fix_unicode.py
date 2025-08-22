#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to replace Unicode emoji characters with ASCII alternatives
to fix UnicodeEncodeError on Windows terminals.
"""

import os
import re
from pathlib import Path

# Unicode to ASCII mapping
UNICODE_REPLACEMENTS = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]',
    '🔄': '[REFRESH]',
    '📊': '[CHART]',
    '💰': '[MONEY]',
    '🏎️': '[F1]',
    '🏁': '[RACE]',
    '📈': '[TREND]',
    '🎯': '[TARGET]',
    '🔥': '[HOT]',
    '📦': '[PACKAGE]',
    '📄': '[DOC]',
    '📥': '[DOWNLOAD]',
    '🏆': '[TROPHY]',
    '📱': '[MOBILE]',
    '🎉': '[PARTY]',
    '👋': '[WAVE]',
    '🔪': '[FORCE]',
    '🎛️': '[CONTROL]',
    '🚀': '[ROCKET]',
    '📋': '[CLIPBOARD]',
    '⚙️': '[SETTINGS]',
    'ℹ️': '[INFO]',
    '🔮': '[CRYSTAL]',
    '📝': '[MEMO]',
    '🎪': '[CIRCUS]',
    # Additional Unicode characters found in dashboard files
    '🕒': '[TIME]',
    '🔧': '[TOOL]',
    '🧪': '[TEST]',
    '💡': '[IDEA]',
    '🎲': '[DICE]',
    '🤖': '[ROBOT]',
    '🛑': '[STOP]',
    '🥇': '[GOLD]',
    '🥈': '[SILVER]',
    '🥉': '[BRONZE]'
}

def replace_unicode_in_file(file_path):
    """Replace Unicode characters in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace Unicode characters
        for unicode_char, ascii_replacement in UNICODE_REPLACEMENTS.items():
            content = content.replace(unicode_char, ascii_replacement)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated: {file_path}")
            return True
        else:
            print(f"[INFO] No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files in dashboard directory."""
    print("[INFO] Starting Unicode character replacement...")
    
    # Get dashboard directory
    dashboard_dir = Path(__file__).parent / "dashboard"
    
    if not dashboard_dir.exists():
        print(f"[ERROR] Dashboard directory not found: {dashboard_dir}")
        return
    
    # Find all Python files
    python_files = list(dashboard_dir.glob("*.py"))
    
    if not python_files:
        print(f"[WARNING] No Python files found in {dashboard_dir}")
        return
    
    print(f"[INFO] Found {len(python_files)} Python files to process")
    
    updated_count = 0
    
    for file_path in python_files:
        if replace_unicode_in_file(file_path):
            updated_count += 1
    
    print(f"\n[OK] Processing complete!")
    print(f"[INFO] Files updated: {updated_count}/{len(python_files)}")
    
    if updated_count > 0:
        print("[INFO] Please restart the dashboards to apply changes.")

if __name__ == "__main__":
    main()