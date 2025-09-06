import os
import json
from typing import List

def lesson2filepath(subject, lesson, class10=False):
    subject_lower = subject.lower()
    if subject != "SS":
        lesson_number = lesson[0]
    base_folder = "lessons10" if class10 else "lessons"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data")

    if subject == "SS":
        lesson_number=lesson[1]
        prefix = lesson[0]
        path = os.path.join(
            data_path,
            base_folder,
            subject_lower,
            f"{prefix}.{lesson_number}.json",
        )
    elif subject == "Science":
        path = os.path.join(
            data_path, base_folder, subject_lower, f"lesson-{lesson_number}.json"
        )
    elif subject == "Math":
        path = os.path.join(
            data_path, base_folder, subject_lower, f"lesson{lesson_number}.json"
        )
    else:
        path = os.path.join(
            data_path, base_folder, subject_lower, f"lesson{lesson_number}.json"
        )

    return os.path.normpath(path)

def get_all_lessons_for_subject(subject: str, class10: bool = False) -> List[str]:
    """Fetches all lessons for a given subject from the data files."""
    lessons_file = "lessons10.json" if class10 else "lessons.json"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data")
    with open(os.path.join(data_path, lessons_file)) as f:
        lessons = json.load(f)
    return lessons.get(subject, [])


def get_all_subjects(class10: bool = False) -> List[str]:
    """Fetches all subjects from the data files."""
    lessons_file = "lessons10.json" if class10 else "lessons.json"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data")
    with open(os.path.join(data_path, lessons_file)) as f:
        lessons = json.load(f)
    return list(lessons.keys())
