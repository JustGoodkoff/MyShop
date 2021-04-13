from datetime import timedelta

from flask import Flask
from flask import render_template
from flask import request, redirect
from flask import session
from flask_login import LoginManager
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from data import db_session
from data.orders import Order
from data.products import Product
from data.unreg_orders import UnregOrder
from data.users import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "my_shop_secret_key"
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/my_shop.db")
    app.run(host="127.0.0.1", port="8000")


@app.route('/')
def home():
    db_sess = db_session.create_session()
    lst_products = db_sess.query(Product).all()
    lst_products.reverse()
    db_sess.close()
    return render_template('index.html', title='Домашняя страница',
                           page="home", lst_products=lst_products, active_sort="Сначала актуальные")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=31)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        req = request.form
        phone_number = req.get("phone_number")
        password = req.get("password")
        if phone_number != "" and password != "":
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.phone_number == phone_number).first()
            if user and user.check_password(password):
                login_user(user)
                if session.get("cart"):
                    db_sess.query(User).filter(User.id == current_user.get_id()).update(
                        {User.cart: User.cart + ",".join([str(i) for i in session["cart"]]) + ","})
                    session["cart"] = []
                db_sess.commit()
                db_sess.close()
                return redirect("/")
            else:
                return render_template("login.html", wrong_data=True)
        else:
            return render_template("login.html", empty_form=True)
    return render_template("login.html")


@app.route('/my_orders/<int:order_id>', methods=['GET', 'POST'])
def show_selected_order(order_id):
    db_sess = db_session.create_session()
    order = db_sess.query(Order).filter(Order.id == order_id).first()
    order = order.order
    lst_products = [db_sess.query(Product).filter(Product.id == i).first() for i in order.split(",")]
    return render_template("index.html", lst_products=lst_products)


@app.route('/sorted_by_low_price', methods=['GET', 'POST'])
def sorted_by_low_price():
    db_sess = db_session.create_session()
    lst_products = db_sess.query(Product).all()
    lst_products.sort(key=lambda x: int(x.price))
    db_sess.close()
    return render_template('index.html', title='Домашняя страница',
                           page="home", lst_products=lst_products, active_sort="Сначала подешевле")


@app.route('/sorted_by_high_price', methods=['GET', 'POST'])
def sorted_by_high_price():
    db_sess = db_session.create_session()
    lst_products = db_sess.query(Product).all()
    lst_products.sort(key=lambda x: -int(x.price))
    db_sess.close()
    return render_template('index.html', title='Домашняя страница',
                           page="home", lst_products=lst_products, active_sort="Сначала подороже")


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def show_selected_product(product_id):
    db_sess = db_session.create_session()
    product = db_sess.query(Product).filter(Product.id == product_id).first()
    return render_template("product.html", product_id=product_id, name=product.name, price=product.price,
                           image=product.image, description=product.description)


@app.route('/my_orders', methods=['GET', 'POST'])
def my_orders():
    db_sess = db_session.create_session()
    orders = db_sess.query(Order).filter(Order.user_id == current_user.get_id()).all()
    orders.reverse()
    if not orders:
        return render_template("orders.html", title="Заказы", empty_orders=True)
    else:
        return render_template("orders.html", title="Заказы", orders=orders)


@app.route("/create_order/<string:products_in_cart>/<int:total_cost>", methods=['GET', 'POST'])
def create_order(products_in_cart, total_cost):
    if current_user.get_id():
        db_sess = db_session.create_session()
        order = Order()
        order.user_id = current_user.get_id()
        order.order = products_in_cart
        order.total_price = total_cost
        order.quantity_of_goods = len(products_in_cart.split(","))
        db_sess.add(order)
        db_sess.query(User).filter(User.id == current_user.get_id()).update({User.cart: ""})
        db_sess.commit()
        db_sess.close()
    else:
        if request.method == "POST":
            db_sess = db_session.create_session()
            req = request.form
            address = req.get("address")
            phone_number = req.get("phone_number")
            if address != "" and phone_number != "":
                if phone_number.isdigit() and len(phone_number) == 11:
                    unreg_order = UnregOrder()
                    unreg_order.user_phone_number = phone_number
                    unreg_order.address = address
                    unreg_order.order = products_in_cart
                    unreg_order.total_price = total_cost
                    db_sess.add(unreg_order)
                    db_sess.commit()
                    db_sess.close()
                    session["cart"] = []
                    return redirect("/")
                else:
                    return render_template("reg.html", products_in_cart=products_in_cart, total_cost=total_cost,
                                           create_order=True, error_text="Ошибка при вводе данных")
            else:
                return render_template("reg.html", products_in_cart=products_in_cart, total_cost=total_cost,
                                       create_order=True, error_text="Нужно заполнить все поля!")
        return render_template("reg.html", products_in_cart=products_in_cart, total_cost=total_cost, create_order=True)
    return redirect("/")


@app.route("/cart", methods=["GET", "POST"])
def cart():
    session.permanent = True
    db_sess = db_session.create_session()
    if current_user.get_id():
        user = db_sess.query(User).filter(User.id == current_user.get_id()).first()
        products_in_cart = user.cart.split(",")
        products_in_cart = delete_removed_products(products_in_cart, "db")
        if not products_in_cart:
            return render_template("index.html", page="cart", empty_cart=True)
        else:
            lst_products = [db_sess.query(Product).filter(Product.id == int(i)).first() for i in products_in_cart]
            total_cost = sum([i.price for i in lst_products])
            products_in_cart = ",".join(products_in_cart)
            return render_template("index.html", title='Корзина',
                                   page="cart", cart=products_in_cart, lst_products=lst_products, total_cost=total_cost)
    else:
        if session.get("cart"):
            products_in_cart = session["cart"]
            products_in_cart = delete_removed_products(products_in_cart, "session")
            lst_products = [db_sess.query(Product).filter(Product.id == int(i)).first() for i in products_in_cart]
            total_cost = sum([i.price for i in lst_products])
            products_in_cart = ",".join([str(id) for id in products_in_cart])
            return render_template("index.html", title='Корзина',
                                   page="cart", cart=products_in_cart, lst_products=lst_products, total_cost=total_cost)
        else:
            return render_template("index.html", page="cart", empty_cart=True)


