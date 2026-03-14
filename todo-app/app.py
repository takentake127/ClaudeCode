import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = "todos.db"


def get_db():
    """データベース接続を取得する（リクエストごとに1つ）"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # 結果を辞書風にアクセスできるようにする
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """リクエスト終了時にデータベース接続を閉じる"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """テーブルがなければ作成する"""
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES todos(id)
        )
    """)
    db.commit()
    db.close()


def get_children(parent_id):
    """指定した親IDに属する子タスクを返す"""
    db = get_db()
    if parent_id is None:
        rows = db.execute("SELECT * FROM todos WHERE parent_id IS NULL").fetchall()
    else:
        rows = db.execute("SELECT * FROM todos WHERE parent_id = ?", (parent_id,)).fetchall()
    return rows


def get_all_descendant_ids(parent_id):
    """指定した親IDの子・孫・ひ孫…すべてのIDを集める（削除用）"""
    db = get_db()
    children = db.execute("SELECT id FROM todos WHERE parent_id = ?", (parent_id,)).fetchall()
    ids = []
    for child in children:
        ids.append(child["id"])
        ids.extend(get_all_descendant_ids(child["id"]))
    return ids


@app.route("/")
def index():
    """メインページ: Todoの一覧を表示する"""
    db = get_db()
    all_todos = db.execute("SELECT * FROM todos").fetchall()
    top_todos = get_children(None)
    return render_template("index.html", top_todos=top_todos, get_children=get_children, all_todos=all_todos)


@app.route("/add", methods=["POST"])
def add():
    """新しいTodoを追加する"""
    title = request.form.get("title", "").strip()
    parent_id = request.form.get("parent_id")

    if parent_id:
        parent_id = int(parent_id)
    else:
        parent_id = None

    if title:
        db = get_db()
        db.execute("INSERT INTO todos (title, parent_id) VALUES (?, ?)", (title, parent_id))
        db.commit()
    return redirect(url_for("index"))


def set_all_descendants(todo_id, done_value):
    """子・孫…すべてのタスクの完了状態を一括変更する"""
    db = get_db()
    children = db.execute("SELECT id FROM todos WHERE parent_id = ?", (todo_id,)).fetchall()
    for child in children:
        db.execute("UPDATE todos SET done = ? WHERE id = ?", (done_value, child["id"]))
        set_all_descendants(child["id"], done_value)


def check_parent_completion(todo_id):
    """親タスクの子がすべて完了していたら、親も自動的に完了にする。
    逆に、子が1つでも未完了なら親を未完了に戻す。祖先まで再帰的にチェックする。"""
    db = get_db()
    todo = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not todo or todo["parent_id"] is None:
        return
    parent_id = todo["parent_id"]
    siblings = db.execute("SELECT done FROM todos WHERE parent_id = ?", (parent_id,)).fetchall()
    all_done = all(s["done"] for s in siblings)
    db.execute("UPDATE todos SET done = ? WHERE id = ?", (1 if all_done else 0, parent_id))
    check_parent_completion(parent_id)


@app.route("/toggle/<int:todo_id>")
def toggle(todo_id):
    """Todoの完了/未完了を切り替える（子・親も連動）"""
    db = get_db()
    todo = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if todo:
        new_done = 0 if todo["done"] else 1
        db.execute("UPDATE todos SET done = ? WHERE id = ?", (new_done, todo_id))
        # 完了/未完了を子タスクにも伝播
        set_all_descendants(todo_id, new_done)
        # 親タスクの自動完了/未完了をチェック
        check_parent_completion(todo_id)
        db.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    """Todoのタイトルを編集する"""
    new_title = request.form.get("title", "").strip()
    if new_title:
        db = get_db()
        db.execute("UPDATE todos SET title = ? WHERE id = ?", (new_title, todo_id))
        db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    """Todoとその子タスクをすべて削除する"""
    db = get_db()
    ids_to_delete = [todo_id] + get_all_descendant_ids(todo_id)
    placeholders = ",".join("?" * len(ids_to_delete))
    db.execute(f"DELETE FROM todos WHERE id IN ({placeholders})", ids_to_delete)
    db.commit()
    return redirect(url_for("index"))


# アプリ起動時にテーブルを作成
init_db()

if __name__ == "__main__":
    app.run(debug=True)
