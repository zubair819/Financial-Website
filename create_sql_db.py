import mysql.connector
from mysql.connector import Error

# Update these with your actual MySQL credentials
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "zubair084",
    "database": "financial_website"
}

def create_database():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS financial_website")
            print("Database created successfully")
    except Error as e:
        print(f"Error creating database: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def create_tables():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)
            
            # Create financial_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    date DATE NOT NULL,
                    income DECIMAL(10, 2) NOT NULL,
                    entertainment DECIMAL(10, 2) NOT NULL,
                    grocery DECIMAL(10, 2) NOT NULL,
                    snacks DECIMAL(10, 2) NOT NULL,
                    bills DECIMAL(10, 2) NOT NULL,
                    salaries DECIMAL(10, 2) NOT NULL,
                    total_expenditure DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            print("Tables created successfully")
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_database()
    create_tables()