-- ============================================================
-- Ecommerce Orders System - Database Schema
-- Generated from Django migrations
-- Compatible with PostgreSQL
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- Product Table
-- Stores all available products with pricing and stock info
-- ------------------------------------------------------------
CREATE TABLE "ecommerce_product" (
    "id"          SERIAL       NOT NULL PRIMARY KEY,
    "name"        VARCHAR(255) NOT NULL,
    "description" TEXT         NULL,
    "price"       DECIMAL      NOT NULL,
    "stock"       INTEGER      NOT NULL CHECK ("stock" >= 0)
);

-- ------------------------------------------------------------
-- User Table (Custom User extending Django's AbstractUser)
-- Adds role field: 'admin' or 'customer'
-- ------------------------------------------------------------
CREATE TABLE "ecommerce_user" (
    "id"           SERIAL       NOT NULL PRIMARY KEY,
    "password"     VARCHAR(128) NOT NULL,
    "last_login"   TIMESTAMP    NULL,
    "is_superuser" BOOLEAN      NOT NULL,
    "username"     VARCHAR(150) NOT NULL UNIQUE,
    "first_name"   VARCHAR(150) NOT NULL,
    "last_name"    VARCHAR(150) NOT NULL,
    "email"        VARCHAR(254) NOT NULL,
    "is_staff"     BOOLEAN      NOT NULL,
    "is_active"    BOOLEAN      NOT NULL,
    "date_joined"  TIMESTAMP    NOT NULL,
    "role"         VARCHAR(10)  NOT NULL DEFAULT 'customer'
);

-- User-Group M2M
CREATE TABLE "ecommerce_user_groups" (
    "id"       SERIAL  NOT NULL PRIMARY KEY,
    "user_id"  BIGINT  NOT NULL REFERENCES "ecommerce_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "group_id" INTEGER NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- User-Permission M2M
CREATE TABLE "ecommerce_user_user_permissions" (
    "id"            SERIAL  NOT NULL PRIMARY KEY,
    "user_id"       BIGINT  NOT NULL REFERENCES "ecommerce_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "permission_id" INTEGER NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ------------------------------------------------------------
-- Order Table
-- Each order belongs to one customer; can have many OrderItems
-- Status: pending | completed | cancelled
-- ------------------------------------------------------------
CREATE TABLE "ecommerce_order" (
    "id"           SERIAL      NOT NULL PRIMARY KEY,
    "status"       VARCHAR(20) NOT NULL DEFAULT 'pending',
    "total_amount" DECIMAL     NOT NULL DEFAULT 0.00,
    "created_at"   TIMESTAMP   NOT NULL,
    "updated_at"   TIMESTAMP   NOT NULL,
    "user_id"      BIGINT      NOT NULL REFERENCES "ecommerce_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ------------------------------------------------------------
-- OrderItem Table
-- Line items for each order; links Order <-> Product
-- Price is stored at time of order (snapshot)
-- ------------------------------------------------------------
CREATE TABLE "ecommerce_orderitem" (
    "id"         SERIAL   NOT NULL PRIMARY KEY,
    "quantity"   INTEGER  NOT NULL CHECK ("quantity" > 0),
    "price"      DECIMAL  NOT NULL,
    "order_id"   BIGINT   NOT NULL REFERENCES "ecommerce_order" ("id") DEFERRABLE INITIALLY DEFERRED,
    "product_id" BIGINT   NOT NULL REFERENCES "ecommerce_product" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
CREATE UNIQUE INDEX "ecommerce_user_groups_user_id_group_id_uniq"
    ON "ecommerce_user_groups" ("user_id", "group_id");

CREATE INDEX "ecommerce_user_groups_user_id"
    ON "ecommerce_user_groups" ("user_id");

CREATE INDEX "ecommerce_user_groups_group_id"
    ON "ecommerce_user_groups" ("group_id");

CREATE UNIQUE INDEX "ecommerce_user_user_permissions_user_id_permission_id_uniq"
    ON "ecommerce_user_user_permissions" ("user_id", "permission_id");

CREATE INDEX "ecommerce_user_user_permissions_user_id"
    ON "ecommerce_user_user_permissions" ("user_id");

CREATE INDEX "ecommerce_user_user_permissions_permission_id"
    ON "ecommerce_user_user_permissions" ("permission_id");

CREATE INDEX "ecommerce_order_user_id"
    ON "ecommerce_order" ("user_id");

CREATE INDEX "ecommerce_orderitem_order_id"
    ON "ecommerce_orderitem" ("order_id");

CREATE INDEX "ecommerce_orderitem_product_id"
    ON "ecommerce_orderitem" ("product_id");

COMMIT;
