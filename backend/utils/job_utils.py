import os
import time

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def cleanup_old_files(upload_folder):
    current_time = time.time()
    one_hour = 60 * 60

    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        # Get file creation time
        file_time = os.path.getctime(filepath)
        if current_time - file_time > one_hour:
            try:
                os.remove(filepath)
                print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")
