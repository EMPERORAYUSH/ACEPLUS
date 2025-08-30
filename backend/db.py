import os
import threading
import queue
from datetime import datetime
from pytz import timezone
from typing import Any, Dict, List, Optional, Tuple
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

IST = timezone("Asia/Kolkata")

def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj

def month_key_from_date_str(date_str: str) -> str:
    # date is in 'dd-mm-YYYY'
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except Exception:
        # If format unexpected, fallback to current month
        dt = datetime.now(IST)
    return dt.strftime("%Y-%m")

def current_month_key() -> str:
    return datetime.now(IST).strftime("%Y-%m")

# -----------------------------------------------------------------------------
# Database Client and WriteQueue
# -----------------------------------------------------------------------------

class DatabaseClient:
    """Mongo client wrapper supporting class-wise (9/10) DB segregation."""

    def __init__(self) -> None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set")

        db9_name = os.getenv("MONGODB_DB_CLASS9")
        db10_name = os.getenv("MONGODB_DB_CLASS10")

        if not db9_name or not db10_name:
            raise ValueError(
                "Database names for both classes must be set. "
                "Please define MONGODB_DB_CLASS9 and MONGODB_DB_CLASS10 in your environment."
            )

        self._client = MongoClient(uri)
        self._db9 = self._client[db9_name]
        self._db10 = self._client[db10_name]

    def get_collection(
        self,
        name: str,
        is_class10: Optional[bool] = None,
        standard: Optional[int] = None
    ) -> Collection:
        if is_class10 is not None:
            return (self._db10 if is_class10 else self._db9)[name]
        if standard is not None:
            return (self._db10 if int(standard) == 10 else self._db9)[name]
        # default to class 9 if ambiguous
        return self._db9[name]


