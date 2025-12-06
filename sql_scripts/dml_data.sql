SET search_path TO bds, public;

--- 1. TRUNCATE VŠECH TABULEK KROMĚ STAFF_MEMBER A RESET SEKVENCI NA 1 ---
-- Staff_member musí být vynechán z TRUNCATE, protože tam je záznam ID 2.
-- Dáváme sem i roles, protože na ně staff_member odkazuje a sekvence roles musí být resetována.
TRUNCATE TABLE address, cart_item, coupon_code, customer_profile, discount_product, inventory, order_item, payment_transaction, orders, product_variant, product_image, product, category, roles, shipping_method, order_status, shopping_cart, user_account
RESTART IDENTITY CASCADE;

--- 2. ÚPRAVA SEKVENČNÍCH ČÍSEL PRO ZACHOVANÉ TABULKY ---

-- 2.1. ROLE: Vložíme role a ručně posuneme sekvenci na 6 (aby další role byla ID 6).
-- Ponecháváme vložení roles, jelikož staff_member (ID 2) na roli 1 odkazuje a ostatní tabulky musí být resetovány od 1.
INSERT INTO roles (role_name) VALUES
('Admin'),('Manager'),('Support'),('Warehouse'),('Sales');
-- Posun sekvence roles, pokud se do budoucna role budou vkládat
SELECT setval('roles_role_id_seq', 5, TRUE);

-- 2.2. STAFF_MEMBER: Nastavení sekvence na 3 (poslední ID + 1), protože záznam ID 2 již existuje.
-- Pokud by v databázi již nebyly žádné další záznamy kromě ID 2, toto zajistí, že další ID bude 3.
SELECT setval('staff_member_staff_id_seq', 2, TRUE);

--- 3. VKLÁDÁNÍ NOVÝCH DAT (Ostatní tabulky začínají od 1) ---

-- 3.1. Vkládání stavů objednávek (status_id 1-5)
INSERT INTO order_status (status_name) VALUES
('Pending'),('Processing'),('Shipped'),('Delivered'),('Cancelled');

-- 3.2. Vkládání metod dopravy (shipping_method_id 1-5)
INSERT INTO shipping_method (name, price, estimated_delivery) VALUES
('Standard',5.99,'3-5 days'), ('Express',12.99,'1-2 days'), ('Overnight',24.99,'1 day'),
('Pickup',0.00,'Same day'), ('International',29.99,'5-10 days');

-- 3.3. Vkládání slev (discount_id 1-5)
INSERT INTO discount (name, discount_percent, discount_amount, is_active) VALUES
('Summer Sale',10.00,NULL,TRUE), ('Winter Sale',NULL,20.00,TRUE), ('Black Friday',15.00,NULL,TRUE),
('New Year',NULL,25.00,TRUE), ('Clearance',20.00,NULL,FALSE);

-- 3.4. Vkládání kuponů (coupon_id 1-5, discount_id 1-5)
INSERT INTO coupon_code (discount_id, code, expiration_date, times_used) VALUES
(1,'SUMMER10','2025-06-30',0), (2,'WINTER20','2025-12-31',0), (3,'BLACK15','2025-11-30',0),
(4,'NY25','2025-01-31',0), (5,'CLEAR20','2025-03-31',0);

