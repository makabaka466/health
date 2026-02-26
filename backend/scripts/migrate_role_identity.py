import pymysql


def main() -> None:
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="123456",
        database="health",
        charset="utf8mb4",
    )

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COUNT(1)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
            """,
            ("health", "users", "role_id"),
        )
        role_id_exists = cur.fetchone()[0] > 0

        if not role_id_exists:
            cur.execute("ALTER TABLE users ADD COLUMN role_id INT NULL")
            cur.execute("CREATE INDEX idx_users_role_id ON users(role_id)")

        cur.execute(
            """
            SELECT COUNT(1)
            FROM information_schema.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME=%s
            """,
            ("health", "users", "fk_users_role_id"),
        )
        fk_exists = cur.fetchone()[0] > 0

        if not fk_exists:
            cur.execute(
                "ALTER TABLE users ADD CONSTRAINT fk_users_role_id FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL"
            )

        conn.commit()
        print("migration_done")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