class WriteQueue:
    """Threaded 'no-wait' write queue for fire-and-forget operations."""

    def __init__(self, db_client: DatabaseClient, worker_count: int = 1) -> None:
        self.db_client = db_client
        self._q: "queue.Queue[Tuple[str, Tuple, Dict]]" = queue.Queue()
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        for i in range(worker_count):
            t = threading.Thread(target=self._worker, name=f"WriteQueueWorker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def enqueue(self, op_name: str, *args, **kwargs) -> None:
        """Enqueue an operation by name and args; repository methods will interpret."""
        self._q.put((op_name, args, kwargs))

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                op_name, args, kwargs = self._q.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                # Dispatch via a callable if provided.
                func = kwargs.pop("callable", None)
                if callable(func):
                    func(*args, **kwargs)
            except Exception as e:
                print(f"[WriteQueue] Error processing op {op_name}: {e}")
            finally:
                self._q.task_done()

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._workers:
            t.join(timeout=1.0)


# -----------------------------------------------------------------------------
# User Repository (user-centric schema, segregated by class DB) with RAM cache
# -----------------------------------------------------------------------------

class UserRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # RAM caches (primary while process is running)
        self._cache9: Dict[str, Dict[str, Any]] = {}
        self._cache10: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        # Ensure indexes exist on both DBs
        for std in (9, 10):
            col = db_client.get_collection("Users", standard=std)
            col.create_index([("id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING), ("division", ASCENDING)])
            col.create_index([("teacher", ASCENDING)])

    # --------------- Cache helpers ---------------
    def _cache_for(self, is_class10: bool) -> Dict[str, Dict[str, Any]]:
        return self._cache10 if is_class10 else self._cache9

    def _set_cached_user(self, user_doc: Dict[str, Any]) -> None:
        std = int(user_doc.get("standard", 9))
        is10 = (std == 10)
        with self._lock:
            self._cache_for(is10)[user_doc["id"]] = user_doc

    def _get_cached_user(self, user_id: str, is_class10: Optional[bool]) -> Optional[Dict[str, Any]]:
        with self._lock:
            if is_class10 is None:
                if user_id in self._cache9:
                    return self._cache9[user_id]
                if user_id in self._cache10:
                    return self._cache10[user_id]
                return None
            cache = self._cache_for(is_class10)
            return cache.get(user_id)

    def _col_for_user(self, user_id: str, is_class10: Optional[bool]) -> Tuple[Collection, bool]:
        """Resolve collection for user. If class unknown, probe 9 then 10. Returns (collection, is_class10)."""
        if is_class10 is not None:
            return self.db_client.get_collection("Users", is_class10=is_class10), is_class10

        # Try RAM caches first
        cached = self._get_cached_user(user_id, None)
        if cached is not None:
            std = int(cached.get("standard", 9))
            return self.db_client.get_collection("Users", standard=std), (std == 10)

        # Probe DB 9 then 10
        col9 = self.db_client.get_collection("Users", is_class10=False)
        doc = col9.find_one({"id": user_id})
        if doc:
            return col9, False
        col10 = self.db_client.get_collection("Users", is_class10=True)
        doc = col10.find_one({"id": user_id})
        if doc:
            return col10, True
        # Default to class 9 if unknown (caller will insert)
        return self.db_client.get_collection("Users", is_class10=False), False

    def get_user(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        cached = self._get_cached_user(user_id, is_class10)
        if cached is not None:
            return cached

        doc = None
        if is_class10 is not None:
            col = self.db_client.get_collection("Users", is_class10=is_class10)
            doc = col.find_one({"id": user_id})
            if doc:
                self._set_cached_user(doc)
                return doc
            other_col = self.db_client.get_collection("Users", is_class10=not is_class10)
            doc = other_col.find_one({"id": user_id})
        else:
            col9 = self.db_client.get_collection("Users", is_class10=False)
            doc = col9.find_one({"id": user_id})
            if not doc:
                col10 = self.db_client.get_collection("Users", is_class10=True)
                doc = col10.find_one({"id": user_id})

        if doc:
            self._set_cached_user(doc)
        return doc

    def create_user(
        self,
        user_id: str,
        password: Optional[str],
        name: str,
        roll_no: int,
        division: str,
        standard: int,
        teacher: bool = False,
    ) -> Dict[str, Any]:
        subjects = ["Math", "SS", "English", "Science"]
        subject_stats = [
            {
                "subject": subj,
                "attempted": 0,
                "avgPercentage": 0.0,
                "marksGained": 0,
                "marksAttempted": 0,
                "highestMark": 0.0,
                "lowestMark": 0.0,
            }
            for subj in subjects
        ]
        user_doc = {
            "id": user_id,
            "name": name,
            "password": password,
            "rollno": roll_no,
            "division": division,
            "standard": int(standard),
            "teacher": teacher,
            "coins": 0,
            "tasks": {"generated_at": None, "tasks_list": []},
            "stats": {"attempted": 0, "correct": 0, "questions": 0, "avgPercentage": 0.0},
            "subjects": subject_stats,
            "examHistory": [],
        }

        # RAM first
        self._set_cached_user(user_doc)

        # Queue DB write
        def _op():
            col = self.db_client.get_collection("Users", standard=standard)
            col.update_one({"id": user_id}, {"$setOnInsert": user_doc}, upsert=True)

        self.write_queue.enqueue("user_create", callable=_op)
        return user_doc

    def set_password(self, user_id: str, new_password: str, is_class10: Optional[bool] = None) -> bool:
        # RAM first
        user = self.get_user(user_id, is_class10)
        if not user:
            return False
        with self._lock:
            user["password"] = new_password

        # Queue DB write
        def _op():
            col, _ = self._col_for_user(user_id, is_class10)
            col.update_one({"id": user_id}, {"$set": {"password": new_password}})

        self.write_queue.enqueue("user_set_password", callable=_op)
        return True

    def update_tasks(self, user_id: str, tasks: Dict[str, Any], is_class10: Optional[bool] = None, coins: Optional[int] = None) -> None:
        # RAM first
        user = self.get_user(user_id, is_class10)
        if not user:
            return
        with self._lock:
            user["tasks"] = tasks
            if coins is not None:
                user["coins"] = coins

        # Queue DB write
        def _op():
            col, _ = self._col_for_user(user_id, is_class10)
            update_set = {"tasks": tasks}
            if coins is not None:
                update_set["coins"] = coins
            col.update_one({"id": user_id}, {"$set": update_set})

        self.write_queue.enqueue("user_update_tasks", callable=_op)

    def get_user_stats(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return None
        return user.get("stats", None)

    def get_all_user_subject_stats(self, user_id: str, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        subjects = user.get("subjects", []) or []
        for s in subjects:
            s.pop("_id", None)
        return subjects

    def get_user_subject_stats(self, user_id: str, subject: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        subjects = self.get_all_user_subject_stats(user_id, is_class10)
        for s in subjects:
            if s.get("subject", "").lower() == subject.lower():
                return s
        return None

    def add_exam_history(self, user_id: str, overview: Dict[str, Any], is_class10: Optional[bool] = None) -> None:
        # RAM first
        user = self.get_user(user_id, is_class10)
        if not user:
            return
        with self._lock:
            if "examHistory" not in user or not isinstance(user["examHistory"], list):
                user["examHistory"] = []
            user["examHistory"].append(overview)

        # Queue DB write
        def _op():
            col, _ = self._col_for_user(user_id, is_class10)
            col.update_one({"id": user_id}, {"$push": {"examHistory": overview}})

        self.write_queue.enqueue("user_add_exam_history", callable=_op)

    def update_stats_after_exam(
        self,
        user_id: str,
        subject: str,
        score: int,
        total_questions: int,
        percentage: float,
        exam_id: str,
        lessons: List[str],
        test: bool = False,
        test_name: Optional[str] = None,
        is_class10: Optional[bool] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            raise ValueError(f"User {user_id} not found")

        with self._lock:
            # Overall
            overall = user.get("stats", {"attempted": 0, "correct": 0, "questions": 0, "avgPercentage": 0.0})
            attempted = int(overall.get("attempted", 0)) + 1
            correct = int(overall.get("correct", 0)) + score
            questions = int(overall.get("questions", 0)) + total_questions
            avg_percentage = (correct / questions * 100.0) if questions > 0 else 0.0
            overall.update(
                {
                    "attempted": attempted,
                    "correct": correct,
                    "questions": questions,
                    "avgPercentage": round(avg_percentage, 2),
                }
            )
            user["stats"] = overall

            # Subject stats
            subjects = user.get("subjects", [])
            subj = None
            for s in subjects:
                if s.get("subject") == subject:
                    subj = s
                    break
            if not subj:
                subj = {
                    "subject": subject,
                    "attempted": 0,
                    "avgPercentage": 0.0,
                    "marksGained": 0,
                    "marksAttempted": 0,
                    "highestMark": 0.0,
                    "lowestMark": 0.0,
                }
                subjects.append(subj)

            subj_attempted = int(subj.get("attempted", 0)) + 1
            subj_marks_gained = int(subj.get("marksGained", 0)) + score
            subj_marks_attempted = int(subj.get("marksAttempted", 0)) + total_questions
            subj_avg = (subj_marks_gained / subj_marks_attempted * 100.0) if subj_marks_attempted > 0 else 0.0
            subj_high = max(float(subj.get("highestMark", 0.0)), float(percentage))
            prev_low = float(subj.get("lowestMark", 0.0))
            subj_low = (
                float(percentage)
                if prev_low == 0.0 and subj_attempted == 1
                else (min(prev_low, float(percentage)) if prev_low > 0 else float(percentage))
            )
            subj.update(
                {
                    "attempted": subj_attempted,
                    "avgPercentage": round(subj_avg, 2),
                    "marksGained": subj_marks_gained,
                    "marksAttempted": subj_marks_attempted,
                    "highestMark": round(subj_high, 2),
                    "lowestMark": round(subj_low, 2),
                }
            )
            user["subjects"] = subjects

        # Queue DB write for stats/subjects
        def _op_stats():
            col, _ = self._col_for_user(user_id, is_class10)
            col.update_one(
                {"id": user_id},
                {"$set": {"stats": user["stats"], "subjects": user["subjects"]}},
            )

        self.write_queue.enqueue("user_update_stats_subjects", callable=_op_stats)

        # Append exam history in RAM + queue to DB
        overview_stats = {
            "exam-id": exam_id,
            "subject": subject,
            "score": score,
            "totalQuestions": total_questions,
            "percentage": percentage,
            "lessons": lessons or [],
            "date": datetime.now(IST).strftime("%d-%m-%Y"),
            "test": bool(test),
        }
        if test and test_name:
            overview_stats["test_name"] = test_name

        self.add_exam_history(user_id, overview_stats, is_class10=is_class10)
        return user["stats"], subj

    def get_user_exams_overview(self, user_id: str, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        return user.get("examHistory", []) or []

    def get_all_students_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        # Fetch directly from DB (list operation) and optionally refresh cache entries
        col = self.db_client.get_collection("Users", standard=standard)
        students = list(col.find({"teacher": {"$ne": True}}))
        result = []
        for s in students:
            s.pop("_id", None)
            self._set_cached_user(s)
            result.append(
                {"id": s.get("id"), "name": s.get("name"), "division": s.get("division"), "roll": s.get("rollno")}
            )
        return result

    def _load_all_users_to_cache(self) -> None:
        """Fetch all users from both DBs and load them into the RAM cache."""
        print("Pre-loading user caches...")
        total_count = 0
        for std in (9, 10):
            try:
                col = self.db_client.get_collection("Users", standard=std)
                user_docs = list(col.find({}))
                db_count = len(user_docs)
                for user_doc in user_docs:
                    user_doc.pop("_id", None)
                    self._set_cached_user(user_doc)
                total_count += db_count
            except Exception as e:
                print(f"ERROR: Could not load users for standard {std}. Reason: {e}")
        print(f"Finished pre-loading. Total users loaded into cache: {total_count}.")


# -----------------------------------------------------------------------------
# Exam Repository (segregated by class DB) with RAM cache
# -----------------------------------------------------------------------------

class ExamRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # RAM caches
        self._cache9: Dict[str, Dict[str, Any]] = {}
        self._cache10: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        # Ensure indexes on both DBs
        for std in (9, 10):
            col = db_client.get_collection("Exams", standard=std)
            col.create_index([("exam-id", ASCENDING)], unique=True)
            col.create_index([("userId", ASCENDING), ("is_submitted", ASCENDING)])
            col.create_index([("submission_timestamp", DESCENDING)])

    def _cache_for(self, is_class10: bool) -> Dict[str, Dict[str, Any]]:
        return self._cache10 if is_class10 else self._cache9

    def _set_cached_exam(self, exam_doc: Dict[str, Any]) -> None:
        std = int(exam_doc.get("standard", 9))
        is10 = (std == 10)
        with self._lock:
            self._cache_for(is10)[exam_doc["exam-id"]] = exam_doc

    def _get_cached_exam(self, exam_id: str, is_class10: Optional[bool]) -> Optional[Dict[str, Any]]:
        with self._lock:
            if is_class10 is None:
                if exam_id in self._cache9:
                    return self._cache9[exam_id]
                if exam_id in self._cache10:
                    return self._cache10[exam_id]
                return None
            cache = self._cache_for(is_class10)
            return cache.get(exam_id)

    def _col_by_params(self, is_class10: Optional[bool] = None, standard: Optional[int] = None) -> Collection:
        return self.db_client.get_collection("Exams", is_class10=is_class10, standard=standard)

    def add_exam(self, exam_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        # RAM first
        self._set_cached_exam(exam_data)

        # Queue DB write
        def _op():
            std = exam_data.get("standard")
            col = self._col_by_params(is_class10=is_class10, standard=std)
            col.insert_one(exam_data)

        self.write_queue.enqueue("exam_add", callable=_op)
        return exam_data

    def get_exam(self, exam_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        cached = self._get_cached_exam(exam_id, is_class10)
        if cached is not None:
            return cached

        if is_class10 is None:
            # Probe DB 9 then 10
            col9 = self._col_by_params(is_class10=False)
            doc = col9.find_one({"exam-id": exam_id})
            if doc:
                self._set_cached_exam(doc)
                return doc
            col10 = self._col_by_params(is_class10=True)
            doc = col10.find_one({"exam-id": exam_id})
            if doc:
                self._set_cached_exam(doc)
                return doc
            return None

        col = self._col_by_params(is_class10=is_class10)
        doc = col.find_one({"exam-id": exam_id})
        if doc:
            self._set_cached_exam(doc)
        return doc

    def update_exam(self, exam_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        # RAM first
        exam = self.get_exam(exam_id, is_class10)
        if not exam:
            return False
        with self._lock:
            exam.update(updated_data)

        # Queue DB write
        def _op():
            col = self._col_by_params(is_class10=is_class10, standard=exam.get("standard"))
            col.update_one({"exam-id": exam_id}, {"$set": updated_data})

        self.write_queue.enqueue("exam_update", callable=_op)
        return True

    def update_exam_solution(self, exam_id: str, question_index: int, solution: str, is_class10: Optional[bool] = None) -> bool:
        exam = self.get_exam(exam_id, is_class10)
        if not exam:
            return False
        with self._lock:
            try:
                if "results" in exam and 0 <= question_index < len(exam["results"]):
                    exam["results"][question_index]["solution"] = solution
            except Exception:
                pass

        def _op():
            col = self._col_by_params(is_class10=is_class10, standard=exam.get("standard"))
            update_field = f"results.{question_index}.solution"
            col.update_one({"exam-id": exam_id}, {"$set": {update_field: solution}})

        self.write_queue.enqueue("exam_update_solution", callable=_op)
        return True


# -----------------------------------------------------------------------------
# Test Repository (segregated by class DB) with RAM cache
# -----------------------------------------------------------------------------

class TestRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # RAM caches
        self._cache9: Dict[str, Dict[str, Any]] = {}
        self._cache10: Dict[str, Dict[str, Any]] = {}
        self._inactive9: Dict[str, Dict[str, Any]] = {}
        self._inactive10: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        for std in (9, 10):
            col = db_client.get_collection("Tests", standard=std)
            col.create_index([("test-id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING)])
            col.create_index([("expiration_date", ASCENDING)])
            inactive = db_client.get_collection("InactiveTests", standard=std)
            inactive.create_index([("test-id", ASCENDING)], unique=True)

    def _cache_for(self, is_class10: bool) -> Dict[str, Dict[str, Any]]:
        return self._cache10 if is_class10 else self._cache9

    def _inactive_for(self, is_class10: bool) -> Dict[str, Dict[str, Any]]:
        return self._inactive10 if is_class10 else self._inactive9

    def _set_cached_test(self, test_doc: Dict[str, Any]) -> None:
        std = int(test_doc.get("standard", 9))
        is10 = (std == 10)
        with self._lock:
            self._cache_for(is10)[test_doc["test-id"]] = test_doc

    def add_test(self, test_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        # RAM first
        self._set_cached_test(test_data)

        def _op():
            std = test_data.get("standard")
            col = self.db_client.get_collection("Tests", standard=std)
            col.insert_one(test_data)

        self.write_queue.enqueue("test_add", callable=_op)
        return test_data

    def get_test(self, test_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            if is_class10 is None:
                if test_id in self._cache9:
                    return self._cache9[test_id]
                if test_id in self._cache10:
                    return self._cache10[test_id]
            else:
                cache = self._cache_for(is_class10)
                if test_id in cache:
                    return cache[test_id]

        # Fallback to DB
        if is_class10 is None:
            col9 = self.db_client.get_collection("Tests", is_class10=False)
            doc = col9.find_one({"test-id": test_id})
            if doc:
                self._set_cached_test(doc)
                return doc
            col10 = self.db_client.get_collection("Tests", is_class10=True)
            doc = col10.find_one({"test-id": test_id})
            if doc:
                self._set_cached_test(doc)
                return doc
            return None

        col = self.db_client.get_collection("Tests", is_class10=is_class10)
        doc = col.find_one({"test-id": test_id})
        if doc:
            self._set_cached_test(doc)
        return doc

    def get_all_tests(self, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        # Fetch from DB to ensure completeness, then backfill cache
        if is_class10 is None:
            tests = []
            for flag in (False, True):
                col = self.db_client.get_collection("Tests", is_class10=flag)
                docs = list(col.find({}))
                for d in docs:
                    d.pop("_id", None)
                    self._set_cached_test(d)
                tests.extend(docs)
            return tests
        col = self.db_client.get_collection("Tests", is_class10=is_class10)
        docs = list(col.find({}))
        for d in docs:
            d.pop("_id", None)
            self._set_cached_test(d)
        return docs

    def get_all_tests_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        col = self.db_client.get_collection("Tests", standard=standard)
        docs = list(col.find({"standard": int(standard)}))
        for d in docs:
            d.pop("_id", None)
            self._set_cached_test(d)
        return docs

    def update_test(self, test_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        with self._lock:
            test.update(updated_data)

        def _op():
            std = test.get("standard", 9)
            col = self.db_client.get_collection("Tests", standard=std)
            col.update_one({"test-id": test_id}, {"$set": updated_data})

        self.write_queue.enqueue("test_update", callable=_op)
        return True

    def delete_test(self, test_id: str, is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        std = int(test.get("standard", 9))
        is10 = (std == 10)
        with self._lock:
            cache = self._cache_for(is10)
            cache.pop(test_id, None)

        def _op():
            col = self.db_client.get_collection("Tests", standard=std)
            col.delete_one({"test-id": test_id})

        self.write_queue.enqueue("test_delete", callable=_op)
        return True

    def move_expired_tests_to_inactive(self) -> int:
        """Move expired tests to InactiveTests for both classes; update RAM and DB."""
        from datetime import timezone as dt_tz
        now = datetime.now(dt_tz.utc)
        total_moved = 0
        try:
            for is_class10 in (False, True):
                tests_col = self.db_client.get_collection("Tests", is_class10=is_class10)
                inactive_col = self.db_client.get_collection("InactiveTests", is_class10=is_class10)
                docs = list(tests_col.find({}))
                for test in docs:
                    exp = test.get("expiration_date")
                    if not exp:
                        continue
                    try:
                        iso = exp.replace("Z", "+00:00")
                        exp_dt = datetime.fromisoformat(iso)
                    except Exception:
                        continue
                    if exp_dt < now:
                        # RAM update
                        with self._lock:
                            cache = self._cache_for(is_class10)
                            inactive_cache = self._inactive_for(is_class10)
                            cache.pop(test["test-id"], None)
                            tcopy = dict(test)
                            tcopy.pop("_id", None)
                            inactive_cache[test["test-id"]] = tcopy
                        # Queue DB move
                        def _op(doc=test, is10=is_class10):
                            incol = self.db_client.get_collection("InactiveTests", is_class10=is10)
                            tcol = self.db_client.get_collection("Tests", is_class10=is10)
                            try:
                                incol.insert_one(doc)
                            finally:
                                tcol.delete_one({"test-id": doc["test-id"]})

                        self.write_queue.enqueue("test_move_expired", callable=_op)
                        total_moved += 1
        except Exception as e:
            print(f"Error during moving expired tests: {e}")
        return total_moved

    def _load_all_tests_to_cache(self) -> None:
        """Fetch all active tests from both DBs and load them into the RAM cache."""
        print("Pre-loading test caches...")
        total_count = 0
        for std in (9, 10):
            try:
                col = self.db_client.get_collection("Tests", standard=std)
                std_count = 0
                for test_doc in col.find({}):
                    test_doc.pop("_id", None)
                    self._set_cached_test(test_doc)
                    std_count += 1
                total_count += std_count
            except Exception as e:
                print(f"ERROR: Could not load tests for standard {std}. Reason: {e}")
        print(f"Finished pre-loading. Total active tests loaded into cache: {total_count}.")


# -----------------------------------------------------------------------------
# Leaderboard Service (segregated per class DB)
# -----------------------------------------------------------------------------

class LeaderboardService:
    def __init__(self, db_client: DatabaseClient, user_repo: UserRepository, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.user_repo = user_repo
        self.write_queue = write_queue
        # Index on both DBs
        for std in (9, 10):
            col = db_client.get_collection("LeaderboardMonthly", standard=std)
            # _id index exists by default and is unique; no need to create it manually.

    @staticmethod
    def calculate_elo_change(score_percentage: float, num_lessons: int, subject: str) -> int:
        base_multiplier = 32
        subject_weights = {
            "Mathematics": 1.5,
            "Science": 1.2,
            "Social Studies": 1.0,
            "Math": 1.5,
            "SS": 1.0,
        }
        subject_weight = subject_weights.get(subject, 1.0)
        lesson_multiplier = 1 + (num_lessons * 0.1)
        performance_multiplier = (score_percentage / 100.0)
        elo_change = base_multiplier * subject_weight * lesson_multiplier * performance_multiplier
        return round(elo_change)

    def _entry_from_user_for_month(self, u: Dict[str, Any], month_key: str) -> Optional[Dict[str, Any]]:
        user_id = u.get("id")
        if not user_id:
            return None
        name = u.get("name", "UNKNOWN")
        division = u.get("division", "N/A")
        coins = u.get("coins", 0)
        exam_history = u.get("examHistory", []) or []
        total_exams = 0
        total_score = 0
        total_questions = 0
        elo_score = 0
        for e in exam_history:
            if month_key_from_date_str(e.get("date", "")) != month_key:
                continue
            total_exams += 1
            score = int(e.get("score", 0))
            tq = int(e.get("totalQuestions", 0))
            total_score += score
            total_questions += tq
            pct = float(e.get("percentage", 0.0))
            subj = e.get("subject", "")
            lessons = e.get("lessons", []) or []
            elo_score += self.calculate_elo_change(pct, len(lessons), subj)
        has_taken_exam = total_exams > 0
        name_parts = (name or "").split()
        if len(name_parts) >= 2:
            display_name = f"{name_parts[0].upper()} {name_parts[-1].upper()}"
        elif len(name_parts) == 1:
            display_name = name_parts[0].upper()
        else:
            display_name = "UNKNOWN"
        return {
            "userId": user_id,
            "name": display_name,
            "division": division,
            "total_exams": total_exams,
            "coins": coins,
            "elo_score": elo_score,
            "has_taken_exam": has_taken_exam,
            "total_score": total_score,
            "total_questions": total_questions,
            "average_percentage": (total_score / total_questions * 100.0) if total_questions > 0 else 0.0,
        }

    def _col(self, standard: int) -> Collection:
        return self.db_client.get_collection("LeaderboardMonthly", standard=standard)

    def _build_snapshot_for_month(self, standard: int, month_key: str) -> Dict[str, Any]:
        users_col = self.db_client.get_collection("Users", standard=standard)
        teachers = set(u["id"] for u in users_col.find({"teacher": True}, {"id": 1}))
        users = list(users_col.find({}, {"_id": 0}))
        entries: List[Dict[str, Any]] = []
        for u in users:
            user_id = u.get("id")
            if not user_id or user_id in teachers:
                continue
            entry = self._entry_from_user_for_month(u, month_key)
            if entry:
                entries.append(entry)

        entries.sort(
            key=lambda x: (x.get("has_taken_exam", False), x.get("elo_score", 0), x.get("coins", 0)),
            reverse=True,
        )
        version = hashlib.sha256(f"{month_key}-{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        doc_id = f"{month_key}-{standard}"
        snapshot = {
            "_id": doc_id,
            "version": version,
            "month": month_key,
            "standard": standard,
            "entries": entries,
        }
        self._col(standard).replace_one({"_id": doc_id}, snapshot, upsert=True)
        return snapshot

    def get_or_build_monthly(
        self,
        standard: int,
        month_key: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        mk = month_key or current_month_key()
        doc_id = f"{mk}-{standard}"
        doc = self._col(standard).find_one({"_id": doc_id})
        if not doc:
            doc = self._build_snapshot_for_month(standard, mk)
        entries = doc.get("entries", [])
        total_count = len(entries)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = min(total_count, start_idx + page_size)
        paged = entries[start_idx:end_idx]
        for i, entry in enumerate(paged, 1):
            entry["rank"] = start_idx + i
        return {
            "version": doc.get("version"),
            "month": mk,
            "standard": standard,
            "total_count": total_count,
            "entries": paged,
        }

    def preload_current_month_leaderboard(self):
        """Builds the leaderboard for the current month for both standards if it doesn't exist."""
        print("Pre-loading current month leaderboard...")
        month_key = current_month_key()
        for std in (9, 10):
            try:
                # Check if it exists first to avoid unnecessary rebuilds
                doc_id = f"{month_key}-{std}"
                doc = self._col(std).find_one({"_id": doc_id}, {"_id": 1})
                if not doc:
                    self._build_snapshot_for_month(std, month_key)
            except Exception as e:
                print(f"Error pre-loading leaderboard for standard {std}: {e}")
        print("Finished pre-loading leaderboard.")

    def update_on_submission(self, user_id: str, standard: int, month_key: Optional[str] = None) -> None:
        """Recompute a single user's leaderboard entry for the month and upsert into snapshot."""
        mk = month_key or current_month_key()
        doc_id = f"{mk}-{standard}"

        def _op():
            col = self._col(standard)
            doc = col.find_one({"_id": doc_id})
            if not doc:
                doc = self._build_snapshot_for_month(standard, mk)
            user = self.db_client.get_collection("Users", standard=standard).find_one({"id": user_id})
            if not user or user.get("teacher"):
                return
            updated_entry = self._entry_from_user_for_month(user, mk)
            if updated_entry is None:
                return
            entries = doc.get("entries", [])
            replaced = False
            for idx, e in enumerate(entries):
                if e.get("userId") == user_id:
                    entries[idx] = updated_entry
                    replaced = True
                    break
            if not replaced:
                entries.append(updated_entry)
            entries.sort(
                key=lambda x: (x.get("has_taken_exam", False), x.get("elo_score", 0), x.get("coins", 0)),
                reverse=True,
            )
            version = doc.get("version") or hashlib.sha256(f"{mk}-{datetime.now().timestamp()}".encode()).hexdigest()[:8]
            col.update_one(
                {"_id": doc_id},
                {"$set": {"entries": entries, "version": version, "month": mk, "standard": standard}},
                upsert=True,
            )
        self.write_queue.enqueue("leaderboard_update_on_submission", callable=_op)


# -----------------------------------------------------------------------------
# App-level instances and preload
# -----------------------------------------------------------------------------

_db_client = DatabaseClient()
_write_queue = WriteQueue(_db_client, worker_count=1)
user_repo = UserRepository(_db_client, _write_queue)
exam_repo = ExamRepository(_db_client, _write_queue)
test_repo = TestRepository(_db_client, _write_queue)
leaderboard_service = LeaderboardService(_db_client, user_repo, _write_queue)


def preload_caches():
    """Load primary data from DB into RAM caches at startup."""
    print("----- Pre-loading all caches -----")
    try:
        user_repo._load_all_users_to_cache()
        test_repo._load_all_tests_to_cache()
        leaderboard_service.preload_current_month_leaderboard()
    except Exception as e:
        print(f"Error during cache pre-loading: {e}")
    print("----- Cache pre-loading finished -----")


__all__ = [
    "DatabaseClient",
    "WriteQueue",
    "UserRepository",
    "ExamRepository",
    "TestRepository",
    "LeaderboardService",
    "user_repo",
    "exam_repo",
    "test_repo",
    "leaderboard_service",
    "convert_objectid_to_str",
    "preload_caches",
]