-- 3.5. Vkládání uživatelů (user_id 1-60)
INSERT INTO user_account (email, password_hash, is_active) VALUES
('alice@example.com', 'hash1', TRUE), ('bob@example.com', 'hash2', TRUE), ('charlie@example.com', 'hash3', TRUE),
('diana@example.com', 'hash4', TRUE), ('edward@example.com', 'hash5', TRUE), ('frank@example.com', 'hash6', TRUE),
('grace@example.com', 'hash7', TRUE), ('hannah@example.com', 'hash8', TRUE), ('ian@example.com', 'hash9', TRUE),
('julia@example.com', 'hash10', TRUE), ('kevin@example.com', 'hash11', TRUE), ('laura@example.com', 'hash12', TRUE),
('mike@example.com', 'hash13', TRUE), ('nina@example.com', 'hash14', TRUE), ('oscar@example.com', 'hash15', TRUE),
('paula@example.com', 'hash16', TRUE), ('quentin@example.com', 'hash17', TRUE), ('rachel@example.com', 'hash18', TRUE),
('steve@example.com', 'hash19', TRUE), ('tina@example.com', 'hash20', TRUE), ('uma@example.com', 'hash21', TRUE),
('victor@example.com', 'hash22', TRUE), ('wendy@example.com', 'hash23', TRUE), ('xander@example.com', 'hash24', TRUE),
('yvonne@example.com', 'hash25', TRUE), ('zach@example.com', 'hash26', TRUE), ('aaron@example.com', 'hash27', TRUE),
('beth@example.com', 'hash28', TRUE), ('carl@example.com', 'hash29', TRUE), ('dana@example.com', 'hash30', TRUE),
('evan@example.com', 'hash31', TRUE), ('fiona@example.com', 'hash32', TRUE), ('george@example.com', 'hash33', TRUE),
('holly@example.com', 'hash34', TRUE), ('ian2@example.com', 'hash35', TRUE), ('jenny@example.com', 'hash36', TRUE),
('kyle@example.com', 'hash37', TRUE), ('lara@example.com', 'hash38', TRUE), ('mark@example.com', 'hash39', TRUE),
('nora@example.com', 'hash40', TRUE), ('owen@example.com', 'hash41', TRUE), ('pam@example.com', 'hash42', TRUE),
('quinn@example.com', 'hash43', TRUE), ('ralph@example.com', 'hash44', TRUE), ('sara@example.com', 'hash45', TRUE),
('tom@example.com', 'hash46', TRUE), ('ursula@example.com', 'hash47', TRUE), ('victor2@example.com', 'hash48', TRUE),
('wanda@example.com', 'hash49', TRUE), ('xavier@example.com', 'hash50', TRUE), ('yasmin@example.com', 'hash51', TRUE),
('zane@example.com', 'hash52', TRUE), ('abby@example.com', 'hash53', TRUE), ('blake@example.com', 'hash54', TRUE),
('clara@example.com', 'hash55', TRUE), ('derek@example.com', 'hash56', TRUE), ('elena@example.com', 'hash57', TRUE),
('felix@example.com', 'hash58', TRUE), ('gina@example.com', 'hash59', TRUE), ('henry@example.com', 'hash60', TRUE);

