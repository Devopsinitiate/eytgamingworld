#!/usr/bin/env python3
"""
Update PBT Status Tool for Tournament Detail UI Enhancement

This script updates the status of Property-Based Tests in the tasks.md file.
"""

import os
import re
from datetime import datetime

def update_pbt_status(task_file, subtask_title, status, details=None):
    """
    Update the PBT status in the tasks.md file
    
    Args:
        task_file (str): Path to the tasks.md file
        subtask_title (str): Title of the subtask to update
        status (str): New status ('passed', 'failed', 'not started')
        details (str): Optional details about the test result
    """
    if not os.path.exists(task_file):
        print(f"Error: Task file {task_file} not found")
        return False
    
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try XML format first
    pattern = rf'(<task title="{re.escape(subtask_title)}">\s*\n\s*Status:\s*)[^<]+(.*?</task>)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # XML format found
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if status == 'passed':
            status_text = f"passed - {timestamp}"
        elif status == 'failed':
            if details:
                status_text = f"failed - {timestamp}\n\nFailure Details:\n{details}"
            else:
                status_text = f"failed - {timestamp}"
        else:
            status_text = status
        
        # Replace the status
        new_content = content.replace(
            match.group(0),
            f"{match.group(1)}{status_text}{match.group(2)}"
        )
        
        # Write back to file
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Updated PBT status for '{subtask_title}' to '{status}'")
        return True
    
    # Try checkbox format
    checkbox_pattern = rf'(- \[[ x]\] {re.escape(subtask_title)})'
    checkbox_match = re.search(checkbox_pattern, content)
    
    if checkbox_match:
        # Update checkbox based on status
        if status == 'passed':
            new_checkbox = f"- [x] {subtask_title}"
        else:
            new_checkbox = f"- [ ] {subtask_title}"
        
        new_content = content.replace(checkbox_match.group(0), new_checkbox)
        
        # Write back to file
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Updated PBT status for '{subtask_title}' to '{status}' (checkbox format)")
        return True
    
    print(f"Error: Subtask '{subtask_title}' not found in {task_file}")
    return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python update_pbt_status.py <subtask_title> <status> [details]")
        sys.exit(1)
    
    task_file = ".kiro/specs/tournament-detail-ui-enhancement/tasks.md"
    subtask_title = sys.argv[1]
    status = sys.argv[2]
    details = sys.argv[3] if len(sys.argv) > 3 else None
    
    update_pbt_status(task_file, subtask_title, status, details)