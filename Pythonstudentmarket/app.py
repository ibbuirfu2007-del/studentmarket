from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "student_market_secret_key"


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="irfan",      
        database="studentmarket"
    )

@app.route("/")
def home():

    if "user_id" in session:
        return redirect("/dashboard")

    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form.get("department", "")
        phone = request.form.get("phone", "")

        conn = get_connection()
        cur = conn.cursor()

        # Check email already exists
        cur.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        if user:
            flash("Email already exists")
            cur.close()
            conn.close()
            return redirect("/register")

        # Insert user
        cur.execute("""
            INSERT INTO users
            (name,email,password,department,phone)
            VALUES(%s,%s,%s,%s,%s)
        """,
        (
            name,
            email,
            password,
            department,
            phone
        ))

        conn.commit()

        cur.close()
        conn.close()

        flash("Registration Successful")
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"].strip()

        print("Email:", email)
        print("Password:", password)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        print("User:", user)

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user"] = user[1]
            flash("Login Successful")
            return redirect("/dashboard")

        flash("Invalid Email or Password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        products.id,
        products.product_name,
        products.description,
        products.price,
        products.category,
        users.name
    FROM products
    JOIN users
    ON products.user_id = users.id
    ORDER BY products.id DESC
    """)

    products = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        products=products
    )

@app.route("/add_product", methods=["GET", "POST"])
def add_product():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form["product_name"]
        description = request.form["description"]
        category = request.form["category"]
        price = request.form["price"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO products
        (user_id, product_name, description, price, category, status)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
                    (
                        session["user_id"],
                        product_name,
                        description,
                        price,
                        category,
                        "Available"
                    ))

        conn.commit()

        cur.close()
        conn.close()

        flash("Product Added Successfully")

        return redirect("/dashboard")

    return render_template("add_product.html")

@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":

        product_name = request.form["product_name"]
        description = request.form["description"]
        category = request.form["category"]
        price = request.form["price"]

        cur.execute("""
        UPDATE products
        SET
            product_name=%s,
            description=%s,
            category=%s,
            price=%s
        WHERE id=%s
        AND user_id=%s
        """,
                    (
                        product_name,
                        description,
                        category,
                        price,
                        id,
                        session["user_id"]
                    ))

        conn.commit()

        flash("Product Updated Successfully")

        cur.close()
        conn.close()

        return redirect("/dashboard")

    cur.execute("""
        SELECT *
        FROM products
        WHERE id=%s
        AND user_id=%s
    """,
    (
        id,
        session["user_id"]
    ))

    product = cur.fetchone()

    cur.close()
    conn.close()

    if product is None:
        flash("Product Not Found")
        return redirect("/dashboard")

    return render_template(
        "edit_product.html",
        product=product
    )


@app.route("/delete_product/<int:id>")
def delete_product(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM products
        WHERE id=%s
        AND user_id=%s
    """,
    (
        id,
        session["user_id"]
    ))

    conn.commit()

    cur.close()
    conn.close()

    flash("Product Deleted Successfully")

    return redirect("/dashboard")

@app.route("/search", methods=["GET", "POST"])
def search():

    if "user_id" not in session:
        return redirect("/login")

    products = []

    if request.method == "POST":

        keyword = request.form["keyword"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT
            products.id,
            products.product_name,
            products.description,
            products.price,
            products.category,
            users.name
        FROM products
        JOIN users
        ON products.user_id = users.id
        WHERE products.product_name LIKE %s
        OR products.category LIKE %s
        """,
                    (
                        "%" + keyword + "%",
                        "%" + keyword + "%"
                    ))

        products = cur.fetchall()

        cur.close()
        conn.close()

    return render_template(
        "search.html",
        products=products
    )

@app.route("/wishlist")
def wishlist():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        products.id,
        products.product_name,
        products.description,
        products.price,
        products.category
    FROM wishlist
    JOIN products
    ON wishlist.product_id = products.id
    WHERE wishlist.user_id=%s
    """, (session["user_id"],))

    products = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "wishlist.html",
        products=products
    )


# -------------------------------------------------
# Add to Wishlist
# -------------------------------------------------
@app.route("/wishlist/<int:product_id>")
def add_to_wishlist(product_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    # Prevent duplicate wishlist entries
    cur.execute("""
        SELECT *
        FROM wishlist
        WHERE user_id=%s
        AND product_id=%s
    """,
    (
        session["user_id"],
        product_id
    ))

    item = cur.fetchone()

    if item:
        flash("Product already in Wishlist")
    else:

        cur.execute("""
            INSERT INTO wishlist(user_id, product_id)
            VALUES(%s,%s)
        """,
        (
            session["user_id"],
            product_id
        ))

        conn.commit()

        flash("Added to Wishlist")

    cur.close()
    conn.close()

    return redirect("/dashboard")



@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully")

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
