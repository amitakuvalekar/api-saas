import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import csv
from typing import List, Optional
from urllib.parse import unquote

# Database credentials
DB_HOST = os.getenv("DB_HOST", "sql.freedb.tech")
DB_USER = os.getenv("DB_USER", "freedb_amysocial")
DB_PASSWORD = os.getenv("DB_PASSWORD", "nQ2p!a&EFq%EgsK")
DB_NAME = os.getenv("DB_NAME", "freedb_winedb")
DB_PORT = int(os.getenv("DB_PORT", 3306))

app = FastAPI()

def get_db_connection():
    try:
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        return cnx
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def create_database_and_table():
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()

        # Drop table if it exists to ensure a fresh start
        cursor.execute("DROP TABLE IF EXISTS wines")
        print("Table 'wines' dropped if it existed.")

        # Create wines table with a country column
        create_table_query = """
        CREATE TABLE wines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            grape VARCHAR(255),
            region VARCHAR(255),
            country VARCHAR(255),
            variety VARCHAR(255),
            rating VARCHAR(255),
            notes TEXT
        )
        """
        cursor.execute(create_table_query)
        print("Table 'wines' created with 'country' column.")

        cnx.commit()
        cursor.close()
        cnx.close()

    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")

def insert_data_from_csv(csv_file):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)

        insert_query = """
        INSERT INTO wines (name, grape, region, country, variety, rating, notes)
        VALUES (%(name)s, %(grape)s, %(region)s, %(country)s, %(variety)s, %(rating)s, %(notes)s)
        """

        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                try:
                    region_parts = row.get('region', '').split(',')
                    region_name = region_parts[0].strip() if region_parts else ''
                    country_name = region_parts[1].strip() if len(region_parts) > 1 else region_name
                    
                    row['region'] = region_name
                    row['country'] = country_name

                    cursor.execute(insert_query, row)
                except mysql.connector.Error as err:
                    print(f"Error inserting row {row}: {err}")
                    cnx.rollback()
                    continue
            
            cnx.commit()
            print("Data insertion complete.")

    except mysql.connector.Error as err:
        print(f"Error during data insertion: {err}")
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

@app.on_event("startup")
async def startup_event():
    create_database_and_table()
    insert_data_from_csv("wine.csv")
    print("Database reset and repopulated.")

# Pydantic Models
class Wine(BaseModel):
    id: int
    name: str
    grape: Optional[str]
    region: Optional[str]
    country: Optional[str]
    variety: Optional[str]
    rating: Optional[str]
    notes: Optional[str]

class Region(BaseModel):
    name: str
    country: str
    wine_count: int

class RegionByCountry(BaseModel):
    country: str
    wine_count: int
    region_count: int
    regions: List[Region]
    
class Grape(BaseModel):
    name: str
    wine_count: int
    primary_regions: List[dict]


@app.get("/wines", response_model=List[Wine])
async def get_wines(
    country: Optional[str] = None,
    region: Optional[str] = None,
    variety: Optional[str] = None,
):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    query = "SELECT * FROM wines WHERE 1=1"
    params = []

    if country:
        query += " AND country = %s"
        params.append(country)
    if region:
        query += " AND region = %s"
        params.append(region)
    if variety:
        query += " AND variety = %s"
        params.append(variety)

    cursor.execute(query, tuple(params))
    wines = cursor.fetchall()
    
    cursor.close()
    cnx.close()
    return wines

@app.get("/regions", response_model=dict)
async def get_regions(
    country: Optional[str] = None,
    group_by_country: bool = False,
    min_wines: Optional[int] = None,
    sort_by: Optional[str] = "name",
    order: Optional[str] = "asc",
):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    query = "SELECT country, region as name, count(*) as wine_count FROM wines WHERE region IS NOT NULL GROUP BY region, country"
    
    # This filtering logic needs to be adapted for HAVING clause
    # Since we are not using LIKE, we can't filter country directly in the WHERE clause in the same way.
    # We will build the query with proper WHERE and HAVING clauses.
    
    where_clauses = []
    having_clauses = []
    params = []

    if country:
        where_clauses.append("country = %s")
        params.append(country)

    query = "SELECT country, region as name, count(*) as wine_count FROM wines"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " GROUP BY region, country"

    if min_wines:
        having_clauses.append("wine_count >= %s")
        params.append(min_wines)
    
    if having_clauses:
        query += " HAVING " + " AND ".join(having_clauses)

    if sort_by in ["name", "country", "wine_count"]:
        query += f" ORDER BY {sort_by} {order}"

    cursor.execute(query, tuple(params))
    regions_data = cursor.fetchall()

    if group_by_country:
        regions_by_country = {}
        for region in regions_data:
            country_name = region["country"].strip()
            if country_name not in regions_by_country:
                regions_by_country[country_name] = {
                    "country": country_name,
                    "wine_count": 0,
                    "region_count": 0,
                    "regions": [],
                }
            
            regions_by_country[country_name]["wine_count"] += region["wine_count"]
            regions_by_country[country_name]["region_count"] += 1
            regions_by_country[country_name]["regions"].append({
                "name": region["name"],
                "country": country_name,
                "wine_count": region["wine_count"],
            })
        
        response = {"regions_by_country": list(regions_by_country.values())}

    else:
        response = {"regions": regions_data}
        
    cursor.close()
    cnx.close()
    return response

