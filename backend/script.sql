-- Drop tables if they exist
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS brands;
DROP TABLE IF EXISTS outlets;

-- Create brands table
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE,
    category VARCHAR(50),
    established_year INTEGER
);

-- Create outlets table
CREATE TABLE outlets (
    outlet_id SERIAL PRIMARY KEY,
    outlet_name VARCHAR(100),
    location VARCHAR(100),
    size_sqft INTEGER
);

-- Create sales table
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    outlet_id INTEGER REFERENCES outlets(outlet_id),
    sale_date DATE,
    units_sold INTEGER,
    revenue DECIMAL(10,2),
    promotion_flag BOOLEAN,
    brand_name VARCHAR(100),
    product_name VARCHAR(200)
);

-- Insert brand data with similar names
INSERT INTO brands (brand_name, category, established_year) VALUES
    ('TastyBites', 'Snacks', 1995),
    ('Tasty Bites', 'Ready Meals', 2000),
    ('AquaPure', 'Beverages', 1988),
    ('Aqua-Pure', 'Water', 1992),
    ('GloSkin', 'Personal Care', 2005),
    ('NutriVital', 'Health Foods', 1999),
    ('FreshFarms', 'Dairy', 1985),
    ('EcoClean', 'Household', 2010),
    ('PetJoy', 'Pet Care', 2008),
    ('GreenLife', 'Organic Foods', 2015);

-- Insert outlet data with duplicate name patterns
INSERT INTO outlets (outlet_name, location, size_sqft) VALUES
    ('Walmart 1638', 'New York', 125000),
    ('Walmart 390', 'Los Angeles', 95000),
    ('Target 472', 'Chicago', 85000),
    ('Target 183', 'Houston', 75000),
    ('Costco 892', 'Phoenix', 145000),
    ('Costco 567', 'Philadelphia', 135000),
    ('Kroger 238', 'San Antonio', 65000),
    ('Kroger 445', 'San Diego', 55000),
    ('Safeway 721', 'Dallas', 45000),
    ('Safeway 902', 'San Jose', 42000),
    ('Whole Foods 112', 'Austin', 38000),
    ('Whole Foods 334', 'Jacksonville', 36000),
    ('Trader Joe''s 445', 'San Francisco', 25000),
    ('Trader Joe''s 667', 'Columbus', 22000),
    ('Local Market 123', 'Indianapolis', 15000);

-- Function to generate random product names for a brand
CREATE OR REPLACE FUNCTION generate_product_name(brand VARCHAR) 
RETURNS VARCHAR AS $$
DECLARE
    product_types TEXT[] := ARRAY['Cereal', 'Cookies', 'Chips', 'Drink', 'Soap', 'Shampoo', 'Snacks', 'Juice'];
    sizes TEXT[] := ARRAY['100g', '200g', '500g', '1kg', '250ml', '500ml', '1L'];
BEGIN
    RETURN brand || ' ' || 
           product_types[floor(random() * array_length(product_types, 1) + 1)] || ' ' ||
           sizes[floor(random() * array_length(sizes, 1) + 1)];
END;
$$ LANGUAGE plpgsql;

-- Create a temporary sequence for cycling through brands
CREATE TEMPORARY SEQUENCE brand_cycle START 1;

-- Insert sales data with intentional case variations in brand names
INSERT INTO sales (outlet_id, sale_date, units_sold, revenue, promotion_flag, brand_name, product_name)
SELECT 
    floor(random() * 15 + 1)::integer as outlet_id,
    current_date - (floor(random() * 365 + 1)::integer || ' days')::interval as sale_date,
    floor(random() * 100 + 1)::integer as units_sold,
    (random() * 1000 + 10)::decimal(10,2) as revenue,
    random() < 0.3 as promotion_flag,
    CASE 
        -- 3% null brand names
        WHEN random() < 0.03 THEN NULL
        -- 5% case variations in brand names
        WHEN random() < 0.05 THEN 
            CASE floor(random() * 3)::integer
                WHEN 0 THEN 'tastybites'  -- all lowercase
                WHEN 1 THEN 'AQUAPURE'    -- all uppercase
                ELSE 'gloSkin'            -- mixed case variation
            END
        ELSE (
            SELECT brand_name 
            FROM brands 
            WHERE brand_name NOT IN ('GreenLife', 'PetJoy')  -- These brands will have no sales
            ORDER BY ((nextval('brand_cycle') - 1) % 8) + 1  -- Cycle through 8 brands
            LIMIT 1
        )
    END as brand_name,
    NULL as product_name  -- Will be filled in next step
FROM generate_series(1, 1200);

-- Drop the temporary sequence
DROP SEQUENCE brand_cycle;

-- Update product names based on brand names
UPDATE sales 
SET product_name = generate_product_name(brand_name)
WHERE brand_name IS NOT NULL;

