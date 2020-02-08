ALTER TABLE `curriculum_unit` ADD COLUMN `curriculum_unit_status` ENUM('att_1', 'att_2', 'att_3', 'exam', 'close') NOT NULL DEFAULT 'att_1';
ALTER TABLE `att_mark` ADD COLUMN `att_mark_1_success` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Успешная сдача 1-й аттестации. Оценка может быть изменена только администратором';
ALTER TABLE `att_mark` ADD COLUMN `att_mark_2_success` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Успешная сдача 2-й аттестации. Оценка может быть изменена только администратором';
ALTER TABLE `att_mark` ADD COLUMN `att_mark_3_success` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Успешная сдача 3-й аттестации. Оценка может быть изменена только администратором';

ALTER TABLE `student` 
ADD COLUMN `card_number` BIGINT(20) UNSIGNED NULL COMMENT 'Номер карты (пропуск)',
ADD COLUMN `stud_group_leader` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Староста группы',
ADD UNIQUE INDEX `card_number_UNIQUE` (`card_number` ASC) VISIBLE;