-- 3.6. Vkládání zákaznických profilů (user_id 11-60, customer_id 1-50)
INSERT INTO customer_profile (user_id, first_name, last_name, date_of_birth, phone_number_enc) VALUES
(11,'Kevin','Lopez','1990-02-14', pgp_sym_encrypt('1234509876', 'key')), (12,'Laura','Gonzalez','1986-07-23', pgp_sym_encrypt('2345610987', 'key')),
(13,'Mike','Wilson','1992-11-19', pgp_sym_encrypt('3456721098', 'key')), (14,'Nina','Anderson','1988-05-30', pgp_sym_encrypt('4567832109', 'key')),
(15,'Oscar','Thomas','1995-10-02', pgp_sym_encrypt('5678943210', 'key')), (16,'Paula','Taylor','1991-01-21', pgp_sym_encrypt('6789054321', 'key')),
(17,'Quentin','Moore','1989-03-17', pgp_sym_encrypt('7890165432', 'key')), (18,'Rachel','Jackson','1993-12-12', pgp_sym_encrypt('8901276543', 'key')),
(19,'Steve','Martin','1990-09-09', pgp_sym_encrypt('9012387654', 'key')), (20,'Tina','Lee','1987-04-04', pgp_sym_encrypt('0123498765', 'key')),
(21,'Uma','Perez','1992-06-18', pgp_sym_encrypt('1234509876', 'key')), (22,'Victor','White','1991-08-29', pgp_sym_encrypt('2345610987', 'key')),
(23,'Wendy','Harris','1988-07-07', pgp_sym_encrypt('3456721098', 'key')), (24,'Xander','Clark','1994-05-05', pgp_sym_encrypt('4567832109', 'key')),
(25,'Yvonne','Lewis','1993-03-03', pgp_sym_encrypt('5678943210', 'key')), (26,'Zach','Lee','1995-09-08', pgp_sym_encrypt('6789054321', 'key')),
(27,'Aaron','Walker','1986-11-11', pgp_sym_encrypt('7890165432', 'key')), (28,'Beth','Hall','1990-01-02', pgp_sym_encrypt('8901276543', 'key')),
(29,'Carl','Allen','1992-02-12', pgp_sym_encrypt('9012387654', 'key')), (30,'Dana','Young','1989-05-23', pgp_sym_encrypt('0123498765', 'key')),
(31,'Evan','King','1991-07-14', pgp_sym_encrypt('1234509876', 'key')), (32,'Fiona','Wright','1988-09-30', pgp_sym_encrypt('2345610987', 'key')),
(33,'George','Scott','1993-10-19', pgp_sym_encrypt('3456721098', 'key')), (34,'Holly','Torres','1990-12-25', pgp_sym_encrypt('4567832109', 'key')),
(35,'Ian','Nguyen','1987-08-16', pgp_sym_encrypt('5678943210', 'key')), (36,'Jenny','Hill','1992-04-06', pgp_sym_encrypt('6789054321', 'key')),
(37,'Kyle','Flores','1989-03-27', pgp_sym_encrypt('7890165432', 'key')), (38,'Lara','Green','1991-06-09', pgp_sym_encrypt('8901276543', 'key')),
(39,'Mark','Adams','1994-11-18', pgp_sym_encrypt('9012387654', 'key')), (40,'Nora','Baker','1988-02-02', pgp_sym_encrypt('0123498765', 'key')),
(41,'Owen','Gonzales','1990-09-12', pgp_sym_encrypt('1234509876', 'key')), (42,'Pam','Nelson','1993-01-21', pgp_sym_encrypt('2345610987', 'key')),
(43,'Quinn','Carter','1986-05-15', pgp_sym_encrypt('3456721098', 'key')), (44,'Ralph','Mitchell','1992-07-07', pgp_sym_encrypt('4567832109', 'key')),
(45,'Sara','Perez','1995-03-03', pgp_sym_encrypt('5678943210', 'key')), (46,'Tom','Roberts','1989-11-11', pgp_sym_encrypt('6789054321', 'key')),
(47,'Ursula','Turner','1991-08-08', pgp_sym_encrypt('7890165432', 'key')), (48,'Victor','Phillips','1987-06-06', pgp_sym_encrypt('8901276543', 'key')),
(49,'Wanda','Campbell','1994-04-04', pgp_sym_encrypt('9012387654', 'key')), (50,'Xavier','Parker','1990-12-12', pgp_sym_encrypt('0123498765', 'key')),
(51,'Yasmin','Diaz','1991-01-15', pgp_sym_encrypt('1234509876', 'key')), (52,'Zane','Hughes','1989-02-20', pgp_sym_encrypt('2345610987', 'key')),
(53,'Abby','Cruz','1993-03-25', pgp_sym_encrypt('3456721098', 'key')), (54,'Blake','Foster','1988-04-30', pgp_sym_encrypt('4567832109', 'key')),
(55,'Clara','Gibson','1995-05-05', pgp_sym_encrypt('5678943210', 'key')), (56,'Derek','Hunter','1990-06-10', pgp_sym_encrypt('6789054321', 'key')),
(57,'Elena','Ingram','1987-07-15', pgp_sym_encrypt('7890165432', 'key')), (58,'Felix','Jenkins','1992-08-20', pgp_sym_encrypt('8901276543', 'key')),
(59,'Gina','Knight','1989-09-25', pgp_sym_encrypt('9012387654', 'key')), (60,'Henry','Lawson','1991-10-30', pgp_sym_encrypt('0123498765', 'key'));

--- 4. PRODUKTY A INVENTÁŘ ---

-- 4.1. Vkládání kategorií (category_id 1-5)
INSERT INTO category (parent_id, name) VALUES
(NULL,'Electronics'), (NULL,'Clothing'), (NULL,'Home & Kitchen'), (NULL,'Books'), (NULL,'Toys');

