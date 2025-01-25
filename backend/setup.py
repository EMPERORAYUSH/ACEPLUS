import os
import json
import subprocess
import sys

def install_requirements():
    """Install required packages from requirements.txt"""
    try:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        sys.exit(1)

def create_json_files():
    """Create necessary JSON files with empty structures in data directory"""
    json_files = {
        'students.json': [],
        'active_tests.json': {'tests': []},
        'class10_students.json': [],
        'teachers.json': {}
    }
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print("✅ Created data directory")
    
    print("\nCreating JSON files...")
    for filename, initial_data in json_files.items():
        file_path = os.path.join(data_dir, filename)
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=4)
                print(f"✅ Created {filename}")
            else:
                print(f"ℹ️ {filename} already exists, skipping")
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")

def create_directories():
    """Create necessary directories"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    directories = [
        os.path.join(base_dir, 'data', 'reports'),
        os.path.join(base_dir, 'pdfs'),
        os.path.join(base_dir, 'uploads')
    ]
    
    print("\nCreating directories...")
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✅ Created directory: {directory}")
            else:
                print(f"ℹ️ Directory {directory} already exists, skipping")
        except Exception as e:
            print(f"❌ Error creating directory {directory}: {e}")

def main():
    # Get the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script's directory
    os.chdir(script_dir)
    
    print("Starting setup process...\n")
    
    # Install requirements
    install_requirements()
    
    # Create necessary files and directories
    create_json_files()
    create_directories()
    
    print("\n✨ Setup completed successfully!")
    print("\n Now you can start backend server by running: `npm run start-backend`!")

if __name__ == "__main__":
    main() 