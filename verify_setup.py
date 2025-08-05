#!/usr/bin/env python3
"""
Script to verify the setup is complete and working
"""
import sys
import os
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_python_module(module_path, description):
    """Check if a Python module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {description}: {module_path}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_path} - ERROR: {e}")
        return False

def main():
    print("🔍 Verifying AEO Booster Setup")
    print("=" * 50)
    
    all_good = True
    
    # Check key files
    files_to_check = [
        ("package.json", "React package configuration"),
        ("requirements.txt", "Python dependencies"),
        ("main.py", "FastAPI main application"),
        ("src/components/InputForm.jsx", "React InputForm component"),
        ("src/api/projects.py", "FastAPI projects endpoint"),
        ("src/models/project.py", "Database models"),
        ("src/components/__tests__/InputForm.test.jsx", "React component tests"),
        ("tests/api/test_projects.py", "API tests"),
        ("tailwind.config.js", "Tailwind CSS config"),
        ("README.md", "Project documentation"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False
    
    print("\n🐍 Checking Python modules...")
    python_modules = [
        ("src/models/project.py", "Database models module"),
        ("src/api/projects.py", "Projects API module"),
    ]
    
    for module_path, description in python_modules:
        if not check_python_module(module_path, description):
            all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All checks passed! Setup is complete.")
        print("\n🚀 To get started:")
        print("1. Install dependencies: pip install -r requirements.txt && npm install")
        print("2. Start backend: python start_backend.py")
        print("3. Start frontend: npm start")
        print("4. Visit: http://localhost:3000")
    else:
        print("⚠️  Some files are missing. Please check the setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()