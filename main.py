from flask import Flask, render_template, url_for, redirect, flash, request
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey
from flask_bootstrap import Bootstrap5
import time

# TODO CREATE APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# TODO CONFIGURE FLASK LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# TODO CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    orders = relationship('Order', backref='user', lazy=True)
    carts = relationship('Cart', backref='user', lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500))
    image_url: Mapped[str] = mapped_column(String(300))
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    order_items = relationship('OrderItem', backref='product', lazy=True)
    cart_items = relationship('CartItem', backref='product', lazy=True)


class Order(db.Model):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    order_date: Mapped[str] = mapped_column(String(200), nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    order_items = relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_at_purchase: Mapped[float] = mapped_column(Float, nullable=False)


class Cart(db.Model):
    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(200), nullable=False)
    cart_items = relationship('CartItem', backref='cart', lazy=True)


class CartItem(db.Model):
    __tablename__ = "cart_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(Integer, ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)



with app.app_context():
    db.create_all()


# TODO ROUTES
@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)


@app.route('/products/<int:pro_id>')
def show_product(pro_id):
    product = Product.query.get(pro_id)
    return render_template('product.html', product=product)


@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id, created_at=time.strftime('%Y-%m-%d %H:%M:%S'))
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash('Item added to cart')
    return redirect(url_for('home'))


@app.route('/cart')
@login_required
def cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return render_template('cart.html', cart_items=[])

    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    return render_template('cart.html', cart_items=cart_items)


@app.route('/checkout')
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('No items in the cart.')
        return redirect(url_for('home'))

    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    order = Order(user_id=current_user.id, order_date=time.strftime('%Y-%m-%d %H:%M:%S'), total_amount=total_amount)
    db.session.add(order)
    db.session.commit()

    for item in cart_items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity,
                               price_at_purchase=item.product.price)
        db.session.add(order_item)

    db.session.commit()

    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    flash('Order placed successfully!')
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
