from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Todoリストをメモリ上に保存（あとでデータベースに変える予定）
# parent_id: 親タスクのID（Noneなら最上位のタスク）
todos = []
next_id = 1  # IDを連番で管理するためのカウンター


def find_todo(todo_id):
    """IDからTodoを探して返す"""
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return None


def get_children(parent_id):
    """指定した親IDに属する子タスクを返す"""
    return [todo for todo in todos if todo["parent_id"] == parent_id]


def get_all_descendants(parent_id):
    """指定した親IDの子・孫・ひ孫…すべてのIDを集める（削除用）"""
    ids = []
    for todo in todos:
        if todo["parent_id"] == parent_id:
            ids.append(todo["id"])
            ids.extend(get_all_descendants(todo["id"]))
    return ids


@app.route("/")
def index():
    """メインページ: Todoの一覧を表示する"""
    # 最上位のタスク（親がいないもの）だけ取得
    top_todos = get_children(None)
    return render_template("index.html", todos=todos, top_todos=top_todos, get_children=get_children)


@app.route("/add", methods=["POST"])
def add():
    """新しいTodoを追加する"""
    global next_id
    title = request.form.get("title", "").strip()
    parent_id = request.form.get("parent_id")  # 親タスクのID（なければNone）

    # parent_idが空文字なら None に、数字ならintに変換
    if parent_id:
        parent_id = int(parent_id)
    else:
        parent_id = None

    if title:
        todo = {"id": next_id, "title": title, "done": False, "parent_id": parent_id}
        todos.append(todo)
        next_id += 1
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>")
def toggle(todo_id):
    """Todoの完了/未完了を切り替える"""
    todo = find_todo(todo_id)
    if todo:
        todo["done"] = not todo["done"]
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
def edit(todo_id):
    """Todoのタイトルを編集する"""
    todo = find_todo(todo_id)
    if todo:
        new_title = request.form.get("title", "").strip()
        if new_title:
            todo["title"] = new_title
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    """Todoとその子タスクをすべて削除する"""
    global todos
    # 削除するIDを集める（自分＋すべての子孫）
    ids_to_delete = {todo_id} | set(get_all_descendants(todo_id))
    todos = [todo for todo in todos if todo["id"] not in ids_to_delete]
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
