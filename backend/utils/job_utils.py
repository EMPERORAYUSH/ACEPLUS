import os
import time
import traceback
from queue import Queue
import json
import generate

JOB_QUEUE = Queue()
JOB_RESULTS = {}
JOB_STATUS = {}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def cleanup_old_files(upload_folder):
    """Delete files older than 24 hours"""
    current_time = time.time()
    one_day = 24 * 60 * 60

    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        # Get file creation time
        file_time = os.path.getctime(filepath)
        if current_time - file_time > one_day:
            try:
                os.remove(filepath)
                print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")

def process_images_job(job_id, image_paths):
    try:
        print(f"\nStarting job {job_id} for {len(image_paths)} images")
        JOB_STATUS[job_id] = {
            "status": "processing",
            "total": 0,
            "completed": 0,
            "start_time": time.time()
        }
        print(f"Processing {len(image_paths)} images...")

        try:
            questions = []
            print("\nStarting image analysis stream...")
            for update in generate.analyze_images(image_paths):
                print(f"\nReceived update: {json.dumps(update, indent=2)}")

                if update["type"] == "total":
                    JOB_STATUS[job_id]["total"] = update["count"]
                    print(f"Updated total questions count: {update['count']}")
                elif update["type"] == "progress":
                    JOB_STATUS[job_id]["completed"] = update["count"]
                    print(f"Updated completed questions count: {update['count']}")
                elif update["type"] == "result":
                    questions = update["questions"]
                    print(f"Received final questions: {len(questions)}")
                    print("Questions structure:")
                    print(json.dumps(questions, indent=2))
                elif update["type"] == "error":
                    print(f"Received error update: {update['message']}")
                    raise Exception(update["message"])

            if questions:
                print(f"\nJob completed successfully with {len(questions)} questions")
                JOB_RESULTS[job_id] = questions
                JOB_STATUS[job_id]["status"] = "completed"
                # Ensure final counts are accurate
                if JOB_STATUS[job_id]["total"] == 0:
                    JOB_STATUS[job_id]["total"] = len(questions)
                JOB_STATUS[job_id]["completed"] = len(questions)
            else:
                print("\nNo questions were extracted")
                JOB_STATUS[job_id]["status"] = "failed"
                JOB_RESULTS[job_id] = "No questions could be extracted from the images"

        except Exception as e:
            print(f"Error processing images: {str(e)}")
            print("Full error details:")
            print(traceback.format_exc())
            JOB_STATUS[job_id]["status"] = "failed"
            JOB_RESULTS[job_id] = str(e)

    except Exception as e:
        print(f"Error in job {job_id}: {str(e)}")
        print("Full error details:")
        print(traceback.format_exc())
        JOB_STATUS[job_id]["status"] = "failed"
        JOB_RESULTS[job_id] = str(e)
    finally:
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - JOB_STATUS[job_id].get("start_time", end_time)

        print(f"\nFinal job status for {job_id}:")
        print(f"Status: {JOB_STATUS[job_id]['status']}")
        print(f"Total: {JOB_STATUS[job_id]['total']}")
        print(f"Completed: {JOB_STATUS[job_id]['completed']}")
        print(f"Processing time: {processing_time:.2f} seconds")

def job_processor():
    while True:
        try:
            job_id, image_paths = JOB_QUEUE.get()
            process_images_job(job_id, image_paths)
        except Exception as e:
            print(f"Error in job processor: {str(e)}")
        finally:
            JOB_QUEUE.task_done()

def cleanup_old_jobs():
    """Clean up jobs older than 1 hour"""
    while True:
        time.sleep(3600)  # Run every hour
        try:
            current_time = time.time()
            for job_id in list(JOB_STATUS.keys()):
                if current_time - JOB_STATUS[job_id].get('start_time', 0) > 3600:
                    JOB_STATUS.pop(job_id, None)
                    JOB_RESULTS.pop(job_id, None)
        except Exception as e:
            print(f"Error in job cleanup: {str(e)}")
