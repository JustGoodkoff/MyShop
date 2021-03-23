from flask import Flask
from flask import render_template
from flask import request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from data import db_session
from data.users import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "my_shop_secret_key"


def main():
    db_session.global_init("db/my_shop.db")
    app.run()


@app.route('/')
def fuck():
    user = "Ученик Яндекс.Лицея"
    return render_template('index.html', title='Домашняя страница',
                           username=user)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        req = request.form
        name = req.get("name")
        address = req.get("address")
        phone_number = req.get("phone_number")
        password = req.get("password")
        if name and address and phone_number and password:
            db_sess = db_session.create_session()
            user = User()
            user.name = name
            user.address = address
            user.phone_number = phone_number
            user.set_password(password=password)
            db_sess.add(user)
            db_sess.commit()
        print(name, address, phone_number, password)
        return redirect(request.url)
    return render_template("reg.html")


if __name__ == '__main__':
    main()
