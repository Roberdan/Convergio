#!/usr/bin/env python3
"""
Integration Test Runner
Esegue tutti i test di integrazione dalla cartella tests/integration
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(test_file):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_file.name}")
    print(f"{'='*60}")
    
    try:
        # Set up environment with proper PYTHONPATH
        env = os.environ.copy()
        project_root = Path(__file__).parent.parent
        backend_path = project_root / "backend"
        
        # Add backend to PYTHONPATH
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{backend_path}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = str(backend_path)
        
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=False, 
                              text=True,
                              env=env)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file.name}: {e}")
        return False

def main():
    """Run all integration tests"""
    
    integration_dir = Path(__file__).parent / "integration"
    
    # Priorità ai test standalone (non richiedono dipendenze backend)
    standalone_tests = [
        "test_agents.py"
    ]
    
    # Test che richiedono dipendenze backend (opzionali)
    backend_dependent_tests = [
        "test_ali_coordination.py",
        "test_multiagent_conversations.py", 
        "test_performance_optimization.py",
        "test_performance_simple.py"
    ]
    
    # Trova tutti i test disponibili
    all_test_files = list(integration_dir.glob("test_*.py"))
    available_tests = [f.name for f in all_test_files]
    
    # Esegui test standalone prima
    print(f"🚀 Running standalone tests (no backend dependencies required)")
    standalone_results = {}
    for test_name in standalone_tests:
        if test_name in available_tests:
            test_file = integration_dir / test_name
            success = run_test(test_file)
            standalone_results[test_name] = success
    
    # Esegui test dipendenti dal backend
    print(f"\n🔗 Running backend-dependent tests (optional)")
    backend_results = {}
    for test_name in backend_dependent_tests:
        if test_name in available_tests:
            test_file = integration_dir / test_name
            success = run_test(test_file)
            backend_results[test_name] = success
    
    # Combina risultati
    results = {**standalone_results, **backend_results}
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    
    standalone_passed = sum(1 for success in standalone_results.values() if success)
    standalone_total = len(standalone_results)
    
    backend_passed = sum(1 for success in backend_results.values() if success)
    backend_total = len(backend_results)
    
    print("🚀 Standalone Tests (Required):")
    for test_name, success in standalone_results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    if backend_results:
        print("\n🔗 Backend-Dependent Tests (Optional):")
        for test_name, success in backend_results.items():
            status = "✅ PASSED" if success else "❌ FAILED (optional)"
            print(f"   {test_name}: {status}")
    
    print(f"\nStandalone: {standalone_passed}/{standalone_total} tests passed")
    if backend_total > 0:
        print(f"Backend-dependent: {backend_passed}/{backend_total} tests passed")
    
    # Success se tutti i test standalone passano
    if standalone_passed == standalone_total:
        print("🎉 All required tests passed!")
        if backend_passed < backend_total:
            print("💡 Some optional backend-dependent tests failed (install backend dependencies to fix)")
        return True
    else:
        print("❌ Some required standalone tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)