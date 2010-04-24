alter table auth_user add column hide_ignored_questions tinyint(1) not NULL;
update auth_user set hide_ignored_questions=0;
alter table auth_user add column tag_filter_setting varchar(16) not NULL;
update auth_user set tag_filter_setting='ignored';
