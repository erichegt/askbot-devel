BEGIN;
CREATE TABLE `forum_emailfeedsetting` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `subscriber_id` integer NOT NULL,
    `feed_type` varchar(16) NOT NULL,
    `frequency` varchar(8) NOT NULL,
    `added_at` datetime NOT NULL,
    `reported_at` datetime NULL
)
;
ALTER TABLE `forum_emailfeedsetting` ADD CONSTRAINT subscriber_id_refs_id_6fee6730cc813af8 FOREIGN KEY (`subscriber_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `tag` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(255) NOT NULL UNIQUE,
    `created_by_id` integer NOT NULL,
    `deleted` bool NOT NULL,
    `deleted_at` datetime NULL,
    `deleted_by_id` integer NULL,
    `used_count` integer UNSIGNED NOT NULL
)
;
ALTER TABLE `tag` ADD CONSTRAINT created_by_id_refs_id_6ae4d97547205d6d FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `tag` ADD CONSTRAINT deleted_by_id_refs_id_6ae4d97547205d6d FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `comment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `user_id` integer NOT NULL,
    `comment` varchar(300) NOT NULL,
    `added_at` datetime NOT NULL
)
;
ALTER TABLE `comment` ADD CONSTRAINT content_type_id_refs_id_89a4b13ec5a7994 FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `comment` ADD CONSTRAINT user_id_refs_id_5ba842626be725e8 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `vote` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `user_id` integer NOT NULL,
    `vote` smallint NOT NULL,
    `voted_at` datetime NOT NULL,
    UNIQUE (`content_type_id`, `object_id`, `user_id`)
)
;
ALTER TABLE `vote` ADD CONSTRAINT content_type_id_refs_id_77dc6ffafedbbec FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `vote` ADD CONSTRAINT user_id_refs_id_3ce5b20589f5b210 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `flagged_item` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `user_id` integer NOT NULL,
    `flagged_at` datetime NOT NULL,
    UNIQUE (`content_type_id`, `object_id`, `user_id`)
)
;
ALTER TABLE `flagged_item` ADD CONSTRAINT content_type_id_refs_id_261d26c8891bb28c FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `flagged_item` ADD CONSTRAINT user_id_refs_id_92ae9d35e3c608 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `question` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(300) NOT NULL,
    `author_id` integer NOT NULL,
    `added_at` datetime NOT NULL,
    `wiki` bool NOT NULL,
    `wikified_at` datetime NULL,
    `answer_accepted` bool NOT NULL,
    `closed` bool NOT NULL,
    `closed_by_id` integer NULL,
    `closed_at` datetime NULL,
    `close_reason` smallint NULL,
    `deleted` bool NOT NULL,
    `deleted_at` datetime NULL,
    `deleted_by_id` integer NULL,
    `locked` bool NOT NULL,
    `locked_by_id` integer NULL,
    `locked_at` datetime NULL,
    `score` integer NOT NULL,
    `vote_up_count` integer NOT NULL,
    `vote_down_count` integer NOT NULL,
    `answer_count` integer UNSIGNED NOT NULL,
    `comment_count` integer UNSIGNED NOT NULL,
    `view_count` integer UNSIGNED NOT NULL,
    `offensive_flag_count` smallint NOT NULL,
    `favourite_count` integer UNSIGNED NOT NULL,
    `last_edited_at` datetime NULL,
    `last_edited_by_id` integer NULL,
    `last_activity_at` datetime NOT NULL,
    `last_activity_by_id` integer NOT NULL,
    `tagnames` varchar(125) NOT NULL,
    `summary` varchar(180) NOT NULL,
    `html` longtext NOT NULL
)
;
ALTER TABLE `question` ADD CONSTRAINT author_id_refs_id_5159d9f3a9162ff4 FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `question` ADD CONSTRAINT closed_by_id_refs_id_5159d9f3a9162ff4 FOREIGN KEY (`closed_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `question` ADD CONSTRAINT deleted_by_id_refs_id_5159d9f3a9162ff4 FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `question` ADD CONSTRAINT locked_by_id_refs_id_5159d9f3a9162ff4 FOREIGN KEY (`locked_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `question` ADD CONSTRAINT last_edited_by_id_refs_id_5159d9f3a9162ff4 FOREIGN KEY (`last_edited_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `question` ADD CONSTRAINT last_activity_by_id_refs_id_5159d9f3a9162ff4 FOREIGN KEY (`last_activity_by_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `forum_questionview` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `who_id` integer NOT NULL,
    `when` datetime NOT NULL
)
;
ALTER TABLE `forum_questionview` ADD CONSTRAINT question_id_refs_id_fe63ebce6b3cbac FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `forum_questionview` ADD CONSTRAINT who_id_refs_id_293b67239e957c53 FOREIGN KEY (`who_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `favorite_question` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    `added_at` datetime NOT NULL
)
;
ALTER TABLE `favorite_question` ADD CONSTRAINT question_id_refs_id_2cafd2f21ebe1cc3 FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `favorite_question` ADD CONSTRAINT user_id_refs_id_1632ce11ad7ac7de FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `question_revision` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `revision` integer UNSIGNED NOT NULL,
    `title` varchar(300) NOT NULL,
    `author_id` integer NOT NULL,
    `revised_at` datetime NOT NULL,
    `tagnames` varchar(125) NOT NULL,
    `summary` varchar(300) NOT NULL,
    `text` longtext NOT NULL
)
;
ALTER TABLE `question_revision` ADD CONSTRAINT question_id_refs_id_61316ec87bef5296 FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `question_revision` ADD CONSTRAINT author_id_refs_id_79de7cc0b077fdb1 FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `forum_anonymousanswer` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `session_key` varchar(40) NOT NULL,
    `wiki` bool NOT NULL,
    `added_at` datetime NOT NULL,
    `ip_addr` char(15) NOT NULL,
    `author_id` integer NULL,
    `text` longtext NOT NULL,
    `summary` varchar(180) NOT NULL
)
;
ALTER TABLE `forum_anonymousanswer` ADD CONSTRAINT question_id_refs_id_17dd6b2f4cc171c7 FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `forum_anonymousanswer` ADD CONSTRAINT author_id_refs_id_3ac41be013fb542e FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `forum_anonymousquestion` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(300) NOT NULL,
    `session_key` varchar(40) NOT NULL,
    `text` longtext NOT NULL,
    `summary` varchar(180) NOT NULL,
    `tagnames` varchar(125) NOT NULL,
    `wiki` bool NOT NULL,
    `added_at` datetime NOT NULL,
    `ip_addr` char(15) NOT NULL,
    `author_id` integer NULL
)
;
ALTER TABLE `forum_anonymousquestion` ADD CONSTRAINT author_id_refs_id_2a673297511a98a FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `answer` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `author_id` integer NOT NULL,
    `added_at` datetime NOT NULL,
    `wiki` bool NOT NULL,
    `wikified_at` datetime NULL,
    `accepted` bool NOT NULL,
    `accepted_at` datetime NULL,
    `deleted` bool NOT NULL,
    `deleted_by_id` integer NULL,
    `locked` bool NOT NULL,
    `locked_by_id` integer NULL,
    `locked_at` datetime NULL,
    `score` integer NOT NULL,
    `vote_up_count` integer NOT NULL,
    `vote_down_count` integer NOT NULL,
    `comment_count` integer UNSIGNED NOT NULL,
    `offensive_flag_count` smallint NOT NULL,
    `last_edited_at` datetime NULL,
    `last_edited_by_id` integer NULL,
    `html` longtext NOT NULL
)
;
ALTER TABLE `answer` ADD CONSTRAINT question_id_refs_id_2300e0297d6550c9 FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `answer` ADD CONSTRAINT author_id_refs_id_6573e62f192b0170 FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `answer` ADD CONSTRAINT deleted_by_id_refs_id_6573e62f192b0170 FOREIGN KEY (`deleted_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `answer` ADD CONSTRAINT locked_by_id_refs_id_6573e62f192b0170 FOREIGN KEY (`locked_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `answer` ADD CONSTRAINT last_edited_by_id_refs_id_6573e62f192b0170 FOREIGN KEY (`last_edited_by_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `answer_revision` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `answer_id` integer NOT NULL,
    `revision` integer UNSIGNED NOT NULL,
    `author_id` integer NOT NULL,
    `revised_at` datetime NOT NULL,
    `summary` varchar(300) NOT NULL,
    `text` longtext NOT NULL
)
;
ALTER TABLE `answer_revision` ADD CONSTRAINT answer_id_refs_id_47145eaebe77d8fe FOREIGN KEY (`answer_id`) REFERENCES `answer` (`id`);
ALTER TABLE `answer_revision` ADD CONSTRAINT author_id_refs_id_2c17693c3ccc055f FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `badge` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(50) NOT NULL,
    `type` smallint NOT NULL,
    `slug` varchar(50) NOT NULL,
    `description` varchar(300) NOT NULL,
    `multiple` bool NOT NULL,
    `awarded_count` integer UNSIGNED NOT NULL,
    UNIQUE (`name`, `type`)
)
;
CREATE TABLE `award` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `badge_id` integer NOT NULL,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `awarded_at` datetime NOT NULL,
    `notified` bool NOT NULL
)
;
ALTER TABLE `award` ADD CONSTRAINT user_id_refs_id_5d197ea32d83e9b6 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `award` ADD CONSTRAINT badge_id_refs_id_4237a025651af0e1 FOREIGN KEY (`badge_id`) REFERENCES `badge` (`id`);
ALTER TABLE `award` ADD CONSTRAINT content_type_id_refs_id_72f17e2d83bbde26 FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE TABLE `repute` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `positive` smallint NOT NULL,
    `negative` smallint NOT NULL,
    `question_id` integer NOT NULL,
    `reputed_at` datetime NOT NULL,
    `reputation_type` smallint NOT NULL,
    `reputation` integer NOT NULL
)
;
ALTER TABLE `repute` ADD CONSTRAINT user_id_refs_id_fcf719405a426cd FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `repute` ADD CONSTRAINT question_id_refs_id_4749166abeb39c4e FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
CREATE TABLE `activity` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `activity_type` smallint NOT NULL,
    `active_at` datetime NOT NULL,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL,
    `is_auditted` bool NOT NULL
)
;
ALTER TABLE `activity` ADD CONSTRAINT user_id_refs_id_6015206347c8583f FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `activity` ADD CONSTRAINT content_type_id_refs_id_78877d15efa8edfd FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE TABLE `book` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `title` varchar(255) NOT NULL,
    `short_name` varchar(255) NOT NULL,
    `author` varchar(255) NOT NULL,
    `price` numeric(6, 2) NOT NULL,
    `pages` smallint NOT NULL,
    `published_at` datetime NOT NULL,
    `publication` varchar(255) NOT NULL,
    `cover_img` varchar(255) NOT NULL,
    `tagnames` varchar(125) NOT NULL,
    `added_at` datetime NOT NULL,
    `last_edited_at` datetime NOT NULL
)
;
ALTER TABLE `book` ADD CONSTRAINT user_id_refs_id_607b4cfdf0283c8d FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `book_author_info` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `book_id` integer NOT NULL,
    `blog_url` varchar(255) NOT NULL,
    `added_at` datetime NOT NULL,
    `last_edited_at` datetime NOT NULL
)
;
ALTER TABLE `book_author_info` ADD CONSTRAINT user_id_refs_id_3781e2a5fbe1cfda FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `book_author_info` ADD CONSTRAINT book_id_refs_id_688c8f047c49bbf8 FOREIGN KEY (`book_id`) REFERENCES `book` (`id`);
CREATE TABLE `book_author_rss` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `book_id` integer NOT NULL,
    `title` varchar(255) NOT NULL,
    `url` varchar(255) NOT NULL,
    `rss_created_at` datetime NOT NULL,
    `added_at` datetime NOT NULL
)
;
ALTER TABLE `book_author_rss` ADD CONSTRAINT user_id_refs_id_1fd25dcf3596f741 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `book_author_rss` ADD CONSTRAINT book_id_refs_id_f64066171717121 FOREIGN KEY (`book_id`) REFERENCES `book` (`id`);
CREATE TABLE `forum_anonymousemail` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `key` varchar(32) NOT NULL,
    `email` varchar(75) NOT NULL UNIQUE,
    `isvalid` bool NOT NULL
)
;
CREATE TABLE `question_tags` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `tag_id` integer NOT NULL,
    UNIQUE (`question_id`, `tag_id`)
)
;
ALTER TABLE `question_tags` ADD CONSTRAINT question_id_refs_id_35d758e3d99eb83a FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `question_tags` ADD CONSTRAINT tag_id_refs_id_3b0ddddfbc0346ad FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`);
CREATE TABLE `question_followed_by` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`question_id`, `user_id`)
)
;
ALTER TABLE `question_followed_by` ADD CONSTRAINT question_id_refs_id_6ea9c52125c22aae FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `question_followed_by` ADD CONSTRAINT user_id_refs_id_49cca2976d30712d FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `book_question` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `book_id` integer NOT NULL,
    `question_id` integer NOT NULL,
    UNIQUE (`book_id`, `question_id`)
)
;
ALTER TABLE `book_question` ADD CONSTRAINT book_id_refs_id_535ac8946a43c4d1 FOREIGN KEY (`book_id`) REFERENCES `book` (`id`);
ALTER TABLE `book_question` ADD CONSTRAINT question_id_refs_id_372b7e81c7aff6d8 FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
CREATE TABLE `django_authopenid_nonce` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `server_url` varchar(255) NOT NULL,
    `timestamp` integer NOT NULL,
    `salt` varchar(40) NOT NULL
)
;
CREATE TABLE `django_authopenid_association` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `server_url` longtext NOT NULL,
    `handle` varchar(255) NOT NULL,
    `secret` longtext NOT NULL,
    `issued` integer NOT NULL,
    `lifetime` integer NOT NULL,
    `assoc_type` longtext NOT NULL
)
;
CREATE TABLE `django_authopenid_userassociation` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `openid_url` varchar(255) NOT NULL,
    `user_id` integer NOT NULL UNIQUE
)
;
ALTER TABLE `django_authopenid_userassociation` ADD CONSTRAINT user_id_refs_id_f63a9e7163d208d FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `django_authopenid_userpasswordqueue` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL UNIQUE,
    `new_password` varchar(30) NOT NULL,
    `confirm_key` varchar(40) NOT NULL
)
;
ALTER TABLE `django_authopenid_userpasswordqueue` ADD CONSTRAINT user_id_refs_id_7f488ca76bcaaa4 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `django_authopenid_externallogindata` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `external_username` varchar(40) NOT NULL UNIQUE,
    `external_session_data` longtext NOT NULL,
    `user_id` integer NULL
)
;
ALTER TABLE `django_authopenid_externallogindata` ADD CONSTRAINT user_id_refs_id_462c0ee2c3e5e139 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `auth_permission` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(50) NOT NULL,
    `content_type_id` integer NOT NULL,
    `codename` varchar(100) NOT NULL,
    UNIQUE (`content_type_id`, `codename`)
)
;
ALTER TABLE `auth_permission` ADD CONSTRAINT content_type_id_refs_id_6bc81a32728de91f FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE TABLE `auth_group` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(80) NOT NULL UNIQUE
)
;
CREATE TABLE `auth_user` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `username` varchar(30) NOT NULL UNIQUE,
    `first_name` varchar(30) NOT NULL,
    `last_name` varchar(30) NOT NULL,
    `email` varchar(75) NOT NULL,
    `password` varchar(128) NOT NULL,
    `is_staff` bool NOT NULL,
    `is_active` bool NOT NULL,
    `is_superuser` bool NOT NULL,
    `last_login` datetime NOT NULL,
    `date_joined` datetime NOT NULL,
    `is_approved` bool NOT NULL,
    `email_isvalid` bool NOT NULL,
    `email_key` varchar(32) NULL,
    `reputation` integer UNSIGNED NOT NULL,
    `gravatar` varchar(32) NOT NULL,
    `gold` smallint NOT NULL,
    `silver` smallint NOT NULL,
    `bronze` smallint NOT NULL,
    `questions_per_page` smallint NOT NULL,
    `last_seen` datetime NOT NULL,
    `real_name` varchar(100) NOT NULL,
    `website` varchar(200) NOT NULL,
    `location` varchar(100) NOT NULL,
    `date_of_birth` date NULL,
    `about` longtext NOT NULL
)
;
CREATE TABLE `auth_message` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `message` longtext NOT NULL
)
;
ALTER TABLE `auth_message` ADD CONSTRAINT user_id_refs_id_7837edc69af0b65a FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `auth_group_permissions` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` integer NOT NULL,
    `permission_id` integer NOT NULL,
    UNIQUE (`group_id`, `permission_id`)
)
;
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT group_id_refs_id_2ccea4c93cea63fe FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
ALTER TABLE `auth_group_permissions` ADD CONSTRAINT permission_id_refs_id_4de83ca7792de1 FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
CREATE TABLE `auth_user_groups` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `group_id` integer NOT NULL,
    UNIQUE (`user_id`, `group_id`)
)
;
ALTER TABLE `auth_user_groups` ADD CONSTRAINT user_id_refs_id_1993cb70831107f1 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `auth_user_groups` ADD CONSTRAINT group_id_refs_id_321a8efef0ee9890 FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE TABLE `auth_user_user_permissions` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `permission_id` integer NOT NULL,
    UNIQUE (`user_id`, `permission_id`)
)
;
ALTER TABLE `auth_user_user_permissions` ADD CONSTRAINT user_id_refs_id_166738bf2045483 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `auth_user_user_permissions` ADD CONSTRAINT permission_id_refs_id_6d7fb3c2067e79cb FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
COMMIT;
