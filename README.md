## Добавлены инструкции по установке приложения под различными OS.

https://trello.com/b/gZx6mGb6/tpcsf

miro
https://miro.com/app/board/o9J_kxGMGvw=/

Техническое задание: https://github.com/erilya/csf_vsu_stud_db/blob/master/__docs/TZ_2.docx

Курсовой проект:
https://github.com/erilya/csf_vsu_stud_db/blob/master/__docs/kurs_proj.docx

Видео:
https://youtu.be/eBAWfz7o7z8
### Выступление (презентация):
https://github.com/erilya/csf_vsu_stud_db/blob/master/__docs/pt_pres_das_eia.pptx

### Инструкция:

### OS Windows
https://github.com/erilya/csf_vsu_stud_db/blob/master/__docs/config_pt_windows_das.txt

### OS Linux
https://github.com/erilya/csf_vsu_stud_db/blob/master/__docs/config_pt_linux_debian_ubuntu.txt

Приложение, а так же вся документация для него разрабатывается группой студентов в рамках дисциплины "Технологии программирования" 3 курса ФКН 1 группы: Еремин Илья, Дуненбаев Артем и Баженов Вадим.

Login in GitHub: Еремин Илья erilya, Дуненбаев Артем Petizzen и Баженов Вадим Bazhen1337 (выбыл из команды)


# Система учёта аттестаций ВГУ ФКН для бакалавриата.
## Приложение должно позволять хранить информацию о:
1. Студентах факультета;
2. Студенческих группах (состояние группы в каждом семестре на протяжении всего срока обучения);
3. Учебных планах _(единица учебного плана - это предмет у определённой группы, в определённом семестре, с указанием преподавателя и типа отёчности: зачёт, экзамен, зачёт с оценкой)_;
4. Результатах аттестаций.

В системе необходимо реализовать авторизацию. Необходимо выделить следующие роли пользователей
### Роли:
1. **Секретарь (администратор)**. Формирует студенческие группы, списки студентов, преподавателей, учебные планы. Может также выставлять оценки по аттестациям по всем предметам.
2. **Преподаватель**. Может выставлять оценки по аттестациям только для своих предметов и групп.
3. **Гость**. Доступ без авторизации. Может просматривать результаты аттестаций.

Необходимо реализовать интерфейс для перевода всех студентов одной группы на следующий семестр(курс) и выпуска. При этом необходимо учитывать, что перевод возможен только при условии заполнения всех записей об аттестациях для текущего семестра. После перевода студента на следующий семестр (или оформления выпуска) редактирование результатов аттестаций запрещается, в том числе секретарю. Результаты за прошлый семестр должны быть сохранены включая выпущенных студентов.

Предусмотреть механизм отчисления и восстановления студента, а также установления для него атрибута "в академическом отпуске". 

### В приложении должно быть реализовано дополнительно:
1. Вывод статистической информации о результатах аттестации по группам и по конкретному студенту
2. Формирование бланков аттестационных ведомостей в формате odt, doc или pdf


