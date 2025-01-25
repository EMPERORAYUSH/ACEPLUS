import json
import os

def convert_file_to_utf8(file_path):
    try:
        # Try reading with different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = json.load(f)
                break
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue
                
        if content is None:
            print(f"Could not read file {file_path} with any encoding")
            return
            
        # Write back in UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully converted {file_path} to UTF-8")
        
    except Exception as e:
        print(f"Error converting {file_path}: {e}")

def convert_all_lesson_files():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    # Convert lessons.json and lessons10.json
    for file in ['lessons.json', 'lessons10.json']:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            convert_file_to_utf8(file_path)
    
    # Convert individual lesson files
    for folder in ['lessons', 'lessons10']:
        lesson_dir = os.path.join(data_dir, folder)
        if os.path.exists(lesson_dir):
            for subject in os.listdir(lesson_dir):
                subject_dir = os.path.join(lesson_dir, subject)
                if os.path.isdir(subject_dir):
                    for file in os.listdir(subject_dir):
                        if file.endswith('.json'):
                            file_path = os.path.join(subject_dir, file)
                            convert_file_to_utf8(file_path)

if __name__ == '__main__':
    convert_all_lesson_files() 