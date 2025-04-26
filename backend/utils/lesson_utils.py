import os

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
