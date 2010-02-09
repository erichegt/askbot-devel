CREATE TABLE `fbconnect_fbassociation` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `fbuid` varchar(12) NOT NULL UNIQUE
)
;
ALTER TABLE `fbconnect_fbassociation` ADD CONSTRAINT `user_id_refs_id_3534873d`
FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `fbconnect_fbassociation_user_id` ON `fbconnect_fbassociation` (`user_id`);
