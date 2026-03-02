

CREATE DATABASE IF NOT EXISTS `health`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `health`;

CREATE TABLE IF NOT EXISTS `roles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(20) NOT NULL,
  `description` VARCHAR(100) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `role_id` INT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`),
  KEY `idx_users_role_id` (`role_id`),
  CONSTRAINT `fk_users_role_id`
    FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


USE `health`;
-- 健康知识文章表
CREATE TABLE IF NOT EXISTS health_articles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  title VARCHAR(200) NOT NULL COMMENT '文章标题',
  category ENUM(
    '慢性病管理',
    '饮食营养',
    '心理健康',
    '运动健身',
    '老年健康',
    '儿童健康'
  ) NOT NULL COMMENT '文章分类',
  summary VARCHAR(500) DEFAULT NULL COMMENT '摘要',
  content LONGTEXT NOT NULL COMMENT '正文内容',
  cover_image VARCHAR(500) DEFAULT NULL COMMENT '封面图URL',
  tags JSON DEFAULT NULL COMMENT '标签JSON数组，如 [\"高血压\",\"控盐\"]',
  view_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览量',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),

  -- 索引：分类、时间、热度
  KEY idx_category (category),
  KEY idx_created_at (created_at),
  KEY idx_view_count (view_count),

  -- 搜索索引：标题+摘要+正文
  FULLTEXT KEY ft_title_summary_content (title, summary, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康知识文章表';


CREATE TABLE health_data_user (
    id INT AUTO_INCREMENT PRIMARY KEY,     -- 健康数据记录的唯一ID
    user_id INT NOT NULL,                  -- 关联用户ID
    data_title VARCHAR(255),               -- 健康数据的标题
    data_content LONGTEXT,                 -- 健康数据的文本内容
    pdf_data LONGBLOB,                     -- PDF文件的二进制数据
    file_type ENUM('text', 'pdf') NOT NULL, -- 数据类型（'text'表示文本，'pdf'表示PDF文件）
    pdf_size INT,                          -- PDF文件大小（字节），仅在file_type为'pdf'时有效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id)  -- 关联用户表
);











