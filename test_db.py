
from db import get_db_connection

try:
    connection = get_db_connection()

    if connection.is_connected():
        print("SUCCESS: Connected to MetriQ database!")

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")

        result = cursor.fetchone()

        print("Database name:", result[0])

        cursor.close()
        connection.close()

except Exception as error:
    print("DATABASE CONNECTION FAILED!")
    print("Error:", error)
