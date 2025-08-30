import os
import time
from datetime import datetime, timedelta

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

def delete_unsubmitted_exams(exam_repo):
    """Delete exams that are not submitted and older than 7 days."""
    # Calculate the cutoff date (7 days ago)
    cutoff_date = datetime.now() - timedelta(days=7)
    
    # For both class 9 and class 10 exams
    for is_class10 in [False, True]:
        # Get the collection for this class
        col = exam_repo._col_by_params(is_class10=is_class10)
        
        # Find unsubmitted exams
        unsubmitted_exams = col.find({"is_submitted": False})
        
        for exam in unsubmitted_exams:
            try:
                # Parse the timestamp string
                exam_timestamp = datetime.strptime(exam["timestamp"], "%Y-%m-%d %H:%M:%S")
                
                # Check if the exam is older than 7 days
                if exam_timestamp < cutoff_date:
                    # Delete the exam
                    exam_repo.delete_exam(exam["exam-id"], is_class10)
                    print(f"Deleted unsubmitted exam: {exam['exam-id']}")
            except Exception as e:
                print(f"Error processing exam {exam.get('exam-id', 'unknown')}: {e}")
