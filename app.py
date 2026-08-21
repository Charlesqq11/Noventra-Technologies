from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os


# =========================================================
# APP SETUP
# =========================================================

app = Flask(__name__)

app.secret_key = "noventra-change-this-secret-key"


# =========================================================
# ADMIN LOGIN
# =========================================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Noventra@2026"


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")

DATABASE = os.path.join(DATABASE_DIR, "noventra.db")


def get_db():

    os.makedirs(DATABASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    os.makedirs(DATABASE_DIR, exist_ok=True)

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            email TEXT NOT NULL,
            country_code TEXT,
            phone TEXT,
            service TEXT NOT NULL,
            budget TEXT,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    conn = get_db()

    # Total client projects
    total_clients = conn.execute("""
        SELECT COUNT(*)
        FROM enquiries
    """).fetchone()[0]

    # Total completed projects
    completed_projects = conn.execute("""
        SELECT COUNT(*)
        FROM enquiries
        WHERE status = 'Completed'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_clients=total_clients,
        completed_projects=completed_projects
    )


# =========================================================
# SERVICES
# =========================================================

@app.route("/services")
def services():
    return render_template("services.html")

# =========================================================
# SOLUTIONS
# =========================================================

@app.route("/solutions")
def solutions():
    return render_template("solutions.html")


# =========================================================
# CASE STUDIES
# =========================================================

@app.route("/case-studies")
def case_studies():
    return render_template("case-studies.html")


@app.route("/case-study")
def case_study():
    return render_template("case-study.html")


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():
    return render_template("about.html")


# =========================================================
# CONTACT
# =========================================================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        company = request.form.get("company", "").strip()
        email = request.form.get("email", "").strip()
        country_code = request.form.get("country_code", "").strip()
        phone = request.form.get("phone", "").strip()
        service = request.form.get("service", "").strip()
        budget = request.form.get("budget", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not service or not message:

            flash(
                "Please complete all required fields.",
                "error"
            )

            return redirect(url_for("contact"))

        conn = get_db()

        conn.execute("""
            INSERT INTO enquiries (
                name,
                company,
                email,
                country_code,
                phone,
                service,
                budget,
                message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            company,
            email,
            country_code,
            phone,
            service,
            budget,
            message
        ))

        conn.commit()
        conn.close()

        flash(
            "Thank you. Your project inquiry has been received.",
            "success"
        )

        return redirect(url_for("contact"))

    return render_template("contact.html")


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        flash(
            "Invalid username or password.",
            "error"
        )

        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    conn = get_db()

    query = """
        SELECT *
        FROM enquiries
        WHERE 1=1
    """

    params = []

    # Search
    if search:

        query += """
            AND (
                name LIKE ?
                OR company LIKE ?
                OR email LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    # Status filter
    if status_filter in [
        "New",
        "Contacted",
        "Completed"
    ]:

        query += """
            AND status = ?
        """

        params.append(status_filter)

    query += """
        ORDER BY created_at DESC
    """

    enquiries = conn.execute(
        query,
        params
    ).fetchall()

    # Statistics

    total = conn.execute("""
        SELECT COUNT(*)
        FROM enquiries
    """).fetchone()[0]

    new_count = conn.execute("""
        SELECT COUNT(*)
        FROM enquiries
        WHERE status = 'New'
    """).fetchone()[0]

    contacted_count = conn.execute("""
        SELECT COUNT(*)
        FROM enquiries
        WHERE status = 'Contacted'
    """).fetchone()[0]

    completed_count = conn.execute("""
        SELECT COUNT(*)
        FROM enquiries
        WHERE status = 'Completed'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        enquiries=enquiries,
        total=total,
        new_count=new_count,
        contacted_count=contacted_count,
        completed_count=completed_count,
        search=search,
        status_filter=status_filter
    )


# =========================================================
# UPDATE ENQUIRY STATUS
# =========================================================

# =========================================================
# VIEW ENQUIRY DETAILS
# =========================================================

@app.route("/admin/enquiry/<int:enquiry_id>")
def view_enquiry(enquiry_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    enquiry = conn.execute("""
        SELECT *
        FROM enquiries
        WHERE id = ?
    """, (enquiry_id,)).fetchone()

    conn.close()

    if enquiry is None:
        flash("Enquiry not found.", "error")
        return redirect(url_for("admin"))

    return render_template(
        "enquiry_details.html",
        enquiry=enquiry
    )

@app.route("/admin/status/<int:enquiry_id>", methods=["POST"])
def update_status(enquiry_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    status = request.form.get("status", "").strip()

    allowed_statuses = [
        "New",
        "Contacted",
        "Completed"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid status.",
            "error"
        )

        return redirect(url_for("admin"))

    conn = get_db()

    conn.execute("""
        UPDATE enquiries
        SET status = ?
        WHERE id = ?
    """, (
        status,
        enquiry_id
    ))

    conn.commit()
    conn.close()

    flash(
        "Enquiry status updated.",
        "success"
    )

    return redirect(url_for("admin"))

# =========================================================
# DELETE ENQUIRY
# =========================================================

@app.route("/admin/delete/<int:enquiry_id>", methods=["POST"])
def delete_enquiry(enquiry_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM enquiries
        WHERE id = ?
    """, (enquiry_id,))

    conn.commit()
    conn.close()

    flash(
        "Enquiry deleted successfully.",
        "success"
    )

    return redirect(url_for("admin"))

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("admin_login"))


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )