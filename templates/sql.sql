mysql> use pharmacy_db;
Database changed
mysql> show tables;
+-----------------------+
| Tables_in_pharmacy_db |
+-----------------------+
| customer              |
| inventory             |
| medicine              |
| supplier              |
| users                 |
+-----------------------+
5 rows in set (0.01 sec)

mysql> desc customer;
+-------------+--------------+------+-----+---------+----------------+
| Field       | Type         | Null | Key | Default | Extra          |
+-------------+--------------+------+-----+---------+----------------+
| customer_id | int          | NO   | PRI | NULL    | auto_increment |
| name        | varchar(100) | NO   |     | NULL    |                |
| phone       | varchar(15)  | NO   |     | NULL    |                |
| email       | varchar(100) | YES  | UNI | NULL    |                |
| is_admin    | tinyint(1)   | YES  |     | 0       |                |
| password    | varchar(255) | NO   |     | NULL    |                |
+-------------+--------------+------+-----+---------+----------------+
6 rows in set (0.01 sec)

mysql> desc inventory;
+--------------+-------------+------+-----+---------+-------+
| Field        | Type        | Null | Key | Default | Extra |
+--------------+-------------+------+-----+---------+-------+
| inventory_id | varchar(10) | NO   | PRI | NULL    |       |
| medicine_id  | varchar(10) | YES  | MUL | NULL    |       |
| supplier_id  | varchar(10) | YES  | MUL | NULL    |       |
| stock_added  | int         | NO   |     | NULL    |       |
| date_added   | date        | NO   |     | NULL    |       |
+--------------+-------------+------+-----+---------+-------+
5 rows in set (0.01 sec)

mysql> desc medicine;
+-------------------+---------------+------+-----+---------+-------+
| Field             | Type          | Null | Key | Default | Extra |
+-------------------+---------------+------+-----+---------+-------+
| medicine_id       | varchar(10)   | NO   | PRI | NULL    |       |
| name              | varchar(100)  | NO   |     | NULL    |       |
| category          | varchar(50)   | YES  |     | NULL    |       |
| price             | decimal(10,2) | NO   |     | NULL    |       |
| expiry_date       | date          | NO   |     | NULL    |       |
| quantity_in_stock | int           | NO   |     | NULL    |       |
+-------------------+---------------+------+-----+---------+-------+
6 rows in set (0.00 sec)

mysql> desc supplier;
+-------------+--------------+------+-----+---------+-------+
| Field       | Type         | Null | Key | Default | Extra |
+-------------+--------------+------+-----+---------+-------+
| supplier_id | varchar(10)  | NO   | PRI | NULL    |       |
| name        | varchar(100) | NO   |     | NULL    |       |
| contact     | varchar(15)  | NO   |     | NULL    |       |
| address     | text         | YES  |     | NULL    |       |
+-------------+--------------+------+-----+---------+-------+
4 rows in set (0.01 sec)

mysql> desc user;
ERROR 1146 (42S02): Table 'pharmacy_db.user' doesn't exist
mysql> desc users;
+------------+--------------+------+-----+-------------------+-------------------+
| Field      | Type         | Null | Key | Default           | Extra             |
+------------+--------------+------+-----+-------------------+-------------------+
| id         | int          | NO   | PRI | NULL              | auto_increment    |
| name       | varchar(100) | NO   |     | NULL              |                   |
| email      | varchar(100) | NO   | UNI | NULL              |                   |
| password   | varchar(255) | NO   |     | NULL              |                   |
| created_at | timestamp    | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+------------+--------------+------+-----+-------------------+-------------------+
5 rows in set (0.00 sec)



mysql> desc carts;
+-------------+-----------+------+-----+-------------------+-----------------------------------------------+
| Field       | Type      | Null | Key | Default           | Extra                                         |
+-------------+-----------+------+-----+-------------------+-----------------------------------------------+
| cart_id     | int       | NO   | PRI | NULL              | auto_increment                                |
| customer_id | int       | NO   | MUL | NULL              |                                               |
| created_at  | timestamp | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED                             |
| updated_at  | timestamp | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
+-------------+-----------+------+-----+-------------------+-----------------------------------------------+
4 rows in set (0.03 sec)

mysql> desc carts_items;
ERROR 1146 (42S02): Table 'pharmacy_db.carts_items' doesn't exist
mysql> desc cart_items;
+--------------+-------------+------+-----+-------------------+-------------------+
| Field        | Type        | Null | Key | Default           | Extra             |
+--------------+-------------+------+-----+-------------------+-------------------+
| cart_item_id | int         | NO   | PRI | NULL              | auto_increment    |
| cart_id      | int         | NO   | MUL | NULL              |                   |
| medicine_id  | varchar(10) | NO   | MUL | NULL              |                   |
| quantity     | int         | NO   |     | NULL              |                   |
| added_at     | timestamp   | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+--------------+-------------+------+-----+-------------------+-------------------+
5 rows in set (0.01 sec)
