LESSON_TYPES = ('Лекция', 'Практика', 'Семинар')
HALF_YEARS = ('1', '2')


def get_field(field_id: str, fields: tuple):
    return next((fld for fld in fields if fld.id == field_id))
