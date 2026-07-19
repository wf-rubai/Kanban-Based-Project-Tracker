import os

# Use PyMySQL as a drop-in replacement for MySQLdb so contributors don't need
# to compile the native mysqlclient package. Only activated when actually
# talking to MySQL (skipped for the sqlite fallback used in quick testing).
if os.environ.get("DJANGO_DB", "mysql") != "sqlite":
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
