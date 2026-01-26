#!/usr/bin/env python3
"""
Brand Color Consistency Fix Script for EYTGaming

This script helps identify and fix brand color inconsistencies across the codebase.
It searches for old color values and provides a report of files that need updating.
"""

import os
import re
from pathlib import Path

# Define the correct EYT brand colors
CORRECT_COLORS = {
    'primary': '#b91c1c',
    'primary_dark': '#991b1b', 
    'primary_light': '#dc2626'
}

# Define incorrect colors to look for
INCORRECT_COLORS = [
    '#ef4444',  # Bright red that was incorrectly used
    '#3b82f6',  # Blue that shouldn't be used
    '#007bff',  # Bootstrap blue
    '#135bec',  # Another blue variant
]

def scan_file(file_path):
    """Scan a file for incorrect color usage."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for line_num, line in enumerate(content.split('\n'), 1):
            for incorrect_color in INCORRECT_COLORS:
                if incorrect_color.lower() in line.lower():
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'color': incorrect_color,
                        'content': line.strip()
                    })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return issues

def scan_directory(directory, extensions=None):
    """Scan directory for files with brand color issues."""
    if extensions is None:
        extensions = ['.css', '.html', '.js', '.py']
    
    all_issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        skip_dirs = ['.git', '__pycache__', 'node_modules', '.pytest_cache', 'venv']
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                issues = scan_file(file_path)
                all_issues.extend(issues)
    
    return all_issues

def generate_report(issues):
    """Generate a report of brand color issues."""
    if not issues:
        print("✅ No brand color inconsistencies found!")
        return
    
    print(f"🔍 Found {len(issues)} brand color inconsistencies:")
    print("=" * 60)
    
    # Group by file
    files_with_issues = {}
    for issue in issues:
        file_path = issue['file']
        if file_path not in files_with_issues:
            files_with_issues[file_path] = []
        files_with_issues[file_path].append(issue)
    
    for file_path, file_issues in files_with_issues.items():
        print(f"\n📁 {file_path}")
        print("-" * 40)
        
        for issue in file_issues:
            print(f"  Line {issue['line']}: {issue['color']}")
            print(f"    {issue['content']}")
        
        print(f"  → Should use: {CORRECT_COLORS['primary']} (EYT Red)")

def main():
    """Main function to run the brand color consistency check."""
    print("EYTGaming Brand Color Consistency Checker")
    print("=" * 50)
    
    # Scan the current directory
    current_dir = Path.cwd()
    print(f"Scanning: {current_dir}")
    
    # Scan for issues
    issues = scan_directory(current_dir)
    
    # Generate report
    generate_report(issues)
    
    if issues:
        print("\n" + "=" * 60)
        print("🔧 RECOMMENDED ACTIONS:")
        print("1. Update the brand-consistency-fix.css file (already created)")
        print("2. Ensure all templates include the brand consistency CSS")
        print("3. Update any hardcoded color values in the files above")
        print("4. Test the changes across different pages")
        print("\n✅ The brand-consistency-fix.css file should override most issues automatically!")
    else:
        print("\n🎉 All brand colors are consistent!")

if __name__ == "__main__":
    main()