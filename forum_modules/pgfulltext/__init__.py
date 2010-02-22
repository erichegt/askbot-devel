NAME = 'Postgresql Full Text Search'
DESCRIPTION = "Enables PostgreSql full text search functionality."

try:
    import psycopg2
    CAN_ENABLE = True
except:
    CAN_ENABLE = False
    