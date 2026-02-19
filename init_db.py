import psycopg2

def setup_db():
    # Connect to the Postgres container we just started
    conn = psycopg2.connect("dbname=postgres user=postgres password=mysecretpassword host=localhost")
    cur = conn.cursor()
    
    # Create the jobs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID PRIMARY KEY,
            task_name VARCHAR(255),
            payload TEXT,
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database and 'jobs' table initialized!")

if __name__ == '__main__':
    setup_db()