def delete_removed_products(products_id, data):
    db_sess = db_session.create_session()
    new_cart = []
    for product_id in products_id:
        if product_id != "":
            if db_sess.query(Product).filter(Product.id == int(product_id)).first():
                new_cart.append(product_id)
    if data == "db":
        if not len(new_cart) == len(products_id) and not len(new_cart) == 0:
            db_sess.query(User).filter(User.id == current_user.id).update({User.cart: ",".join([i for i in new_cart])})
        elif len(new_cart) == 0:
            db_sess.query(User).filter(User.id == current_user.id).update({User.cart: ""})
        else:
            return products_id
    db_sess.commit()
    db_sess.close()
    return new_cart


@app.route("/add_to_cart/<int:product_id>", methods=['GET', 'POST'])
def add_to_cart(product_id):
    if current_user.get_id():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.get_id()).first()
        if user.cart == "":
            db_sess.query(User).filter(User.id == current_user.get_id()).update({User.cart: product_id})
        else:
            db_sess.query(User).filter(User.id == current_user.get_id()).update(
                {User.cart: User.cart + f",{product_id}"})
        db_sess.commit()
        db_sess.close()
        return redirect(request.referrer)
    else:
        if session.get("cart"):
            session["cart"] = session.get("cart") + [product_id]
        else:
            session["cart"] = [product_id]
    return redirect(request.referrer)


@app.route("/delete_from_cart/<int:product_id>", methods=['GET', 'POST'])
def delete_from_cart(product_id):
    if current_user.get_id():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.get_id()).first()
        products_in_cart = user.cart.split(",")
        products_in_cart.remove(str(product_id))
        db_sess.query(User).filter(User.id == current_user.get_id()).update({User.cart: ",".join(products_in_cart)})
        db_sess.commit()
        db_sess.close()
    else:
        products_in_cart = session["cart"]
        products_in_cart.remove(product_id)
        session["cart"] = products_in_cart
    return redirect("/cart")


@app.route('/admin/create_product', methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        db_sess = db_session.create_session()
        req = request.form
        name = req.get("name")
        image = req.get("image")
        price = req.get("price")
        description = req.get("description")
        if name and price and image:
            if price.isdigit():
                product = Product()
                product.name = name
                product.image = image
                product.price = price
                product.description = description
                db_sess.add(product)
                db_sess.commit()
                db_sess.close()
                return redirect('/admin')
            else:
                return render_template("admin_create_product.html", wrong_data=True)
        else:
            return render_template("admin_create_product.html", empty_form=True)
    return render_template("admin_create_product.html")


@app.route("/registration", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db_sess = db_session.create_session()
        req = request.form
        name = req.get("name")
        address = req.get("address")
        phone_number = req.get("phone_number")
        password = req.get("password")
        if name != "" and address != "" and phone_number != "" and password != "":
            if "".join(name.split()).isalpha() and phone_number.isdigit() and len(phone_number) == 11 and \
                    len(password) >= 8:
                if not db_sess.query(User).filter(User.phone_number == phone_number).first():
                    user = User()
                    user.name = name
                    user.address = address
                    user.phone_number = phone_number
                    user.set_password(password=password)
                    db_sess.add(user)
                    db_sess.commit()
                    db_sess.close()
                else:
                    return render_template("reg.html", error_text="Аккаунт с таким номером телефона уже существует!")
            else:
                return render_template("reg.html", error_text="Ошибка при вводе данных")
        else:
            return render_template("reg.html", error_text="Нужно заполнить все поля!")
        return redirect("/login")
    return render_template("reg.html")


@app.route('/admin')
def admin():
    db_sess = db_session.create_session()
    lst_products = db_sess.query(Product).all()
    db_sess.close()
    return render_template("admin.html", lst_products=lst_products)


@app.route("/admin/change_product/<int:product_id>", methods=["GET", "POST"])
def change_product(product_id):
    if request.method == "POST":
        db_sess = db_session.create_session()
        req = request.form
        name = req.get("name")
        image = req.get("image")
        price = req.get("price")
        description = req.get("description")
        if name and image and price:
            if price.isdigit():
                product = Product()
                product.name = name
                product.image = image
                product.price = price
                product.description = description
                db_sess.query(Product).filter(Product.id == product_id).update(
                    {Product.name: product.name, Product.image: product.image, Product.price: product.price,
                     Product.description: description})
                db_sess.commit()
                db_sess.close()
                return redirect("/admin")
            else:
                return render_template("admin_change_product.html", wrong_data=True)
        else:
            return render_template("admin_change_product.html", empty_form=True)
    db_sess = db_session.create_session()
    product = db_sess.query(Product).filter(Product.id == product_id).first()
    return render_template("admin_change_product.html",
                           product_id=product_id,
                           name=product.name,
                           image=product.image,
                           price=product.price,
                           description=product.description)


@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    db_sess = db_session.create_session()
    db_sess.query(Product).filter(Product.id == product_id).delete()
    db_sess.commit()
    db_sess.close()
    return redirect("/admin")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    main()
