CREATE SCHEMA IF NOT EXISTS bds;
SET search_path TO bds, public;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS user_account (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_profile (
    customer_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES user_account(user_id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    phone_number_enc BYTEA 
);

CREATE TABLE IF NOT EXISTS address (
    address_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customer_profile(customer_id),
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    is_billing BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(30) NOT NULL 
);

-- TADY JSEM PŘIDAL TEN SLOUPEC
CREATE TABLE IF NOT EXISTS staff_member (
    staff_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role_id INT NOT NULL REFERENCES roles(role_id),
    hire_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS category (
    category_id SERIAL PRIMARY KEY,
    parent_id INT REFERENCES category(category_id),
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS product (
    product_id SERIAL PRIMARY KEY,
    category_id INT NOT NULL REFERENCES category(category_id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    internal_rating DECIMAL(2,1) 
);

CREATE TABLE IF NOT EXISTS product_image (
    image_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    url VARCHAR(255) NOT NULL,
    sort_order INT
);

CREATE TABLE IF NOT EXISTS product_variant (
    variant_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES product(product_id),
    sku VARCHAR(50) NOT NULL,
    attribute_value VARCHAR(100) NOT NULL,
    additional_price DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id SERIAL PRIMARY KEY,
    variant_id INT NOT NULL REFERENCES product_variant(variant_id),
    quantity INT NOT NULL DEFAULT 0,
    location_code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS shopping_cart (
    cart_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customer_profile(customer_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_item (
    cart_item_id SERIAL PRIMARY KEY,
    cart_id INT NOT NULL REFERENCES shopping_cart(cart_id),
    variant_id INT NOT NULL REFERENCES product_variant(variant_id),
    quantity INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS order_status (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS shipping_method (
    shipping_method_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    estimated_delivery VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customer_profile(customer_id),
    status_id INT NOT NULL REFERENCES order_status(status_id),
    shipping_method_id INT NOT NULL REFERENCES shipping_method(shipping_method_id),
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_cost DECIMAL(10,2) NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS order_item (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    variant_id INT NOT NULL REFERENCES product_variant(variant_id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_transaction (
    transaction_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS discount (
    discount_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    discount_percent DECIMAL(5,2),
    discount_amount DECIMAL(10,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS coupon_code (
    coupon_id SERIAL PRIMARY KEY,
    discount_id INT NOT NULL REFERENCES discount(discount_id),
    code VARCHAR(50) NOT NULL UNIQUE,
    expiration_date DATE NOT NULL,
    times_used INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS discount_product (
    discount_product_id SERIAL PRIMARY KEY,
    discount_id INT NOT NULL REFERENCES discount(discount_id),
    product_id INT NOT NULL REFERENCES product(product_id)
);

CREATE INDEX IF NOT EXISTS idx_customer_profile_last_name 
ON customer_profile (last_name);

CREATE OR REPLACE VIEW v_payment_summary AS
SELECT
    pt.transaction_id,
    o.order_id,
    cp.first_name,
    cp.last_name,
    pt.amount,
    pt.payment_method,
    pt.transaction_timestamp
FROM payment_transaction pt
JOIN orders o ON pt.order_id = o.order_id
JOIN customer_profile cp ON o.customer_id = cp.customer_id;

CREATE OR REPLACE VIEW v_app_user_safe AS
SELECT user_id, email, is_active, created_at
FROM user_account;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_inventory_by_category_location AS
SELECT
    c.name AS category_name,
    i.location_code,
    SUM(i.quantity) AS total_stock
FROM inventory i
JOIN product_variant pv ON i.variant_id = pv.variant_id
JOIN product p ON pv.product_id = p.product_id
JOIN category c ON p.category_id = c.category_id
GROUP BY c.name, i.location_code
HAVING SUM(i.quantity) > 50;

CREATE OR REPLACE FUNCTION days_until_coupon_expires(coupon_id_input INT)
RETURNS INT
LANGUAGE sql
AS $$
    SELECT (expiration_date - CURRENT_DATE)::INT
    FROM coupon_code
    WHERE coupon_id = coupon_id_input;
$$;

CREATE OR REPLACE PROCEDURE update_order_paid_status(trans_id INT)
LANGUAGE SQL
AS $$
    UPDATE orders
    SET is_paid = TRUE
    WHERE order_id = (
        SELECT order_id FROM payment_transaction WHERE transaction_id = trans_id
    ) AND is_paid = FALSE;
$$;

CREATE OR REPLACE FUNCTION update_order_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(quantity * unit_price), 0)
        FROM order_item
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_after_order_item_insert ON order_item;
CREATE TRIGGER trg_after_order_item_insert
AFTER INSERT ON order_item
FOR EACH ROW
EXECUTE FUNCTION update_order_total();

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bds-app') THEN
      CREATE ROLE "bds-app" WITH LOGIN PASSWORD 'admin';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bds-script') THEN
      CREATE ROLE "bds-script" WITH LOGIN PASSWORD 'admin';
  END IF;
END
$$;

GRANT USAGE ON SCHEMA bds TO "bds-app";
GRANT USAGE ON SCHEMA bds TO "bds-script";

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bds TO "bds-app";
GRANT SELECT, INSERT, UPDATE, DELETE ON bds.order_item TO "bds-app";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bds TO "bds-app";

GRANT SELECT ON bds.product TO "bds-script";
GRANT SELECT ON bds.category TO "bds-script";

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA bds TO "bds-app";
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA bds TO "bds-app";