@app.get("/regions/{region_name}/wines", response_model=List[Wine])
async def get_wines_by_region(region_name: str):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    
    decoded_region_name = unquote(region_name)
    
    cursor.execute("SELECT * FROM wines WHERE region = %s", (decoded_region_name,))
    wines = cursor.fetchall()

    if not wines:
        raise HTTPException(status_code=404, detail="Region not found or no wines in this region")
    
    cursor.close()
    cnx.close()
    return wines


@app.get("/grapes", response_model=List[Grape])
async def get_grapes(
    min_wines: Optional[int] = None,
    variety: Optional[str] = None,
    region: Optional[str] = None,
    sort_by: Optional[str] = "name",
    order: Optional[str] = "asc",
):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    # Base query for grapes and their wine counts
    subquery_g = """
    SELECT TRIM(grape) AS name, COUNT(*) AS wine_count
    FROM wines
    WHERE grape IS NOT NULL AND grape != ''
    GROUP BY TRIM(grape)
    """
    
    # Subquery for regions related to grapes
    subquery_r = """
    SELECT TRIM(grape) AS grape, region AS region_name, COUNT(*) AS region_count
    FROM wines
    WHERE grape IS NOT NULL AND grape != ''
    GROUP BY TRIM(grape), region
    """

    from_clause = f"""
    FROM ({subquery_g}) AS g
    LEFT JOIN ({subquery_r}) AS r ON g.name = r.grape
    """

    select_clause = """
    SELECT g.name, g.wine_count, GROUP_CONCAT(DISTINCT CONCAT(r.region_name, ':', r.region_count) ORDER BY r.region_count DESC SEPARATOR ';') AS primary_regions
    """
    
    where_clauses = []
    params = []

    if variety:
        where_clauses.append("g.name = %s")
        params.append(variety)
    
    if region:
        # If filtering by region, we need to join with a subquery that identifies grapes in that region
        from_clause += f"""
        INNER JOIN (SELECT DISTINCT TRIM(grape) AS grape_in_region FROM wines WHERE region = %s) AS fr ON g.name = fr.grape_in_region
        """
        params.append(region)

    full_query = select_clause + from_clause

    if where_clauses:
        full_query += " WHERE " + " AND ".join(where_clauses)
    
    full_query += " GROUP BY g.name, g.wine_count" # Crucial: Add the outer GROUP BY

    if min_wines:
        full_query += " HAVING g.wine_count >= %s"
        params.append(min_wines)

    if sort_by in ["name", "wine_count"]:
        full_query += f" ORDER BY g.{sort_by} {order}, g.name ASC"

    cursor.execute(full_query, tuple(params))
    grapes_data = cursor.fetchall()
    
    grape_list = []
    for grape in grapes_data:
        primary_regions = []
        if grape.get('primary_regions'):
            for r in grape['primary_regions'].split(';'):
                try:
                    name, count = r.split(':')
                    primary_regions.append({'name': name, 'count': int(count)})
                except ValueError:
                    pass

        grape_list.append({
            "name": grape["name"],
            "wine_count": grape["wine_count"],
            "primary_regions": primary_regions,
        })
    
    cursor.close()
    cnx.close()
    return grape_list

@app.get("/grapes/{grape_name}/wines", response_model=List[Wine])
async def get_wines_by_grape(grape_name: str):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    
    decoded_grape_name = unquote(grape_name)
    
    cursor.execute("SELECT * FROM wines WHERE grape = %s", (decoded_grape_name,))
    wines = cursor.fetchall()

    if not wines:
        raise HTTPException(status_code=404, detail="Grape not found or no wines with this grape")
    
    cursor.close()
    cnx.close()
    return wines