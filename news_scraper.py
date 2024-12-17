from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from newsapi import NewsApiClient  # Ensure this line is included
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ab2c9ff3b49c4f4c8ccc16e39b48475a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your credentials.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html', name=current_user.username)

@app.route('/scrape', methods=['POST'])
@login_required
def scrape():
    countries = request.form.getlist('countries')
    categories = request.form.getlist('categories')
    max_articles = int(request.form.get('max_articles', 50))
    articles = scraper.get_news(countries, categories, max_articles)
    return render_template('results.html', articles=articles)

class NewsScraper:
    def __init__(self, api_key):
        self.newsapi = NewsApiClient(api_key=api_key)
    
    def get_news(self, countries, categories, max_articles):
        all_articles = []
        for country in countries:
            for category in categories:
                try:
                    headlines = self.newsapi.get_top_headlines(
                        country=country,
                        category=category,
                        language='en',
                        page_size=max_articles // (len(countries) * len(categories))
                    )
                    for article in headlines.get('articles', []):
                        cleaned_article = {
                            'source': article['source']['name'],
                            'title': article.get('title', 'No Title'),
                            'description': article.get('description', 'No Description'),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt', datetime.now().isoformat()),
                            'content': article.get('content', 'No Content')
                        }
                        all_articles.append(cleaned_article)
                except Exception as e:
                    print(f"Error fetching news for {country}/{category}: {e}")
        return all_articles

scraper = NewsScraper(api_key='ab2c9ff3b49c4f4c8ccc16e39b48475a')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
