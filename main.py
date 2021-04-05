from flask import Flask
from flask import render_template
from flask import request, redirect
from flask_login import LoginManager
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from flask_login import user_logged_in

from data import db_session
from data.products import Product
from data.users import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "my_shop_secret_key"
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/my_shop.db")
    app.run()


@app.route('/')
def fuck():
    db_sess = db_session.create_session()
    lst_products = db_sess.query(Product).all()
    # print(lst_products)
    return render_template('index.html', title='Домашняя страница',
                           page="home", lst_products=lst_products)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        req = request.form
        phone_number = req.get("phone_number")
        password = req.get("password")
        print(phone_number)
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.phone_number == phone_number).first()
        login_user(user)
        return redirect("/")
    return render_template("login.html")


@app.route("/add_to_cart/<int:product_id>", methods=['GET', 'POST'])
def add_to_cart(product_id):
    db_sess = db_session.create_session()
    if user_logged_in:
        db_sess.query(User).filter(User.id == current_user.get_id()).update({User.cart: User.cart + f"{product_id},"})
        db_sess.commit()
        db_sess.close()
        return redirect("/")


@app.route("/delete_from_cart/<int:product_id>", methods=['GET', 'POST'])
def delete_from_cart(product_id):
    if user_logged_in:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.get_id()).first()
        cart = user.cart.split(",")
        cart.remove(str(product_id))
        db_sess.query(User).filter(User.id == current_user.get_id()).update({User.cart: ",".join(cart)})
        db_sess.commit()
        db_sess.close()
    return redirect("/cart")


@app.route("/cart", methods=["GET", "POST"])
def cart():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.get_id()).first()
    cart = user.cart.split(",")
    cart.pop()
    # print(cart)
    lst_products = [db_sess.query(Product).filter(Product.id == int(i)).first() for i in cart]
    return render_template("index.html", title='Корзина',
                           page="cart", lst_products=lst_products)





@app.route("/registration", methods=["GET", "POST"])
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
            db_sess.close()
        print(name, address, phone_number, password)
        return redirect("/")
    return render_template("reg.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    main()
