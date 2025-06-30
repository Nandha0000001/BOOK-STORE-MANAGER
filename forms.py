from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField, DateField, HiddenField, SearchField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or login.')


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    isbn = StringField('ISBN', validators=[DataRequired(), Length(min=10, max=13)])
    publisher = StringField('Publisher', validators=[Optional(), Length(max=100)])
    publication_date = DateField('Publication Date', validators=[Optional()], format='%Y-%m-%d')
    category = SelectField('Category', choices=[
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('mystery', 'Mystery'),
        ('thriller', 'Thriller'),
        ('romance', 'Romance'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('self-help', 'Self-Help'),
        ('children', 'Children'),
        ('young-adult', 'Young Adult'),
        ('other', 'Other')
    ])
    image = FileField('Book Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only (jpg, jpeg, png)!')
    ])
    submit = SubmitField('Save Book')


class SearchForm(FlaskForm):
    query = SearchField('Search books...', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('', 'All Categories'),
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('mystery', 'Mystery'),
        ('thriller', 'Thriller'),
        ('romance', 'Romance'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('self-help', 'Self-Help'),
        ('children', 'Children'),
        ('young-adult', 'Young Adult'),
        ('other', 'Other')
    ], validators=[Optional()])
    submit = SubmitField('Search')
    
class AdminBookSearchForm(FlaskForm):
    query = SearchField('Search by title, author or ISBN...', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('', 'All Categories'),
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('mystery', 'Mystery'),
        ('thriller', 'Thriller'),
        ('romance', 'Romance'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('self-help', 'Self-Help'),
        ('children', 'Children'),
        ('young-adult', 'Young Adult'),
        ('other', 'Other')
    ], validators=[Optional()])
    stock_status = SelectField('Stock Status', choices=[
        ('', 'All'),
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock (<5)'),
        ('out_of_stock', 'Out of Stock')
    ], validators=[Optional()])
    sort_by = SelectField('Sort By', choices=[
        ('title_asc', 'Title (A-Z)'),
        ('title_desc', 'Title (Z-A)'),
        ('price_asc', 'Price (Low to High)'),
        ('price_desc', 'Price (High to Low)'),
        ('stock_asc', 'Stock (Low to High)'),
        ('stock_desc', 'Stock (High to Low)'),
        ('date_asc', 'Date Added (Oldest First)'),
        ('date_desc', 'Date Added (Newest First)')
    ], validators=[Optional()], default='title_asc')
    submit = SubmitField('Filter')


class AddToCartForm(FlaskForm):
    book_id = HiddenField('Book ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField('Add to Cart')


class CheckoutForm(FlaskForm):
    shipping_address = TextAreaField('Shipping Address', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer')
    ], validators=[DataRequired()])
    submit = SubmitField('Place Order')


class UpdateOrderStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Status')
    
class AdminOrderSearchForm(FlaskForm):
    query = SearchField('Search by order ID or customer username...', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[Optional()])
    date_from = DateField('Date From', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateField('Date To', format='%Y-%m-%d', validators=[Optional()])
    sort_by = SelectField('Sort By', choices=[
        ('date_desc', 'Date (Newest First)'),
        ('date_asc', 'Date (Oldest First)'),
        ('total_desc', 'Amount (High to Low)'),
        ('total_asc', 'Amount (Low to High)')
    ], validators=[Optional()], default='date_desc')
    submit = SubmitField('Filter')


class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[
        ('customer', 'Customer'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    submit = SubmitField('Update User')
    
class AdminUserSearchForm(FlaskForm):
    query = SearchField('Search by username or email...', validators=[Optional()])
    role = SelectField('Role', choices=[
        ('', 'All Roles'),
        ('customer', 'Customer'),
        ('admin', 'Admin')
    ], validators=[Optional()])
    sort_by = SelectField('Sort By', choices=[
        ('username_asc', 'Username (A-Z)'),
        ('username_desc', 'Username (Z-A)'),
        ('email_asc', 'Email (A-Z)'),
        ('email_desc', 'Email (Z-A)'),
        ('date_asc', 'Joined (Oldest First)'),
        ('date_desc', 'Joined (Newest First)')
    ], validators=[Optional()], default='username_asc')
    submit = SubmitField('Filter')
