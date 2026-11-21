
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from app.database import engine, SessionLocal, Base
from app.models import User, Product, Order, OrderItem


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Commerce Web Application")

app.add_middleware(
    SessionMiddleware,
    secret_key="replace-this-with-a-long-random-secret"
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(directory="app/templates")

# Password hashing
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


# Database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Get logged-in user
def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


# Add sample products
def seed_products(db: Session):
    if db.query(Product).count() == 0:
        products = [
            Product(
                name="Laptop",
                description="Powerful laptop for work and study.",
                price=50000,
                image_url="https://placehold.co/400x250?text=Laptop",
                stock=10
            ),
            Product(
                name="Smartphone",
                description="Modern smartphone with great features.",
                price=20000,
                image_url="https://placehold.co/400x250?text=Smartphone",
                stock=15
            ),
            Product(
                name="Headphones",
                description="Comfortable headphones with clear sound.",
                price=2000,
                image_url="https://placehold.co/400x250?text=Headphones",
                stock=20
            ),
            Product(
                name="Smart Watch",
                description="Smart watch for your daily activities.",
                price=3000,
                image_url="https://placehold.co/400x250?text=Smart+Watch",
                stock=12
            )
        ]

        db.add_all(products)
        db.commit()


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_products(db)
    finally:
        db.close()


# Home page
@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    user = get_current_user(request, db)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "user": user
        }
    )


# Registration page
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "user": None,
            "error": None
        }
    )


# Register new user
@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": "Email already registered."
            },
            status_code=400
        )

    user = User(
        username=username,
        email=email,
        password=pwd_context.hash(password)
    )

    db.add(user)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": None,
                "error": "Could not create account. Try another email."
            },
            status_code=400
        )

    return RedirectResponse(
        url="/login",
        status_code=303
    )


# Login page
@app.get("/login")
def login_page(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "user": None,
            "error": None,
            "next": next
        }
    )


# Login user
@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "user": None,
                "error": "Invalid email or password.",
                "next": next
            },
            status_code=400
        )

    request.session.clear()
    request.session["user_id"] = user.id

    # Only allow safe local redirects
    if not next.startswith("/") or next.startswith("//"):
        next = "/"

    return RedirectResponse(
        url=next,
        status_code=303
    )


# Logout
@app.get("/logout")
def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=303
    )


# Add product to cart
@app.post("/cart/add/{product_id}")
def add_to_cart(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # Check whether the user is logged in
    user = get_current_user(request, db)

    if not user:
        return RedirectResponse(
            url="/login?next=/",
            status_code=303
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product or product.stock <= 0:
        return RedirectResponse("/", status_code=303)

    cart = request.session.get("cart", {})
    key = str(product_id)

    current_quantity = int(cart.get(key, 0))

    if current_quantity < product.stock:
        cart[key] = current_quantity + 1

    request.session["cart"] = cart

    return RedirectResponse(
        url="/cart",
        status_code=303
    )


# View cart
@app.get("/cart")
def view_cart(
    request: Request,
    db: Session = Depends(get_db)
):
    cart = request.session.get("cart", {})
    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = db.query(Product).filter(
            Product.id == int(product_id)
        ).first()

        if product:
            quantity = int(quantity)
            subtotal = product.price * quantity

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })

            total += subtotal

    user = get_current_user(request, db)

    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "cart_items": cart_items,
            "total": total,
            "user": user
        }
    )


# Remove product from cart
@app.post("/cart/remove/{product_id}")
def remove_from_cart(
    product_id: int,
    request: Request
):
    cart = request.session.get("cart", {})
    cart.pop(str(product_id), None)

    request.session["cart"] = cart

    return RedirectResponse(
        url="/cart",
        status_code=303
    )


# Checkout
@app.post("/checkout")
def checkout(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if not user:
        return RedirectResponse("/login", status_code=303)

    cart = request.session.get("cart", {})

    if not cart:
        return RedirectResponse("/cart", status_code=303)

    order = Order(
        user_id=user.id,
        total_amount=0
    )

    total = 0

    for product_id, quantity in cart.items():
        product = db.query(Product).filter(
            Product.id == int(product_id)
        ).first()

        quantity = int(quantity)

        if not product or quantity <= 0 or quantity > product.stock:
            return RedirectResponse("/cart", status_code=303)

        subtotal = product.price * quantity
        total += subtotal

        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=quantity,
                price=product.price
            )
        )

        product.stock -= quantity

    order.total_amount = total

    db.add(order)
    db.commit()

    request.session["cart"] = {}

    return RedirectResponse(
        url="/orders",
        status_code=303
    )


# View order history
@app.get("/orders")
def view_orders(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if not user:
        return RedirectResponse("/login", status_code=303)

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={
            "orders": orders,
            "user": user
        }
    )


# Health check
@app.get("/health")
def health():
    return {
        "status": "E-Commerce application is running"
    }
