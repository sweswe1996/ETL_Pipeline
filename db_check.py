import sqlite3

# データベースに接続
conn = sqlite3.connect("output/books.db")

tables = conn.execute("SELECT name FROM sqlite_master where type = 'table'").fetchall()

# テーブル一覧を表示
print("=" * 25)
print("DataBase of Table List")
print("=" * 25)
for table in tables:
    print(f" * {table[0]}")

print()

for table in tables:
    tablename = table[0]

    print("=" * 25)
    print(f"Table Name : {tablename}")
    print("=" * 25)

    # カラム名を取得して表示
    cursor = conn.execute(f"SELECT * FROM {tablename} LIMIT 0")
    col_names = [desc[0] for desc in cursor.description]
    print("Columns", col_names)
    print()

    # データを表示（booksは5件、それ以外は10件）
    limit = 5 if tablename == "books" else 10
    rows = conn.execute(f"SELECT * FROM {tablename} LIMIT {limit}").fetchall()
    for row in rows:
        print(row)

    if tablename == "books":
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        print("." * 50)
        print(f"...all {total} books of 5 books is display!")
    print()

# 接続を閉じる
conn.close()