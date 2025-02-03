import os

def lesson2filepath(subject, lesson, class10=False, data_path="data"):
    subject_lower = subject.lower()
    lesson_number = lesson.split()[-1]
    # Add class10 folder prefix if needed
    base_folder = "lessons10" if class10 else "lessons"

    if subject == "SS":
        prefix = lesson.split(":")[0].lower()
        return os.path.join(
            data_path,
            base_folder,
            subject_lower,
            f"{prefix}.{lesson_number.split('-')[1]}.json",
        )
    elif subject == "Science":
        return os.path.join(
            data_path, base_folder, subject_lower, f"lesson-{lesson_number}.json"
        )
    elif subject == "Math":
        return os.path.join(
            data_path, base_folder, subject_lower, f"lesson{lesson_number}.json"
        )
    else:
        return os.path.join(
            data_path, base_folder, subject_lower, f"lesson{lesson_number}.json"
        )
