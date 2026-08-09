import psycopg2

def main():
    conn = psycopg2.connect('postgresql://postgres:12345678@localhost:5432/postgres')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname='evalforge'")
    exists = cur.fetchone()
    if not exists:
        cur.execute('CREATE DATABASE evalforge')
        print('Created database evalforge')
    else:
        print('Database evalforge already exists')
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