-- 4.2. Vkládání produktů (product_id 1-8, category_id 1-2)
INSERT INTO product (category_id, name, description, base_price, is_featured, created_at) VALUES
(1,'Smartphone Model 1','Latest smartphone',699.99,TRUE,NOW()), (1,'Smartphone Model 2','Latest smartphone',799.99,FALSE,NOW()),
(1,'Laptop Model 1','High performance laptop',1200.00,TRUE,NOW()), (1,'Laptop Model 2','High performance laptop',1500.00,FALSE,NOW()),
(2,'T-shirt Red','100% Cotton',19.99,FALSE,NOW()), (2,'T-shirt Blue','100% Cotton',19.99,FALSE,NOW()),
(2,'Jeans Slim Fit','Denim Jeans',49.99,TRUE,NOW()), (2,'Jeans Regular Fit','Denim Jeans',44.99,FALSE,NOW());

-- 4.3. Vkládání variant produktů (variant_id 1-5, product_id 1-3)
INSERT INTO product_variant (product_id, sku, attribute_value, additional_price) VALUES
(1,'SM1-BLK','Black',0.00), (1,'SM1-WHT','White',0.00), (2,'SM2-BLK','Black',0.00),
(2,'SM2-WHT','White',0.00), (3,'LP1-16GB','16GB RAM',150.00);

-- 4.4. Vkládání inventáře (inventory_id 1-5, variant_id 1-5)
INSERT INTO inventory (variant_id, quantity, location_code) VALUES
(1,100,'LOC1'), (2,80,'LOC1'), (3,50,'LOC2'), (4,60,'LOC2'), (5,30,'LOC3');

-- 4.5. Vkládání slev a produktů (discount_product_id 1-5, discount_id 1-4, product_id 1-5)
INSERT INTO discount_product (discount_id, product_id) VALUES
(1,1), (1,2), (2,3), (3,4), (4,5);

--- 5. KOŠÍKY A OBJEDNÁVKY ---

-- 5.1. Vkládání nákupních košíků (cart_id 1-5, customer_id 1-5)
INSERT INTO shopping_cart (customer_id, created_at) VALUES
(1,NOW()), (2,NOW()), (3,NOW()), (4,NOW()), (5,NOW());

-- 5.2. Vkládání položek nákupního košíku (cart_item_id 1-5, cart_id 1-5, variant_id 1-5)
INSERT INTO cart_item (cart_id, variant_id, quantity) VALUES
(1,1,2), (2,2,1), (3,3,1), (4,4,2), (5,5,1);

-- 5.3. Vkládání objednávek (order_id 1-5)
INSERT INTO orders (customer_id, status_id, shipping_method_id, order_date, total_amount, shipping_cost, is_paid) VALUES
(1,1,1,CURRENT_DATE,0.00,5.99,TRUE), (2,2,2,CURRENT_DATE,0.00,12.99,FALSE),
(3,3,3,CURRENT_DATE,0.00,24.99,TRUE), (4,4,4,CURRENT_DATE,0.00,0.00,FALSE),
(5,5,5,CURRENT_DATE,0.00,29.99,TRUE);

-- 5.4. Vkládání položek objednávky (order_item_id 1-5, order_id 1-5, variant_id 1-5)
-- Toto spustí trigger trg_after_order_item_insert a aktualizuje total_amount v orders.
INSERT INTO order_item (order_id, variant_id, quantity, unit_price) VALUES
(1,1,2,69.99), (2,2,1,199.99), (3,3,1,249.99), (4,4,2,44.99), (5,5,1,499.99);

-- 5.5. Vkládání platebních transakcí (transaction_id 1-5, order_id 1-5)
INSERT INTO payment_transaction (order_id, amount, payment_method, transaction_timestamp) VALUES
(1,139.98,'Credit Card',NOW()), (2,199.99,'PayPal',NOW()), (3,249.99,'Credit Card',NOW()),
(4,89.98,'Bank Transfer',NOW()), (5,499.99,'Credit Card',NOW());