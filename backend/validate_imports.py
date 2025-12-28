#!/usr/bin/env python3
"""
Import Path Validation Script for Convergio Backend
Prevents recurring import path issues when switching LLMs
"""

import os
import re
import sys
import glob
from pathlib import Path

class ImportValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.backend_src = Path("src")
        
    def validate_main_py(self):
        """Validate main.py uses only relative imports"""
        main_file = self.backend_src / "main.py"
        if not main_file.exists():
            self.errors.append("❌ main.py not found")
            return
            
        with open(main_file, 'r') as f:
            content = f.read()
            
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for absolute imports of internal modules
            if re.match(r'^\s*from (core|api|agents|models|services)\.', line):
                self.errors.append(f"❌ main.py:{i} - Absolute import should be relative: {line.strip()}")
            
            # Check for missing relative imports
            if re.match(r'^\s*from \.(core|api|agents|models|services)\.', line):
                continue  # This is correct
                
        print("✅ main.py import validation completed")
        
    def validate_models(self):
        """Validate all models have extend_existing"""
        model_files = glob.glob(str(self.backend_src / "models" / "*.py"))
        
        for model_file in model_files:
            if model_file.endswith("__init__.py"):
                continue
                
            with open(model_file, 'r') as f:
                content = f.read()
                
            if '__tablename__' in content and '__table_args__' not in content:
                self.errors.append(f"❌ {model_file} - Missing __table_args__ = {{'extend_existing': True}}")
            elif '__tablename__' in content and 'extend_existing' not in content:
                self.errors.append(f"❌ {model_file} - __table_args__ missing 'extend_existing': True")
                
        print("✅ Model validation completed")
        
    def validate_api_imports(self):
        """Validate API modules use correct relative imports"""
        api_files = glob.glob(str(self.backend_src / "api" / "*.py"))
        api_files.extend(glob.glob(str(self.backend_src / "api" / "*" / "*.py")))
        
        for api_file in api_files:
            if api_file.endswith("__init__.py"):
                continue
                
            with open(api_file, 'r') as f:
                content = f.read()
                
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Check for absolute imports that should be relative
                if re.match(r'^\s*from (core|models|agents)\.', line):
                    self.warnings.append(f"⚠️  {api_file}:{i} - Consider relative import: {line.strip()}")
                    
        print("✅ API import validation completed")
        
    def validate_orchestrator(self):
        """Validate orchestrator has correct import patterns"""
        orchestrator_file = self.backend_src / "agents" / "orchestrator.py"
        if not orchestrator_file.exists():
            self.warnings.append("⚠️  orchestrator.py not found")
            return
            
        with open(orchestrator_file, 'r') as f:
            content = f.read()
            
        # Check for problematic relative imports in orchestrator
        if re.search(r'from \.\.core\.', content):
            self.warnings.append("⚠️  orchestrator.py - Consider absolute imports for core modules")
            
        print("✅ Orchestrator validation completed")
        
    def test_import_functionality(self):
        """Test if main module can be imported"""
        try:
            # Set PYTHONPATH
            current_dir = os.getcwd()
            src_path = os.path.join(current_dir, "src")
            
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
                
            # Try to import main
            try:
                from src.main import app  # noqa: F401
                print("✅ Main module imports successfully")
                return True
            except ImportError as e:
                if "attempted relative import" in str(e):
                    self.errors.append(f"❌ Relative import error: {e}")
                elif "No module named" in str(e):
                    self.errors.append(f"❌ Module not found error: {e}")
                else:
                    self.errors.append(f"❌ Import error: {e}")
                return False
                
        except Exception as e:
            self.errors.append(f"❌ Failed to test imports: {e}")
            return False
            
    def generate_fixes(self):
        """Generate automatic fixes for common issues"""
        fixes = []
        
        # Fix main.py imports
        main_file = self.backend_src / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()
                
            original_content = content
            # Fix absolute imports to relative
            content = re.sub(r'^(\s*)from (core|api|agents|models|services)\.', r'\1from .\2.', content, flags=re.MULTILINE)
            
            if content != original_content:
                fixes.append("sed -i 's/^from \\(core\\|api\\|agents\\|models\\|services\\)\\./from .\\1./g' src/main.py")
                
        # Fix models without extend_existing
        model_files = glob.glob(str(self.backend_src / "models" / "*.py"))
        for model_file in model_files:
            if model_file.endswith("__init__.py"):
                continue
                
            with open(model_file, 'r') as f:
                content = f.read()
                
            if '__tablename__' in content and '__table_args__' not in content:
                fixes.append(f"# Add to {model_file} after __tablename__ line:")
                fixes.append("#     __table_args__ = {'extend_existing': True}")
                
        return fixes
        
    def run_validation(self):
        """Run all validations"""
        print("🔍 Starting Convergio Backend Import Validation...")
        print("=" * 50)
        
        self.validate_main_py()
        self.validate_models()
        self.validate_api_imports()
        self.validate_orchestrator()
        import_success = self.test_import_functionality()
        
        print("\n" + "=" * 50)
        print("📊 VALIDATION RESULTS")
        print("=" * 50)
        
        if self.errors:
            print("🚨 ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")
            
        if self.errors:
            print("\n🔧 SUGGESTED FIXES:")
            fixes = self.generate_fixes()
            for fix in fixes:
                print(f"  {fix}")
                
            print("\n📖 For detailed guidance, see: IMPORT_PATH_CONSISTENCY_GUIDE.md")
            
        success = len(self.errors) == 0 and import_success
        print(f"\n{'✅ VALIDATION PASSED' if success else '❌ VALIDATION FAILED'}")
        return success

def main():
    """Main entry point"""
    if not os.path.exists("src"):
        print("❌ Error: Run this script from the backend/ directory")
        sys.exit(1)
        
    validator = ImportValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()