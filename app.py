from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_NAME = "database.db"

def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        master_id INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS masters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        bio TEXT,
        photo_url TEXT,
        experience TEXT,
        sort_order INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price TEXT NOT NULL,
        duration TEXT NOT NULL,
        description TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        master_id INTEGER,
        title TEXT NOT NULL,
        image_url TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY(master_id) REFERENCES masters(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        service_id INTEGER NOT NULL,
        master_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        comment TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(service_id) REFERENCES services(id),
        FOREIGN KEY(master_id) REFERENCES masters(id)
    )
    """)

    c.execute("SELECT COUNT(*) FROM masters")
    if c.fetchone()[0] == 0:
        demo_masters = [
            ("Sofia", "Ногтевой сервис", "Аккуратный маникюр, мягкие оттенки и premium-уход за руками.", "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80", "6 лет опыта", 1),
            ("Emma", "Брови и ресницы", "Естественный результат, архитектура бровей и деликатные ресницы.", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=80", "5 лет опыта", 2),
            ("Mia", "Make-up & hair", "Образы для событий, свадебный и вечерний макияж.", "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80", "7 лет опыта", 3)
        ]
        c.executemany("INSERT INTO masters (name, specialty, bio, photo_url, experience, sort_order) VALUES (?, ?, ?, ?, ?, ?)", demo_masters)

    c.execute("SELECT COUNT(*) FROM services")
    if c.fetchone()[0] == 0:
        services = [
            ("Маникюр Premium", "900 Kč", "60 мин", "Чистый маникюр, выравнивание и покрытие."),
            ("Педикюр Spa", "1200 Kč", "75 мин", "Уход, обработка и spa-ритуал."),
            ("Brows Styling", "700 Kč", "45 мин", "Коррекция, форма и окрашивание."),
            ("Lashes Classic", "1300 Kč", "90 мин", "Нежное классическое наращивание."),
            ("Event Make-up", "1800 Kč", "90 мин", "Стойкий вечерний макияж.")
        ]
        c.executemany("INSERT INTO services (name, price, duration, description) VALUES (?, ?, ?, ?)", services)

    c.execute("SELECT COUNT(*) FROM portfolio")
    if c.fetchone()[0] == 0:
        items = [
            (1, "Milk manicure", "https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=1200&q=80", "Нежное покрытие в premium-стиле."),
            (1, "Glossy nude", "https://images.unsplash.com/photo-1632345031435-8727f6897d53?auto=format&fit=crop&w=1200&q=80", "Чистая форма и идеальный блеск."),
            (2, "Soft brows", "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=1200&q=80", "Естественная архитектура бровей."),
            (2, "Lash set", "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=1200&q=80", "Классические ресницы для выразительного взгляда."),
            (3, "Bridal look", "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?auto=format&fit=crop&w=1200&q=80", "Лёгкий сияющий образ."),
            (3, "Evening glam", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=1200&q=80", "Вечерний макияж и укладка.")
        ]
        c.executemany("INSERT INTO portfolio (master_id, title, image_url, description) VALUES (?, ?, ?, ?)", items)

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        ids = [row[0] for row in c.execute("SELECT id FROM masters ORDER BY id").fetchall()]
        users = [
            ("admin", "1234", "admin", None),
            ("sofia", "1234", "master", ids[0] if len(ids) > 0 else None),
            ("emma", "1234", "master", ids[1] if len(ids) > 1 else None),
            ("mia", "1234", "master", ids[2] if len(ids) > 2 else None),
        ]
        c.executemany("INSERT INTO users (username, password, role, master_id) VALUES (?, ?, ?, ?)", users)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = connect()
    masters = conn.execute("SELECT * FROM masters ORDER BY sort_order, id").fetchall()
    services = conn.execute("SELECT * FROM services ORDER BY id").fetchall()
    portfolio = conn.execute("""
        SELECT portfolio.*, masters.name AS master_name
        FROM portfolio
        LEFT JOIN masters ON masters.id = portfolio.master_id
        ORDER BY portfolio.id DESC
        LIMIT 6
    """).fetchall()
    conn.close()
    return render_template("index.html", masters=masters, services=services, portfolio=portfolio)

@app.route("/masters")
def masters_page():
    conn = connect()
    masters = conn.execute("SELECT * FROM masters ORDER BY sort_order, id").fetchall()
    portfolio = conn.execute("""
        SELECT portfolio.*, masters.name AS master_name
        FROM portfolio
        LEFT JOIN masters ON masters.id = portfolio.master_id
        ORDER BY portfolio.id DESC
    """).fetchall()
    conn.close()
    return render_template("masters.html", masters=masters, portfolio=portfolio)

@app.route("/book", methods=["POST"])
def book():
    form = request.form
    conn = connect()
    c = conn.cursor()

    conflict = c.execute("""
        SELECT id FROM bookings
        WHERE master_id = ? AND date = ? AND time = ?
          AND status != 'cancelled'
    """, (form["master_id"], form["date"], form["time"])).fetchone()

    if conflict:
        conn.close()
        return redirect(url_for("index", booked="busy"))

    c.execute("""
        INSERT INTO bookings (client_name, phone, service_id, master_id, date, time, comment, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        form["client_name"],
        form["phone"],
        form["service_id"],
        form["master_id"],
        form["date"],
        form["time"],
        form.get("comment", ""),
        "new"
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("index", booked="success"))

