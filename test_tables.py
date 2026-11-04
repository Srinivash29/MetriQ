
from db import get_db_connection

try:
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SHOW TABLES")

    tables = cursor.fetchall()

    print("\nMETRIQ DATABASE TABLES")
    print("----------------------")

    for table in tables:
        print(table[0])

    print("\nTotal tables:", len(tables))

    cursor.close()
    connection.close()

except Exception as error:
    print("Error:", error)
