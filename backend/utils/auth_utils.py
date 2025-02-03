from flask_jwt_extended import get_jwt_identity
def get_student_class(user_id, student_info, class10_student_info):
    """Determine if student is in class 10 or 9"""
    if user_id in class10_student_info:
        return class10_student_info[user_id], True
    elif user_id in student_info:
        return student_info[user_id], False
    return None, None

def get_current_user_info():
    """Helper function to extract user info from JWT retoken"""
    jwt_data = get_jwt_identity()

    if isinstance(jwt_data, dict):
        return jwt_data.get("user_id"), jwt_data.get("class10", False)
    # Legacy token support
    return jwt_data, False  # Assume class 9 for old tokens

