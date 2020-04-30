from datetime import datetime
from datetime import timedelta


def get_current_and_next_week_text_dates() -> list:
    today = datetime.now()

    date_str = today.strftime('%d.%m.%Y')
    date_obj = datetime.strptime(date_str, '%d.%m.%Y')

    start_of_week = date_obj - timedelta(days=date_obj.weekday())

    dates = [start_of_week + timedelta(days=i) for i in range(0, 13)]
    current_and_next_week_dates = dates[0:6] + dates[7:13]
    current_and_next_week_text_dates = [week_date.strftime('%d.%m.%Y') for week_date in current_and_next_week_dates]
    return current_and_next_week_text_dates


def convert_students_with_attendance_to_dict(students: list,
                                             teaching_lesson_id: int,
                                             current_and_next_week_dates: list) -> dict:
    students_with_attendance_dict = {}
    for student in students:
        attendance_list = []
        for week_date in current_and_next_week_dates:
            for attendance in student.attendance:
                print(f"attendance_lesson_date: {attendance.lesson_date}")
                print(f"week_date: {week_date}")
                if attendance.lesson_attendance and attendance.teaching_lesson_id == teaching_lesson_id \
                        and attendance.lesson_date == week_date:
                    attendance_list.append(attendance)
                else:
                    attendance_list.append(None)
            students_with_attendance_dict[student] = attendance_list
    return students_with_attendance_dict
