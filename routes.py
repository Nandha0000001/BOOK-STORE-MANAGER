import logging
import os
import uuid
from functools import wraps
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, abort, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from flask_wtf import FlaskForm  # Add this import

from app import db
from models import User, Book, Order, OrderItem, Cart, CartItem
from forms import (
    LoginForm, RegistrationForm, BookForm, SearchForm, 
    AddToCartForm, CheckoutForm, UpdateOrderStatusForm, UserEditForm,
    AdminBookSearchForm, AdminUserSearchForm, AdminOrderSearchForm
)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def save_book_image(form_image):
    """
    Saves an uploaded book image to the filesystem and returns the relative URL.
    """
    if not form_image or not form_image.data:
        return None
        
    # Generate a random filename to avoid collisions
    random_hex = uuid.uuid4().hex
    _, file_extension = os.path.splitext(form_image.data.filename)
    secure_name = secure_filename(random_hex + file_extension)
    
    # Create upload path if it doesn't exist
    upload_path = os.path.join('static', 'uploads', 'books')
    os.makedirs(upload_path, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_path, secure_name)
    form_image.data.save(file_path)
    
    # Return the relative URL (for use in templates)
    return os.path.join('/', upload_path, secure_name)


def register_routes(app):
    # Customer routes
    @app.route('/', methods=['GET', 'POST'])
    def index():
        form = SearchForm()
        books = Book.query
        
        if form.validate_on_submit():
            if form.query.data:
                search_term = f"%{form.query.data.strip()}%"
                books = books.filter(or_(
                    Book.title.ilike(search_term),
                    Book.author.ilike(search_term),
                    Book.description.ilike(search_term)
                ))

            if form.category.data:
                books = books.filter_by(category=form.category.data)

            # Ensure books are filtered only if there are matching results
            books = books.order_by(Book.title).all()
            if not books:
                flash('No books found matching your search criteria.', 'info')
                books = []
            else:
                # Filter out books that do not match the keyword strictly
                books = [book for book in books if form.query.data.strip().lower() in book.title.lower() or form.query.data.strip().lower() in book.author.lower() or form.query.data.strip().lower() in book.description.lower()]
                
        return render_template('index.html', books=books, form=form)

    @app.route('/book/<int:book_id>', methods=['GET', 'POST'])
    def book_detail(book_id):
        book = Book.query.get_or_404(book_id)
        form = AddToCartForm()
        form.book_id.data = book.id
        
        if form.validate_on_submit():
            if not current_user.is_authenticated:
                flash('Please log in to add items to your cart.', 'info')
                return redirect(url_for('login', next=request.url))
                
            # Prevent admin users from adding to cart
            if current_user.is_admin():
                flash('Admin users do not have access to the cart feature.', 'warning')
                return redirect(url_for('admin_dashboard'))
                
            # Create cart if it doesn't exist
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            if not cart:
                cart = Cart(user_id=current_user.id)
                db.session.add(cart)
                db.session.commit()
                
            # Check if book is already in cart
            cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book.id).first()
            if cart_item:
                cart_item.quantity += form.quantity.data
            else:
                cart_item = CartItem(
                    cart_id=cart.id,
                    book_id=book.id,
                    quantity=form.quantity.data
                )
                db.session.add(cart_item)
                
            if form.quantity.data > book.stock:
                flash(f'Only {book.stock} copies available in stock.', 'warning')
                return redirect(url_for('book_detail', book_id=book.id))
                
            db.session.commit()
            flash(f'Added {form.quantity.data} copy/copies of "{book.title}" to your cart.', 'success')
            return redirect(url_for('cart'))
            
        related_books = Book.query.filter_by(category=book.category).filter(Book.id != book.id).limit(4).all()
        return render_template('book_detail.html', book=book, form=form, related_books=related_books)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page or url_for('index'))
            else:
                flash('Login failed. Please check your email and password.', 'danger')
                
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            
            # Create empty cart for new user
            cart = Cart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()
            
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/cart', methods=['GET', 'POST'])
    @login_required
    def cart():
        # Prevent admin users from accessing the cart
        if current_user.is_admin():
            flash('Admin users do not have access to the cart feature.', 'warning')
            return redirect(url_for('admin_dashboard'))
            
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
            
        # Create a form instance for CSRF protection
        form = FlaskForm()
            
        # Handle quantity updates
        if request.method == 'POST':
            remove_item_id = request.form.get('remove_item_id')
            if remove_item_id:
                cart_item = CartItem.query.get(int(remove_item_id))
                if cart_item and cart_item.cart_id == cart.id:
                    db.session.delete(cart_item)
                    db.session.commit()
                    flash('Item removed from cart.', 'success')
                else:
                    flash('Unable to remove item from cart.', 'danger')
                return redirect(url_for('cart'))
            if cart.items:
                for item in cart.items:
                    new_quantity = request.form.get(f'quantity_{item.id}')
                    print(f"Item ID: {item.id}, New Quantity: {new_quantity}")  # Debugging
                    
                    if new_quantity and new_quantity.isdigit():
                        new_quantity = int(new_quantity)
                        if new_quantity <= 0:
                            db.session.delete(item)
                        else:
                            book = Book.query.get(item.book_id)
                            if not book:
                                flash(f'Book with ID {item.book_id} not found.', 'danger')
                                continue
                            if new_quantity > book.stock:
                                flash(f'Only {book.stock} copies of "{book.title}" available.', 'warning')
                                new_quantity = book.stock
                            item.quantity = new_quantity
                try:
                    db.session.commit()
                    flash('Cart updated successfully.', 'success')
                except Exception as e:
                    db.session.rollback()
                    print(f"Error during commit: {e}")  # Debugging
                    flash('An error occurred while updating the cart. Please try again.', 'danger')
            else:
                flash('Your cart is empty.', 'info')
            return redirect(url_for('cart'))
            
        return render_template('cart.html', cart=cart, form=form)

    @app.route('/cart/remove/<int:item_id>', methods=['POST'])
    @login_required
    def remove_from_cart(item_id):
            # Prevent admin users from accessing the cart
            if current_user.is_admin():
                flash('Admin users do not have access to the cart feature.', 'warning')
                return redirect(url_for('admin_dashboard'))
            
            # Fetch the cart item
            cart_item = CartItem.query.get_or_404(item_id)
            
            # Verify the cart belongs to the current user
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            if cart_item.cart_id != cart.id:
                abort(403)  # Forbidden access
            
            # Delete the cart item
            book_title = cart_item.book.title
            db.session.delete(cart_item)
            db.session.commit()
            
            flash(f'"{book_title}" has been removed from your cart.', 'success')
            return redirect(url_for('cart'))

    @app.route('/checkout', methods=['GET', 'POST'])
    @login_required
    def checkout():
        # Prevent admin users from accessing the checkout
        if current_user.is_admin():
            flash('Admin users do not have access to the checkout feature.', 'warning')
            return redirect(url_for('admin_dashboard'))
            
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart or not cart.items:
            flash('Your cart is empty.', 'info')
            return redirect(url_for('index'))
            
        form = CheckoutForm()
        if form.validate_on_submit():
            # Check stock before placing order
            out_of_stock = False
            for item in cart.items:
                book = Book.query.get(item.book_id)
                if item.quantity > book.stock:
                    flash(f'Only {book.stock} copies of "{book.title}" available.', 'warning')
                    out_of_stock = True
            
            if out_of_stock:
                return redirect(url_for('cart'))
                
            # Create new order
            order = Order(
                user_id=current_user.id,
                status='pending',
                total_amount=cart.total_price,
                shipping_address=form.shipping_address.data,
                payment_method=form.payment_method.data
            )
            db.session.add(order)
            db.session.flush()  # Get order ID without committing
            
            # Add order items
            for item in cart.items:
                book = Book.query.get(item.book_id)
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=item.book_id,
                    quantity=item.quantity,
                    price=book.price
                )
                db.session.add(order_item)
                
                # Update stock
                book.stock -= item.quantity
                
            # Clear cart
            for item in cart.items:
                db.session.delete(item)
                
            db.session.commit()
            flash('Your order has been placed successfully!', 'success')
            return redirect(url_for('orders'))
            
        return render_template('checkout.html', cart=cart, form=form)

    @app.route('/orders')
    @login_required
    def orders():
        # Prevent admin users from accessing the customer orders page
        if current_user.is_admin():
            flash('Admin users should use the admin orders panel instead.', 'warning')
            return redirect(url_for('admin_orders'))
            
        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template('orders.html', orders=user_orders)

    # Admin routes
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        total_books = Book.query.count()
        total_users = User.query.count()
        total_orders = Order.query.count()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        low_stock_books = Book.query.filter(Book.stock < 5).all()
        
        return render_template(
            'admin/dashboard.html',
            total_books=total_books,
            total_users=total_users,
            total_orders=total_orders,
            recent_orders=recent_orders,
            low_stock_books=low_stock_books
        )

    @app.route('/admin/books', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_books():
        form = AdminBookSearchForm(request.args)
        
        # Base query
        query = Book.query
        
        # Apply filters
        if form.query.data:
            search_term = f"%{form.query.data}%"
            query = query.filter(or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Book.isbn.ilike(search_term)
            ))
            
        if form.category.data:
            query = query.filter_by(category=form.category.data)
            
        if form.stock_status.data:
            if form.stock_status.data == 'in_stock':
                query = query.filter(Book.stock > 0)
            elif form.stock_status.data == 'low_stock':
                query = query.filter(Book.stock > 0, Book.stock < 5)
            elif form.stock_status.data == 'out_of_stock':
                query = query.filter(Book.stock == 0)
        
        # Apply sorting
        sort_value = form.sort_by.data or 'title_asc'
        if sort_value == 'title_asc':
            query = query.order_by(Book.title.asc())
        elif sort_value == 'title_desc':
            query = query.order_by(Book.title.desc())
        elif sort_value == 'price_asc':
            query = query.order_by(Book.price.asc())
        elif sort_value == 'price_desc':
            query = query.order_by(Book.price.desc())
        elif sort_value == 'stock_asc':
            query = query.order_by(Book.stock.asc())
        elif sort_value == 'stock_desc':
            query = query.order_by(Book.stock.desc())
        elif sort_value == 'date_asc':
            query = query.order_by(Book.created_at.asc())
        elif sort_value == 'date_desc':
            query = query.order_by(Book.created_at.desc())
        
        books = query.all()
        return render_template('admin/books.html', books=books, form=form)

    @app.route('/admin/books/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def add_book():
        form = BookForm()
        if form.validate_on_submit():
            # Handle file upload
            image_url = save_book_image(form.image)
            
            book = Book(
                title=form.title.data,
                author=form.author.data,
                description=form.description.data,
                price=form.price.data,
                stock=form.stock.data,
                isbn=form.isbn.data,
                publisher=form.publisher.data,
                publication_date=form.publication_date.data,
                category=form.category.data,
                image_url=image_url
            )
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('admin_books'))
            
        return render_template('admin/book_form.html', form=form, title='Add New Book')

    @app.route('/admin/books/edit/<int:book_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_book(book_id):
        book = Book.query.get_or_404(book_id)
        form = BookForm(obj=book)
        
        if form.validate_on_submit():
            # Don't use populate_obj directly since we need to handle the image separately
            book.title = form.title.data
            book.author = form.author.data
            book.description = form.description.data
            book.price = form.price.data
            book.stock = form.stock.data
            book.isbn = form.isbn.data
            book.publisher = form.publisher.data
            book.publication_date = form.publication_date.data
            book.category = form.category.data
            
            # Handle the image upload
            image_url = save_book_image(form.image)
            if image_url:
                book.image_url = image_url
                
            book.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('admin_books'))
            
        return render_template('admin/book_form.html', form=form, book=book, title='Edit Book')

    @app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_book(book_id):
        book = Book.query.get_or_404(book_id)
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
        return redirect(url_for('admin_books'))

    @app.route('/admin/users', methods=['GET'])
    @login_required
    @admin_required
    def admin_users():
        form = AdminUserSearchForm(request.args)
        
        # Base query
        query = User.query
        
        # Apply filters
        if form.query.data:
            search_term = f"%{form.query.data}%"
            query = query.filter(or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            ))
            
        if form.role.data:
            query = query.filter_by(role=form.role.data)
            
        # Apply sorting
        sort_value = form.sort_by.data or 'username_asc'
        if sort_value == 'username_asc':
            query = query.order_by(User.username.asc())
        elif sort_value == 'username_desc':
            query = query.order_by(User.username.desc())
        elif sort_value == 'email_asc':
            query = query.order_by(User.email.asc())
        elif sort_value == 'email_desc':
            query = query.order_by(User.email.desc())
        elif sort_value == 'date_asc':
            query = query.order_by(User.created_at.asc())
        elif sort_value == 'date_desc':
            query = query.order_by(User.created_at.desc())
            
        users = query.all()
        return render_template('admin/users.html', users=users, form=form)

    @app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_user(user_id):
        user = User.query.get_or_404(user_id)
        form = UserEditForm(obj=user)
        
        if form.validate_on_submit():
            # Prevent changing your own role from admin
            if user.id == current_user.id and form.role.data != 'admin':
                flash('You cannot change your own admin status.', 'danger')
                return redirect(url_for('admin_users'))
                
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_users'))
            
        return render_template('admin/user_form.html', form=form, user=user)

    @app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_user(user_id):
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin_users'))
            
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/orders', methods=['GET'])
    @login_required
    @admin_required
    def admin_orders():
        form = AdminOrderSearchForm(request.args)
        
        # Base query
        query = Order.query
        
        # Apply filters
        if form.query.data:
            # Try to convert the query to an integer (for order ID)
            try:
                order_id = int(form.query.data)
                query = query.filter(Order.id == order_id)
            except ValueError:
                # If not a number, search by customer username
                search_term = f"%{form.query.data}%"
                query = query.join(User).filter(User.username.ilike(search_term))
                
        if form.status.data:
            query = query.filter(Order.status == form.status.data)
            
        if form.date_from.data:
            query = query.filter(Order.created_at >= form.date_from.data)
            
        if form.date_to.data:
            # Add one day to include the end date fully
            end_date = form.date_to.data + timedelta(days=1)
            query = query.filter(Order.created_at < end_date)
            
        # Apply sorting
        sort_value = form.sort_by.data or 'date_desc'
        if sort_value == 'date_desc':
            query = query.order_by(Order.created_at.desc())
        elif sort_value == 'date_asc':
            query = query.order_by(Order.created_at.asc())
        elif sort_value == 'total_desc':
            query = query.order_by(Order.total_amount.desc())
        elif sort_value == 'total_asc':
            query = query.order_by(Order.total_amount.asc())
            
        orders = query.all()
        return render_template('admin/orders.html', orders=orders, form=form)

    @app.route('/admin/orders/<int:order_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def manage_order(order_id):
        order = Order.query.get_or_404(order_id)
        form = UpdateOrderStatusForm(obj=order)
        
        if form.validate_on_submit():
            order.status = form.status.data
            order.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Order status updated successfully!', 'success')
            return redirect(url_for('admin_orders'))
            
        return render_template('admin/order_detail.html', order=order, form=form)
        
    @app.route('/admin/orders/delete/<int:order_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_order(order_id):
        order = Order.query.get_or_404(order_id)
        
        # Delete order items first to avoid foreign key constraint issues
        for item in order.items:
            db.session.delete(item)
            
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully!', 'success')
        return redirect(url_for('admin_orders'))

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
