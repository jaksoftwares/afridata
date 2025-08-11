/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.2-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.0.0.1    Database: afridata
-- ------------------------------------------------------
-- Server version	11.8.2-MariaDB-1 from Debian

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `accounts_loginattempt`
--

DROP TABLE IF EXISTS `accounts_loginattempt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_loginattempt` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `email` varchar(254) NOT NULL,
  `ip_address` char(39) NOT NULL,
  `success` tinyint(1) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `user_agent` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_loginattempt`
--

LOCK TABLES `accounts_loginattempt` WRITE;
/*!40000 ALTER TABLE `accounts_loginattempt` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `accounts_loginattempt` VALUES
(1,'joseph@gmail.com','127.0.0.1',0,'2025-07-24 08:53:48.521957','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(2,'joseph@gmail.com','127.0.0.1',1,'2025-07-24 08:54:41.864770','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(3,'violet@gmail.com','127.0.0.1',1,'2025-07-24 09:08:31.333028','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(4,'joseph@gmail.com','127.0.0.1',1,'2025-07-24 09:44:57.389933','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(5,'kirikajoseph@gmail.com','127.0.0.1',1,'2025-07-24 10:07:00.490642','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(6,'kirikajoseph@gmail.com','127.0.0.1',1,'2025-07-25 08:29:53.960219','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(7,'joseph@gmail.com','127.0.0.1',1,'2025-07-25 08:31:58.781770','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(8,'kirikajoseph@gmail.com','127.0.0.1',1,'2025-07-30 08:42:36.612823','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'),
(9,'joseph@gmail.com','127.0.0.1',0,'2025-07-30 08:44:06.165704','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36');
/*!40000 ALTER TABLE `accounts_loginattempt` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `accounts_tokenpurchase`
--

DROP TABLE IF EXISTS `accounts_tokenpurchase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_tokenpurchase` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `package` varchar(20) NOT NULL,
  `tokens_purchased` int(10) unsigned NOT NULL CHECK (`tokens_purchased` >= 0),
  `usd_amount` decimal(10,2) NOT NULL,
  `payment_status` varchar(10) NOT NULL,
  `stripe_payment_intent_id` varchar(255) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `accounts_tokenpurchase_user_id_860180f4_fk_custom_user_id` (`user_id`),
  CONSTRAINT `accounts_tokenpurchase_user_id_860180f4_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_tokenpurchase`
--

LOCK TABLES `accounts_tokenpurchase` WRITE;
/*!40000 ALTER TABLE `accounts_tokenpurchase` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `accounts_tokenpurchase` VALUES
(1,'basic',100,10.00,'pending',NULL,'2025-07-25 05:14:41.841901',NULL,1),
(2,'basic',100,10.00,'failed',NULL,'2025-07-25 05:18:03.917690',NULL,1),
(3,'basic',100,10.00,'failed',NULL,'2025-07-25 05:24:24.697790',NULL,1),
(4,'basic',100,10.00,'failed',NULL,'2025-07-25 05:30:58.171874',NULL,1),
(5,'basic',100,10.00,'failed',NULL,'2025-07-25 05:35:45.179751',NULL,1),
(6,'basic',100,10.00,'failed',NULL,'2025-07-25 05:37:08.972099',NULL,1),
(7,'basic',100,10.00,'failed',NULL,'2025-07-25 05:44:47.686083',NULL,1),
(8,'basic',100,10.00,'failed',NULL,'2025-07-25 05:48:07.148906',NULL,1),
(9,'basic',100,10.00,'failed',NULL,'2025-07-25 05:48:17.021615',NULL,1),
(10,'basic',100,10.00,'failed',NULL,'2025-07-25 05:50:47.717749',NULL,1),
(11,'basic',100,10.00,'failed',NULL,'2025-07-25 05:53:11.057362',NULL,1),
(12,'basic',100,10.00,'failed','ws_CO_250720250854464714703374','2025-07-25 05:54:45.254500',NULL,1),
(13,'basic',100,10.00,'pending','ws_CO_250720250901054714703374','2025-07-25 06:01:04.400883',NULL,1),
(14,'basic',100,10.00,'pending','ws_CO_250720250919210714703374','2025-07-25 06:19:19.792426',NULL,1),
(15,'basic',100,10.00,'failed',NULL,'2025-07-25 06:49:27.824581',NULL,1),
(16,'basic',100,10.00,'pending','ws_CO_250720251133105714703374','2025-07-25 08:33:08.567308',NULL,1),
(17,'basic',100,10.00,'pending','ws_CO_250720251156178714703374','2025-07-25 08:56:16.155139',NULL,3);
/*!40000 ALTER TABLE `accounts_tokenpurchase` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `accounts_userprofile`
--

DROP TABLE IF EXISTS `accounts_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_userprofile` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `website` varchar(200) NOT NULL,
  `location` varchar(100) NOT NULL,
  `organization` varchar(200) NOT NULL,
  `job_title` varchar(100) NOT NULL,
  `linkedin_url` varchar(200) NOT NULL,
  `github_url` varchar(200) NOT NULL,
  `twitter_handle` varchar(50) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `downloads_this_month` int(10) unsigned NOT NULL CHECK (`downloads_this_month` >= 0),
  `is_premium_subscriber` tinyint(1) NOT NULL,
  `last_month_reset` date NOT NULL,
  `monthly_download_limit` int(10) unsigned NOT NULL CHECK (`monthly_download_limit` >= 0),
  `premium_subscription_expires` datetime(6) DEFAULT NULL,
  `signup_bonus_awarded` tinyint(1) NOT NULL,
  `token_balance` int(10) unsigned NOT NULL CHECK (`token_balance` >= 0),
  `total_tokens_earned` int(10) unsigned NOT NULL CHECK (`total_tokens_earned` >= 0),
  `total_tokens_spent` int(10) unsigned NOT NULL CHECK (`total_tokens_spent` >= 0),
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `accounts_userprofile_user_id_92240672_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_userprofile`
--

LOCK TABLES `accounts_userprofile` WRITE;
/*!40000 ALTER TABLE `accounts_userprofile` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `accounts_userprofile` VALUES
(1,'','','','','','','',1,0,0,'2025-07-24',50,NULL,1,103,103,0),
(2,'','','','','','','',2,0,0,'2025-07-24',50,NULL,1,100,100,0),
(3,'','','','','','','',3,0,0,'2025-07-24',50,NULL,1,100,100,0);
/*!40000 ALTER TABLE `accounts_userprofile` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `admin_dashboard_adminlog`
--

DROP TABLE IF EXISTS `admin_dashboard_adminlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_dashboard_adminlog` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `action` varchar(20) NOT NULL,
  `model_name` varchar(100) NOT NULL,
  `object_id` varchar(100) NOT NULL,
  `object_repr` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `ip_address` char(39) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `admin_user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `admin_dashb_admin_u_3f5105_idx` (`admin_user_id`,`timestamp`),
  KEY `admin_dashb_action_7ac86c_idx` (`action`,`timestamp`),
  KEY `admin_dashb_model_n_75921b_idx` (`model_name`,`timestamp`),
  CONSTRAINT `admin_dashboard_admi_admin_user_id_5a77d151_fk_custom_us` FOREIGN KEY (`admin_user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_dashboard_adminlog`
--

LOCK TABLES `admin_dashboard_adminlog` WRITE;
/*!40000 ALTER TABLE `admin_dashboard_adminlog` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `admin_dashboard_adminlog` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `admin_dashboard_adminnotification`
--

DROP TABLE IF EXISTS `admin_dashboard_adminnotification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_dashboard_adminnotification` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `message` longtext NOT NULL,
  `notification_type` varchar(20) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_dashboard_adminnotification`
--

LOCK TABLES `admin_dashboard_adminnotification` WRITE;
/*!40000 ALTER TABLE `admin_dashboard_adminnotification` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `admin_dashboard_adminnotification` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `admin_dashboard_bulkaction`
--

DROP TABLE IF EXISTS `admin_dashboard_bulkaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_dashboard_bulkaction` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `action_name` varchar(100) NOT NULL,
  `model_name` varchar(100) NOT NULL,
  `total_items` int(10) unsigned NOT NULL CHECK (`total_items` >= 0),
  `processed_items` int(10) unsigned NOT NULL CHECK (`processed_items` >= 0),
  `failed_items` int(10) unsigned NOT NULL CHECK (`failed_items` >= 0),
  `status` varchar(20) NOT NULL,
  `error_message` longtext NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `admin_user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `admin_dashboard_bulk_admin_user_id_caea0111_fk_custom_us` (`admin_user_id`),
  CONSTRAINT `admin_dashboard_bulk_admin_user_id_caea0111_fk_custom_us` FOREIGN KEY (`admin_user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_dashboard_bulkaction`
--

LOCK TABLES `admin_dashboard_bulkaction` WRITE;
/*!40000 ALTER TABLE `admin_dashboard_bulkaction` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `admin_dashboard_bulkaction` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `admin_dashboard_dashboardsettings`
--

DROP TABLE IF EXISTS `admin_dashboard_dashboardsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_dashboard_dashboardsettings` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `key` varchar(100) NOT NULL,
  `value` longtext NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_dashboard_dashboardsettings`
--

LOCK TABLES `admin_dashboard_dashboardsettings` WRITE;
/*!40000 ALTER TABLE `admin_dashboard_dashboardsettings` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `admin_dashboard_dashboardsettings` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `admin_dashboard_systemmetrics`
--

DROP TABLE IF EXISTS `admin_dashboard_systemmetrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_dashboard_systemmetrics` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(100) NOT NULL,
  `metric_value` double NOT NULL,
  `metric_type` varchar(50) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`metadata`)),
  PRIMARY KEY (`id`),
  KEY `admin_dashb_metric__07d638_idx` (`metric_name`,`timestamp`),
  KEY `admin_dashb_metric__e8cfa0_idx` (`metric_type`,`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_dashboard_systemmetrics`
--

LOCK TABLES `admin_dashboard_systemmetrics` WRITE;
/*!40000 ALTER TABLE `admin_dashboard_systemmetrics` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `admin_dashboard_systemmetrics` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `api_apikey`
--

DROP TABLE IF EXISTS `api_apikey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `api_apikey` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `key` varchar(64) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `last_used` datetime(6) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `api_apikey_user_id_7ebe0e24_fk_custom_user_id` (`user_id`),
  CONSTRAINT `api_apikey_user_id_7ebe0e24_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `api_apikey`
--

LOCK TABLES `api_apikey` WRITE;
/*!40000 ALTER TABLE `api_apikey` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `api_apikey` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `api_apiusage`
--

DROP TABLE IF EXISTS `api_apiusage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `api_apiusage` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `endpoint` varchar(200) NOT NULL,
  `method` varchar(10) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `response_code` int(11) NOT NULL,
  `response_time` double NOT NULL,
  `ip_address` char(39) NOT NULL,
  `user_agent` longtext NOT NULL,
  `api_key_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `api_apiusag_api_key_f9d4f8_idx` (`api_key_id`,`timestamp`),
  KEY `api_apiusag_endpoin_2fdec3_idx` (`endpoint`,`timestamp`),
  CONSTRAINT `api_apiusage_api_key_id_cd3688bc_fk_api_apikey_id` FOREIGN KEY (`api_key_id`) REFERENCES `api_apikey` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `api_apiusage`
--

LOCK TABLES `api_apiusage` WRITE;
/*!40000 ALTER TABLE `api_apiusage` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `api_apiusage` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `auth_permission` VALUES
(1,'Can add log entry',1,'add_logentry'),
(2,'Can change log entry',1,'change_logentry'),
(3,'Can delete log entry',1,'delete_logentry'),
(4,'Can view log entry',1,'view_logentry'),
(5,'Can add permission',2,'add_permission'),
(6,'Can change permission',2,'change_permission'),
(7,'Can delete permission',2,'delete_permission'),
(8,'Can view permission',2,'view_permission'),
(9,'Can add group',3,'add_group'),
(10,'Can change group',3,'change_group'),
(11,'Can delete group',3,'delete_group'),
(12,'Can view group',3,'view_group'),
(13,'Can add content type',4,'add_contenttype'),
(14,'Can change content type',4,'change_contenttype'),
(15,'Can delete content type',4,'delete_contenttype'),
(16,'Can view content type',4,'view_contenttype'),
(17,'Can add session',5,'add_session'),
(18,'Can change session',5,'change_session'),
(19,'Can delete session',5,'delete_session'),
(20,'Can view session',5,'view_session'),
(21,'Can add dataset',6,'add_dataset'),
(22,'Can change dataset',6,'change_dataset'),
(23,'Can delete dataset',6,'delete_dataset'),
(24,'Can view dataset',6,'view_dataset'),
(25,'Can add comment',7,'add_comment'),
(26,'Can change comment',7,'change_comment'),
(27,'Can delete comment',7,'delete_comment'),
(28,'Can view comment',7,'view_comment'),
(29,'Can add premium purchase',8,'add_premiumpurchase'),
(30,'Can change premium purchase',8,'change_premiumpurchase'),
(31,'Can delete premium purchase',8,'delete_premiumpurchase'),
(32,'Can view premium purchase',8,'view_premiumpurchase'),
(33,'Can add token transaction',9,'add_tokentransaction'),
(34,'Can change token transaction',9,'change_tokentransaction'),
(35,'Can delete token transaction',9,'delete_tokentransaction'),
(36,'Can view token transaction',9,'view_tokentransaction'),
(37,'Can add download',10,'add_download'),
(38,'Can change download',10,'change_download'),
(39,'Can delete download',10,'delete_download'),
(40,'Can view download',10,'view_download'),
(41,'Can add referral',11,'add_referral'),
(42,'Can change referral',11,'change_referral'),
(43,'Can delete referral',11,'delete_referral'),
(44,'Can view referral',11,'view_referral'),
(45,'Can add login attempt',12,'add_loginattempt'),
(46,'Can change login attempt',12,'change_loginattempt'),
(47,'Can delete login attempt',12,'delete_loginattempt'),
(48,'Can view login attempt',12,'view_loginattempt'),
(49,'Can add User',13,'add_customuser'),
(50,'Can change User',13,'change_customuser'),
(51,'Can delete User',13,'delete_customuser'),
(52,'Can view User',13,'view_customuser'),
(53,'Can add user profile',14,'add_userprofile'),
(54,'Can change user profile',14,'change_userprofile'),
(55,'Can delete user profile',14,'delete_userprofile'),
(56,'Can view user profile',14,'view_userprofile'),
(57,'Can add token purchase',15,'add_tokenpurchase'),
(58,'Can change token purchase',15,'change_tokenpurchase'),
(59,'Can delete token purchase',15,'delete_tokenpurchase'),
(60,'Can view token purchase',15,'view_tokenpurchase'),
(61,'Can add topic',16,'add_topic'),
(62,'Can change topic',16,'change_topic'),
(63,'Can delete topic',16,'delete_topic'),
(64,'Can view topic',16,'view_topic'),
(65,'Can add thread',17,'add_thread'),
(66,'Can change thread',17,'change_thread'),
(67,'Can delete thread',17,'delete_thread'),
(68,'Can view thread',17,'view_thread'),
(69,'Can add post',18,'add_post'),
(70,'Can change post',18,'change_post'),
(71,'Can delete post',18,'delete_post'),
(72,'Can view post',18,'view_post'),
(73,'Can add user activity',19,'add_useractivity'),
(74,'Can change user activity',19,'change_useractivity'),
(75,'Can delete user activity',19,'delete_useractivity'),
(76,'Can view user activity',19,'view_useractivity'),
(77,'Can add post vote',20,'add_postvote'),
(78,'Can change post vote',20,'change_postvote'),
(79,'Can delete post vote',20,'delete_postvote'),
(80,'Can view post vote',20,'view_postvote'),
(81,'Can add api key',21,'add_apikey'),
(82,'Can change api key',21,'change_apikey'),
(83,'Can delete api key',21,'delete_apikey'),
(84,'Can view api key',21,'view_apikey'),
(85,'Can add api usage',22,'add_apiusage'),
(86,'Can change api usage',22,'change_apiusage'),
(87,'Can delete api usage',22,'delete_apiusage'),
(88,'Can view api usage',22,'view_apiusage'),
(89,'Can add admin notification',23,'add_adminnotification'),
(90,'Can change admin notification',23,'change_adminnotification'),
(91,'Can delete admin notification',23,'delete_adminnotification'),
(92,'Can view admin notification',23,'view_adminnotification'),
(93,'Can add Dashboard Setting',24,'add_dashboardsettings'),
(94,'Can change Dashboard Setting',24,'change_dashboardsettings'),
(95,'Can delete Dashboard Setting',24,'delete_dashboardsettings'),
(96,'Can view Dashboard Setting',24,'view_dashboardsettings'),
(97,'Can add bulk action',25,'add_bulkaction'),
(98,'Can change bulk action',25,'change_bulkaction'),
(99,'Can delete bulk action',25,'delete_bulkaction'),
(100,'Can view bulk action',25,'view_bulkaction'),
(101,'Can add system metrics',26,'add_systemmetrics'),
(102,'Can change system metrics',26,'change_systemmetrics'),
(103,'Can delete system metrics',26,'delete_systemmetrics'),
(104,'Can view system metrics',26,'view_systemmetrics'),
(105,'Can add admin log',27,'add_adminlog'),
(106,'Can change admin log',27,'change_adminlog'),
(107,'Can delete admin log',27,'delete_adminlog'),
(108,'Can view admin log',27,'view_adminlog');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `community_post`
--

DROP TABLE IF EXISTS `community_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_post` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` bigint(20) NOT NULL,
  `thread_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `community_post_author_id_a6c5f564_fk_custom_user_id` (`author_id`),
  KEY `community_post_thread_id_67d7c63c_fk_community_thread_id` (`thread_id`),
  CONSTRAINT `community_post_author_id_a6c5f564_fk_custom_user_id` FOREIGN KEY (`author_id`) REFERENCES `custom_user` (`id`),
  CONSTRAINT `community_post_thread_id_67d7c63c_fk_community_thread_id` FOREIGN KEY (`thread_id`) REFERENCES `community_thread` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_post`
--

LOCK TABLES `community_post` WRITE;
/*!40000 ALTER TABLE `community_post` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `community_post` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `community_postvote`
--

DROP TABLE IF EXISTS `community_postvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_postvote` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `vote` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `community_postvote_post_id_user_id_de51ab34_uniq` (`post_id`,`user_id`),
  KEY `community_postvote_user_id_a13ecd0b_fk_custom_user_id` (`user_id`),
  CONSTRAINT `community_postvote_post_id_d0443dbf_fk_community_post_id` FOREIGN KEY (`post_id`) REFERENCES `community_post` (`id`),
  CONSTRAINT `community_postvote_user_id_a13ecd0b_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_postvote`
--

LOCK TABLES `community_postvote` WRITE;
/*!40000 ALTER TABLE `community_postvote` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `community_postvote` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `community_thread`
--

DROP TABLE IF EXISTS `community_thread`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_thread` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `content` longtext NOT NULL,
  `is_pinned` tinyint(1) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `views` int(10) unsigned NOT NULL CHECK (`views` >= 0),
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` bigint(20) NOT NULL,
  `topic_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `community_thread_author_id_8cd7c473_fk_custom_user_id` (`author_id`),
  KEY `community_thread_topic_id_7e726a8b_fk_community_topic_id` (`topic_id`),
  CONSTRAINT `community_thread_author_id_8cd7c473_fk_custom_user_id` FOREIGN KEY (`author_id`) REFERENCES `custom_user` (`id`),
  CONSTRAINT `community_thread_topic_id_7e726a8b_fk_community_topic_id` FOREIGN KEY (`topic_id`) REFERENCES `community_topic` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_thread`
--

LOCK TABLES `community_thread` WRITE;
/*!40000 ALTER TABLE `community_thread` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `community_thread` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `community_topic`
--

DROP TABLE IF EXISTS `community_topic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_topic` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `icon` varchar(50) NOT NULL,
  `color` varchar(7) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_topic`
--

LOCK TABLES `community_topic` WRITE;
/*!40000 ALTER TABLE `community_topic` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `community_topic` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `community_useractivity`
--

DROP TABLE IF EXISTS `community_useractivity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_useractivity` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `last_seen` datetime(6) NOT NULL,
  `post_count` int(10) unsigned NOT NULL CHECK (`post_count` >= 0),
  `thread_count` int(10) unsigned NOT NULL CHECK (`thread_count` >= 0),
  `reputation` int(11) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `community_useractivity_user_id_4367c25b_fk_custom_user_id` (`user_id`),
  CONSTRAINT `community_useractivity_user_id_4367c25b_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_useractivity`
--

LOCK TABLES `community_useractivity` WRITE;
/*!40000 ALTER TABLE `community_useractivity` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `community_useractivity` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `custom_user`
--

DROP TABLE IF EXISTS `custom_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `custom_user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `email` varchar(254) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `bio` longtext NOT NULL,
  `profile_picture` varchar(100) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `is_verified` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `last_login_ip` char(39) DEFAULT NULL,
  `referral_code` varchar(10) DEFAULT NULL,
  `referred_by_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `custom_user_referral_code_48fb684b_uniq` (`referral_code`),
  KEY `custom_user_referred_by_id_31dd64ec_fk_custom_user_id` (`referred_by_id`),
  CONSTRAINT `custom_user_referred_by_id_31dd64ec_fk_custom_user_id` FOREIGN KEY (`referred_by_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `custom_user`
--

LOCK TABLES `custom_user` WRITE;
/*!40000 ALTER TABLE `custom_user` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `custom_user` VALUES
(1,'pbkdf2_sha256$260000$beG5VfLQedlqBpBSPnuqX1$rPzcW3pYlSWKPAF8va6SxHnu6NiIAI2EEY42mmZCYLc=','2025-07-25 08:31:58.711510',0,'joseph_kirika','','',0,1,'2025-07-24 08:54:41.563023','joseph@gmail.com','Joseph Kirika','0714603375','','',NULL,0,'2025-07-24 08:54:41.815391','2025-07-24 08:54:41.815604','127.0.0.1','1FBF0UGR',NULL),
(2,'pbkdf2_sha256$260000$4k9zHrfVQe1YrjJCcAcNwr$indAbSmY2e851PGKniO1tYAN9nZca2igeUPJTGSotAs=','2025-07-24 09:08:31.337201',0,'vayo','','',0,1,'2025-07-24 09:08:31.028211','violet@gmail.com','Violet Akhonya','0714703374','Addition of my projects','',NULL,0,'2025-07-24 09:08:31.320941','2025-07-24 09:08:31.320962','127.0.0.1','HH0Y872V',NULL),
(3,'pbkdf2_sha256$260000$Jw0FsGLX3sO2cW4I6WK1hj$oHUVWb+xuFVBPKrWwxFN3M1STfxyVj1bydXsvLWlCR4=','2025-07-30 08:42:36.535705',1,'Joseph','','',1,1,'2025-07-24 10:06:19.503746','kirikajoseph@gmail.com','Joseph Kirika','','','',NULL,0,'2025-07-24 10:06:19.674819','2025-07-24 10:06:19.674842','127.0.0.1','YSONYRG3',NULL);
/*!40000 ALTER TABLE `custom_user` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `custom_user_groups`
--

DROP TABLE IF EXISTS `custom_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `custom_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `customuser_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `custom_user_groups_customuser_id_group_id_ea14f886_uniq` (`customuser_id`,`group_id`),
  KEY `custom_user_groups_group_id_02874f21_fk_auth_group_id` (`group_id`),
  CONSTRAINT `custom_user_groups_customuser_id_8e3d0338_fk_custom_user_id` FOREIGN KEY (`customuser_id`) REFERENCES `custom_user` (`id`),
  CONSTRAINT `custom_user_groups_group_id_02874f21_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `custom_user_groups`
--

LOCK TABLES `custom_user_groups` WRITE;
/*!40000 ALTER TABLE `custom_user_groups` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `custom_user_groups` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `custom_user_user_permissions`
--

DROP TABLE IF EXISTS `custom_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `custom_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `customuser_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `custom_user_user_permiss_customuser_id_permission_f9232336_uniq` (`customuser_id`,`permission_id`),
  KEY `custom_user_user_per_permission_id_f82b5e3f_fk_auth_perm` (`permission_id`),
  CONSTRAINT `custom_user_user_per_customuser_id_ec2da4cb_fk_custom_us` FOREIGN KEY (`customuser_id`) REFERENCES `custom_user` (`id`),
  CONSTRAINT `custom_user_user_per_permission_id_f82b5e3f_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `custom_user_user_permissions`
--

LOCK TABLES `custom_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `custom_user_user_permissions` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `custom_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `dataset_comment`
--

DROP TABLE IF EXISTS `dataset_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_comment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `upvotes` int(10) unsigned NOT NULL CHECK (`upvotes` >= 0),
  `created_at` datetime(6) NOT NULL,
  `author_id` bigint(20) NOT NULL,
  `dataset_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataset_comment_author_id_6c07393c_fk_custom_user_id` (`author_id`),
  KEY `dataset_comment_dataset_id_bbc44f0b_fk_dataset_dataset_id` (`dataset_id`),
  CONSTRAINT `dataset_comment_author_id_6c07393c_fk_custom_user_id` FOREIGN KEY (`author_id`) REFERENCES `custom_user` (`id`),
  CONSTRAINT `dataset_comment_dataset_id_bbc44f0b_fk_dataset_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `dataset_dataset` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset_comment`
--

LOCK TABLES `dataset_comment` WRITE;
/*!40000 ALTER TABLE `dataset_comment` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `dataset_comment` VALUES
(1,'This is a great dataset',0,'2025-07-25 09:43:23.882454',3,1);
/*!40000 ALTER TABLE `dataset_comment` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `dataset_dataset`
--

DROP TABLE IF EXISTS `dataset_dataset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_dataset` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `file` varchar(100) NOT NULL,
  `dataset_type` varchar(20) NOT NULL,
  `bio` longtext NOT NULL,
  `topics` varchar(500) NOT NULL,
  `rating` double NOT NULL,
  `downloads` int(10) unsigned NOT NULL CHECK (`downloads` >= 0),
  `views` int(10) unsigned NOT NULL CHECK (`views` >= 0),
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` bigint(20) NOT NULL,
  `file_size_mb` double NOT NULL,
  `has_documentation` tinyint(1) NOT NULL,
  `is_premium` tinyint(1) NOT NULL,
  `metadata_quality_score` int(10) unsigned NOT NULL CHECK (`metadata_quality_score` >= 0),
  `premium_price_usd` decimal(10,2) DEFAULT NULL,
  `premium_token_discount` int(10) unsigned NOT NULL CHECK (`premium_token_discount` >= 0),
  `quality_tier` varchar(10) NOT NULL,
  `token_cost` int(10) unsigned NOT NULL CHECK (`token_cost` >= 0),
  PRIMARY KEY (`id`),
  KEY `dataset_dataset_author_id_3f34da0c_fk_custom_user_id` (`author_id`),
  CONSTRAINT `dataset_dataset_author_id_3f34da0c_fk_custom_user_id` FOREIGN KEY (`author_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset_dataset`
--

LOCK TABLES `dataset_dataset` WRITE;
/*!40000 ALTER TABLE `dataset_dataset` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `dataset_dataset` VALUES
(1,'Traffic Data','datasets/machine-readable-business-employment-data-mar-2025-quarter.csv','csv','This is a business dataset','AI',0,0,16,'2025-07-24 09:00:45.835466','2025-07-24 09:00:45.835549',1,3.626185417175293,0,0,0,NULL,0,'basic',5);
/*!40000 ALTER TABLE `dataset_dataset` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `dataset_download`
--

DROP TABLE IF EXISTS `dataset_download`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_download` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tokens_spent` int(10) unsigned NOT NULL CHECK (`tokens_spent` >= 0),
  `is_premium_download` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `dataset_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `premium_purchase_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dataset_download_user_id_dataset_id_49e2d863_uniq` (`user_id`,`dataset_id`),
  KEY `dataset_download_dataset_id_7e65d4b4_fk_dataset_dataset_id` (`dataset_id`),
  KEY `dataset_download_premium_purchase_id_3ef3c904_fk_dataset_p` (`premium_purchase_id`),
  CONSTRAINT `dataset_download_dataset_id_7e65d4b4_fk_dataset_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `dataset_dataset` (`id`),
  CONSTRAINT `dataset_download_premium_purchase_id_3ef3c904_fk_dataset_p` FOREIGN KEY (`premium_purchase_id`) REFERENCES `dataset_premiumpurchase` (`id`),
  CONSTRAINT `dataset_download_user_id_aa3c8d25_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset_download`
--

LOCK TABLES `dataset_download` WRITE;
/*!40000 ALTER TABLE `dataset_download` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `dataset_download` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `dataset_premiumpurchase`
--

DROP TABLE IF EXISTS `dataset_premiumpurchase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_premiumpurchase` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `payment_method` varchar(15) NOT NULL,
  `usd_amount` decimal(10,2) NOT NULL,
  `tokens_used` int(10) unsigned NOT NULL CHECK (`tokens_used` >= 0),
  `payment_status` varchar(10) NOT NULL,
  `stripe_payment_intent_id` varchar(255) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `dataset_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dataset_premiumpurchase_user_id_dataset_id_54de8285_uniq` (`user_id`,`dataset_id`),
  KEY `dataset_premiumpurch_dataset_id_73e8b294_fk_dataset_d` (`dataset_id`),
  CONSTRAINT `dataset_premiumpurch_dataset_id_73e8b294_fk_dataset_d` FOREIGN KEY (`dataset_id`) REFERENCES `dataset_dataset` (`id`),
  CONSTRAINT `dataset_premiumpurchase_user_id_ade47b55_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset_premiumpurchase`
--

LOCK TABLES `dataset_premiumpurchase` WRITE;
/*!40000 ALTER TABLE `dataset_premiumpurchase` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `dataset_premiumpurchase` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `dataset_referral`
--

DROP TABLE IF EXISTS `dataset_referral`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_referral` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `bonus_awarded` tinyint(1) NOT NULL,
  `bonus_amount` int(10) unsigned NOT NULL CHECK (`bonus_amount` >= 0),
  `created_at` datetime(6) NOT NULL,
  `referred_user_id` bigint(20) NOT NULL,
  `referrer_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dataset_referral_referrer_id_referred_user_id_95650c0c_uniq` (`referrer_id`,`referred_user_id`),
  KEY `dataset_referral_referred_user_id_e7e7d945_fk_custom_user_id` (`referred_user_id`),
  CONSTRAINT `dataset_referral_referred_user_id_e7e7d945_fk_custom_user_id` FOREIGN KEY (`referred_user_id`) REFERENCES `custom_user` (`id`),
  CONSTRAINT `dataset_referral_referrer_id_67fd3462_fk_custom_user_id` FOREIGN KEY (`referrer_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset_referral`
--

LOCK TABLES `dataset_referral` WRITE;
/*!40000 ALTER TABLE `dataset_referral` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `dataset_referral` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `dataset_tokentransaction`
--

DROP TABLE IF EXISTS `dataset_tokentransaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dataset_tokentransaction` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `transaction_type` varchar(20) NOT NULL,
  `amount` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `dataset_id` bigint(20) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataset_tokentransac_dataset_id_ce868fae_fk_dataset_d` (`dataset_id`),
  KEY `dataset_tokentransaction_user_id_84827302_fk_custom_user_id` (`user_id`),
  CONSTRAINT `dataset_tokentransac_dataset_id_ce868fae_fk_dataset_d` FOREIGN KEY (`dataset_id`) REFERENCES `dataset_dataset` (`id`),
  CONSTRAINT `dataset_tokentransaction_user_id_84827302_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataset_tokentransaction`
--

LOCK TABLES `dataset_tokentransaction` WRITE;
/*!40000 ALTER TABLE `dataset_tokentransaction` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `dataset_tokentransaction` VALUES
(1,'signup_bonus',50,'Welcome bonus for new users','2025-07-24 08:54:41.821890',NULL,1),
(2,'upload_bonus',3,'Upload bonus for \"Traffic Data\"','2025-07-24 09:00:45.918411',1,1),
(3,'signup_bonus',50,'Welcome bonus for new users','2025-07-24 09:08:31.324623',NULL,2),
(4,'signup_bonus',50,'Welcome bonus for new users','2025-07-24 10:06:19.710545',NULL,3);
/*!40000 ALTER TABLE `dataset_tokentransaction` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_custom_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_custom_user_id` FOREIGN KEY (`user_id`) REFERENCES `custom_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `django_content_type` VALUES
(13,'accounts','customuser'),
(12,'accounts','loginattempt'),
(15,'accounts','tokenpurchase'),
(14,'accounts','userprofile'),
(1,'admin','logentry'),
(27,'admin_dashboard','adminlog'),
(23,'admin_dashboard','adminnotification'),
(25,'admin_dashboard','bulkaction'),
(24,'admin_dashboard','dashboardsettings'),
(26,'admin_dashboard','systemmetrics'),
(21,'api','apikey'),
(22,'api','apiusage'),
(3,'auth','group'),
(2,'auth','permission'),
(18,'community','post'),
(20,'community','postvote'),
(17,'community','thread'),
(16,'community','topic'),
(19,'community','useractivity'),
(4,'contenttypes','contenttype'),
(7,'dataset','comment'),
(6,'dataset','dataset'),
(10,'dataset','download'),
(8,'dataset','premiumpurchase'),
(11,'dataset','referral'),
(9,'dataset','tokentransaction'),
(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `django_migrations` VALUES
(1,'contenttypes','0001_initial','2025-07-24 08:51:37.670970'),
(2,'contenttypes','0002_remove_content_type_name','2025-07-24 08:51:38.263884'),
(3,'auth','0001_initial','2025-07-24 08:51:40.286276'),
(4,'auth','0002_alter_permission_name_max_length','2025-07-24 08:51:40.742061'),
(5,'auth','0003_alter_user_email_max_length','2025-07-24 08:51:40.796778'),
(6,'auth','0004_alter_user_username_opts','2025-07-24 08:51:40.816339'),
(7,'auth','0005_alter_user_last_login_null','2025-07-24 08:51:40.827692'),
(8,'auth','0006_require_contenttypes_0002','2025-07-24 08:51:40.837052'),
(9,'auth','0007_alter_validators_add_error_messages','2025-07-24 08:51:40.857707'),
(10,'auth','0008_alter_user_username_max_length','2025-07-24 08:51:40.873121'),
(11,'auth','0009_alter_user_last_name_max_length','2025-07-24 08:51:40.888681'),
(12,'auth','0010_alter_group_name_max_length','2025-07-24 08:51:41.125121'),
(13,'auth','0011_update_proxy_permissions','2025-07-24 08:51:41.195112'),
(14,'auth','0012_alter_user_first_name_max_length','2025-07-24 08:51:41.215901'),
(15,'accounts','0001_initial','2025-07-24 08:51:44.118174'),
(16,'accounts','0002_customuser_referral_code_customuser_referred_by_and_more','2025-07-24 08:51:48.926230'),
(17,'accounts','0003_alter_customuser_referral_code','2025-07-24 08:51:49.336646'),
(18,'admin','0001_initial','2025-07-24 08:51:50.191015'),
(19,'admin','0002_logentry_remove_auto_add','2025-07-24 08:51:50.256899'),
(20,'admin','0003_logentry_add_action_flag_choices','2025-07-24 08:51:50.278506'),
(21,'admin_dashboard','0001_initial','2025-07-24 08:51:53.257186'),
(22,'api','0001_initial','2025-07-24 08:51:55.107056'),
(23,'community','0001_initial','2025-07-24 08:51:59.403978'),
(24,'dataset','0001_initial','2025-07-24 08:52:01.725387'),
(25,'dataset','0002_alter_dataset_dataset_type','2025-07-24 08:52:02.199389'),
(26,'dataset','0003_dataset_file_size_mb_dataset_has_documentation_and_more','2025-07-24 08:52:14.346299'),
(27,'sessions','0001_initial','2025-07-24 08:52:14.877007');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `django_session` VALUES
('1ouh6lm16l66shujf3jqtlosh7nw169y','.eJxVjEEOwiAURO_C2pC2fArt0r1nIB_4WNSAgTbRGO-uJF3oapKZN-_FDG7rYrZKxUTPZibY4bez6K6U2uAvmM6Zu5zWEi1vCN_Xyk_Z0-24s3-CBevyfZMVpBGUskHQ0HmHMEnsYYROoJ6kdcFPMNLge0swiiCUBm1BShVaNGmlWmNOhh73WJ5s7t4fnT0_Ig:1uesqq:QPRkt17i2yf96LNwmrD4JofVnbiFbQfCxlHxYI1eT48','2025-08-07 10:07:00.526621'),
('ehvfww8xox2ukrfyz11mm8wcw5t2zpyu','.eJxVjEEOwiAURO_C2pC2fArt0r1nIB_4WNSAgTbRGO-uJF3oapKZN-_FDG7rYrZKxUTPZibY4bez6K6U2uAvmM6Zu5zWEi1vCN_Xyk_Z0-24s3-CBevyfZMVpBGUskHQ0HmHMEnsYYROoJ6kdcFPMNLge0swiiCUBm1BShVaNGmlWmNOhh73WJ5s7t4fnT0_Ig:1ufDoP:ELS73AJ2lUEyxrAMAmiDxtHFV4RCGWe9lBwzjzbA9DM','2025-08-08 08:29:53.977131'),
('jezyfde26loc677sddy64e1i0pzw2jmr','.eJxVjDkOwjAURO_iGlneLVHScwbrLzYOIFuKkyri7iRSCihn3pvZRIJ1qWkdeU4Ti6sw4vLbIdArtwPwE9qjS-ptmSeUhyJPOuS9c37fTvfvoMKo-9pHxqhVpBIChowciQyBBla-6IJOsTKkSBUAwBKyddaCLy47t0cvPl8SJTkt:1uerwF:4agkSICY038igBD6OKEzQcmdocVspZh3d6wzQIrFaa4','2025-08-07 09:08:31.404453'),
('ug1ubb8d5zwt0oa2aw9847uke6v3x5sn','.eJxVjEEOwiAURO_C2hB-gUq7dO8ZyAc-FjVgoE00xrvbJl3ocmbevDezuMyTXRpVmwIbGbDDb-fQ3yhvQ7hivhTuS55rcnxD-L42fi6B7qed_RNM2Kb1LY3qvUHEeMQ4aJReKXDoHKExEDswIIRcs-h033utJLkI0JHWQxBi2KSNWkslW3o-Un2xUXy-ngs_Hw:1ufDqQ:OWMHh1r9KedlRF9NheANZhPat52f98sAtn9UsEV2VvY','2025-08-08 08:31:58.803264');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
commit;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-08-01 10:26:18
