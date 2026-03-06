CREATE DATABASE IF NOT EXISTS `health`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `health`;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `article_read_histories`;
DROP TABLE IF EXISTS `article_favorites`;
DROP TABLE IF EXISTS `chat_messages`;
DROP TABLE IF EXISTS `system_logs`;
DROP TABLE IF EXISTS `system_settings`;
DROP TABLE IF EXISTS `health_data_user`;
DROP TABLE IF EXISTS `health_articles`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `roles`;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================
-- 1) 角色表
-- =========================
CREATE TABLE `roles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(20) NOT NULL,
  `description` VARCHAR(100) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 2) 用户表（含钱包与隐私字段）
-- =========================
CREATE TABLE `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `wallet_address` VARCHAR(42) NULL,
  `private_key_hash` VARCHAR(128) NULL,
  `encrypted_profile_data` TEXT NULL,
  `public_profile_data` TEXT NULL,
  `profile_is_public` TINYINT(1) NOT NULL DEFAULT 0,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `role_id` INT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_wallet_address` (`wallet_address`),
  KEY `idx_users_role_id` (`role_id`),
  KEY `idx_users_is_active` (`is_active`),
  CONSTRAINT `fk_users_role_id`
    FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 3) 健康数据表（公开/私密 + 上链信息）
-- =========================
CREATE TABLE `health_data_user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `data_title` VARCHAR(255) NULL,
  `data_content` TEXT NULL,
  `encrypted_data_content` TEXT NULL,
  `pdf_data` LONGBLOB NULL,
  `encrypted_pdf_data` LONGBLOB NULL,
  `file_type` ENUM('text', 'pdf') NOT NULL DEFAULT 'text',
  `pdf_size` INT NULL,
  `is_public` TINYINT(1) NOT NULL DEFAULT 0,
  `onchain_data_id` VARCHAR(66) NULL,
  `onchain_tx_hash` VARCHAR(66) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_health_data_user_id` (`user_id`),
  KEY `idx_health_data_file_type` (`file_type`),
  KEY `idx_health_data_is_public` (`is_public`),
  CONSTRAINT `fk_health_data_user_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 4) 系统设置表
-- =========================
CREATE TABLE `system_settings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `setting_key` VARCHAR(100) NOT NULL,
  `setting_value` TEXT NOT NULL,
  `updated_by` INT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_system_settings_key` (`setting_key`),
  KEY `idx_system_settings_updated_by` (`updated_by`),
  CONSTRAINT `fk_system_settings_updated_by`
    FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 5) 系统日志表
-- =========================
CREATE TABLE `system_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `level` VARCHAR(20) NOT NULL DEFAULT 'INFO',
  `module` VARCHAR(100) NOT NULL,
  `action` VARCHAR(100) NOT NULL,
  `message` TEXT NOT NULL,
  `operator_id` INT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_system_logs_level` (`level`),
  KEY `idx_system_logs_module` (`module`),
  KEY `idx_system_logs_operator_id` (`operator_id`),
  KEY `idx_system_logs_created_at` (`created_at`),
  CONSTRAINT `fk_system_logs_operator_id`
    FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 6) 聊天记录表
-- =========================
CREATE TABLE `chat_messages` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `message` TEXT NOT NULL,
  `is_user` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_chat_messages_user_id` (`user_id`),
  CONSTRAINT `fk_chat_messages_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 7) 健康文章表
-- =========================
CREATE TABLE `health_articles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `category` VARCHAR(50) NOT NULL,
  `summary` VARCHAR(500) NULL,
  `content` TEXT NOT NULL,
  `cover_image` VARCHAR(500) NULL,
  `tags` VARCHAR(500) NULL,
  `view_count` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_health_articles_category` (`category`),
  KEY `idx_health_articles_view_count` (`view_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 8) 文章收藏表
-- =========================
CREATE TABLE `article_favorites` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `article_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_article_favorite_user_article` (`user_id`, `article_id`),
  KEY `idx_article_favorites_user_id` (`user_id`),
  KEY `idx_article_favorites_article_id` (`article_id`),
  CONSTRAINT `fk_article_favorites_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_article_favorites_article_id`
    FOREIGN KEY (`article_id`) REFERENCES `health_articles` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 9) 文章阅读历史表
-- =========================
CREATE TABLE `article_read_histories` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `article_id` INT NOT NULL,
  `read_count` INT NOT NULL DEFAULT 1,
  `last_read_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_article_read_user_article` (`user_id`, `article_id`),
  KEY `idx_article_read_histories_user_id` (`user_id`),
  KEY `idx_article_read_histories_article_id` (`article_id`),
  CONSTRAINT `fk_article_read_histories_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_article_read_histories_article_id`
    FOREIGN KEY (`article_id`) REFERENCES `health_articles` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- 10) 基础种子数据
-- =========================
INSERT INTO `roles` (`name`, `description`) VALUES
('admin', '系统管理员'),
('user', '普通用户');

INSERT INTO `system_settings` (`setting_key`, `setting_value`) VALUES
('project_name', '"健康管理系统"'),
('allow_user_register', 'true'),
('ai_enabled', 'true'),
('maintenance_mode', 'false'),
('default_health_data_public', 'false');