@app.route("/slots")
def slots():
    date = request.args.get("date")
    master_id = request.args.get("master_id")
    if not date or not master_id:
        return jsonify([])

    all_slots = ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00"]
    conn = connect()
    rows = conn.execute("""
        SELECT time FROM bookings
        WHERE date = ? AND master_id = ? AND status != 'cancelled'
    """, (date, master_id)).fetchall()
    conn.close()

    busy = {row["time"] for row in rows}
    available = [slot for slot in all_slots if slot not in busy]
    return jsonify(available)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect()
        user = conn.execute("""
            SELECT users.*, masters.name AS master_name
            FROM users
            LEFT JOIN masters ON masters.id = users.master_id
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["master_id"] = user["master_id"]
            return redirect("/dashboard")

        return render_template("login.html", error="Неверный логин или пароль.")

    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect("/login")

    conn = connect()

    if session["role"] == "admin":
        bookings = conn.execute("""
            SELECT bookings.*, masters.name AS master_name, services.name AS service_name, services.price
            FROM bookings
            JOIN masters ON masters.id = bookings.master_id
            JOIN services ON services.id = bookings.service_id
            ORDER BY bookings.date, bookings.time
        """).fetchall()
        masters = conn.execute("SELECT * FROM masters ORDER BY sort_order, id").fetchall()
        services = conn.execute("SELECT * FROM services ORDER BY id DESC").fetchall()
        users = conn.execute("""
            SELECT users.*, masters.name AS master_name
            FROM users
            LEFT JOIN masters ON masters.id = users.master_id
            ORDER BY users.id DESC
        """).fetchall()
        portfolio = conn.execute("""
            SELECT portfolio.*, masters.name AS master_name
            FROM portfolio
            LEFT JOIN masters ON masters.id = portfolio.master_id
            ORDER BY portfolio.id DESC
        """).fetchall()
        stats = {
            "bookings": conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "masters": conn.execute("SELECT COUNT(*) FROM masters").fetchone()[0],
            "services": conn.execute("SELECT COUNT(*) FROM services").fetchone()[0],
            "new_bookings": conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'new'").fetchone()[0]
        }
        conn.close()
        return render_template("admin.html", bookings=bookings, masters=masters, services=services, users=users, portfolio=portfolio, stats=stats)

    bookings = conn.execute("""
        SELECT bookings.*, services.name AS service_name, services.price, masters.name AS master_name
        FROM bookings
        JOIN services ON services.id = bookings.service_id
        JOIN masters ON masters.id = bookings.master_id
        WHERE bookings.master_id = ?
        ORDER BY bookings.date, bookings.time
    """, (session["master_id"],)).fetchall()
    master = conn.execute("SELECT * FROM masters WHERE id = ?", (session["master_id"],)).fetchone()
    conn.close()
    return render_template("master.html", bookings=bookings, master=master)

@app.route("/admin/add-master", methods=["POST"])
def add_master():
    if session.get("role") != "admin":
        return redirect("/login")
    conn = connect()
    conn.execute("""
        INSERT INTO masters (name, specialty, bio, photo_url, experience, sort_order)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form["specialty"],
        request.form.get("bio", ""),
        request.form.get("photo_url", ""),
        request.form.get("experience", ""),
        request.form.get("sort_order", 0) or 0
    ))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/admin/add-service", methods=["POST"])
def add_service():
    if session.get("role") != "admin":
        return redirect("/login")
    conn = connect()
    conn.execute("""
        INSERT INTO services (name, price, duration, description)
        VALUES (?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form["price"],
        request.form["duration"],
        request.form.get("description", "")
    ))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/admin/add-portfolio", methods=["POST"])
def add_portfolio():
    if session.get("role") != "admin":
        return redirect("/login")
    conn = connect()
    conn.execute("""
        INSERT INTO portfolio (master_id, title, image_url, description)
        VALUES (?, ?, ?, ?)
    """, (
        request.form["master_id"],
        request.form["title"],
        request.form["image_url"],
        request.form.get("description", "")
    ))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/admin/add-user", methods=["POST"])
def add_user():
    if session.get("role") != "admin":
        return redirect("/login")

    role = request.form["role"]
    master_id = request.form.get("master_id") or None

    conn = connect()
    try:
        conn.execute("""
            INSERT INTO users (username, password, role, master_id)
            VALUES (?, ?, ?, ?)
        """, (
            request.form["username"],
            request.form["password"],
            role,
            master_id if role == "master" else None
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()
    return redirect("/dashboard")

@app.route("/booking/<int:booking_id>/status", methods=["POST"])
def update_booking_status(booking_id):
    if "role" not in session:
        return redirect("/login")

    new_status = request.form["status"]
    conn = connect()

    if session["role"] == "admin":
        conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
    else:
        conn.execute("""
            UPDATE bookings SET status = ?
            WHERE id = ? AND master_id = ?
        """, (new_status, booking_id, session["master_id"]))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/delete/<string:item>/<int:item_id>")
def delete_item(item, item_id):
    if session.get("role") != "admin":
        return redirect("/login")

    table_map = {
        "booking": "bookings",
        "master": "masters",
        "service": "services",
        "portfolio": "portfolio",
        "user": "users"
    }
    table = table_map.get(item)
    if not table:
        return redirect("/dashboard")

    conn = connect()
    if table == "masters":
        conn.execute("DELETE FROM portfolio WHERE master_id = ?", (item_id,))
        conn.execute("DELETE FROM bookings WHERE master_id = ?", (item_id,))
        conn.execute("DELETE FROM users WHERE master_id = ?", (item_id,))
    if table == "services":
        conn.execute("DELETE FROM bookings WHERE service_id = ?", (item_id,))
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
