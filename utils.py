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


def get_current_lesson_and_his_type():
    pass
