#!/usr/bin/env python3
"""
🚀 Convergio Version Management Script
Reads version from VERSION file and generates build info
"""

import os
import subprocess
import json
from pathlib import Path

def get_version():
    """Read version from VERSION file"""
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"

def get_build_number():
    """Generate build number from git commit"""
    try:
        # Get short commit hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # Get commit count
        commit_count = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        return f"{commit_count}-{commit_hash}"
    except:
        return "dev-build"

def get_git_info():
    """Get additional git information"""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        is_dirty = subprocess.call(
            ["git", "diff", "--quiet"],
            stderr=subprocess.DEVNULL
        ) != 0
        
        return {
            "branch": branch,
            "dirty": is_dirty
        }
    except:
        return {
            "branch": "unknown",
            "dirty": False
        }

def main():
    """Main function to output version info"""
    version = get_version()
    build_number = get_build_number()
    git_info = get_git_info()
    
    version_info = {
        "version": version,
        "build_number": build_number,
        "git_branch": git_info["branch"],
        "git_dirty": git_info["dirty"],
        "full_version": f"{version}+{build_number}"
    }
    
    # Output as JSON for easy parsing
    print(json.dumps(version_info, indent=2))
    
    return version_info

if __name__ == "__main__":
    main()