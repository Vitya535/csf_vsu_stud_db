# Функция-заглушка
# В production версии необходимо подключение к ldap


def password_checker(login, password):
    if (login, password) == ('eremin_i_a', 'eremin_i_a'):
        return True
    if (login, password) == ('erilya', 'erilya'):
        return True
    if (login, password) == ('ivanov_i_i', 'ivanov_i_i'):
        return True
    if (login, password) == ('kushnerenko_v_k', 'dffgrtrw43'):
        return True
    return False
