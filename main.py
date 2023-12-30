from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from forms import Task, Registerform, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APPKEY')
Bootstrap5(app)
database = SQLAlchemy()

if os.environ.get('LOCAL') == 'True':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///To_do_lists.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')

database.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return database.get_or_404(Users, user_id)


class Users(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    Email = database.Column(database.String(250), nullable=False, unique=True)
    Name = database.Column(database.String(250), nullable=False)
    Username = database.Column(database.String(250), nullable=False, unique=True)
    Password = database.Column(database.String(250), nullable=False)


with app.app_context():
    database.create_all()
db = sqlite3.connect('instance/To_do_lists.db', check_same_thread=False)
cursor = db.cursor()

task_list = []
df = None
title = None
y = 0
empty_list = []


@app.route('/', methods=['GET', 'POST'])
def home():
    global y, empty_list
    y = 0
    empty_list.clear()

    return render_template('home.html')


user_in_db = None
user_name_in_db = None


@app.route('/register', methods=['GET', 'POST'])
def register():
    global user_in_db, user_name_in_db
    form = Registerform()
    if form.validate_on_submit():
        email = form.Email.data
        name = form.Name.data
        username = form.Username.data
        password = form.Password.data
        if form.Password.data != form.Confirm_Password.data:
            flash("Password is not confirmed. Please try again.")
            return redirect(url_for('register'))
        Email_to_register = database.session.execute(database.select(Users).where(Users.Email == email)).scalar()
        Username_to_register = database.session.execute(
            database.select(Users).where(Users.Username == username)).scalar()
        if Email_to_register:
            user_in_db = True
            flash("You've already signed up with that email, login instead!")
            return redirect(url_for('login'))
        elif Username_to_register:
            user_name_in_db = True
            flash("This Username is not available, please pick a new one.")
            return redirect(url_for('login'))
        else:
            user_in_db = False
            user_name_in_db = False
            Secured_pw = generate_password_hash(form.Password.data, method='pbkdf2:sha256', salt_length=8)
            new_user = Users(Email=form.Email.data, Password=Secured_pw, Name=form.Name.data,
                             Username=form.Username.data)
            database.session.add(new_user)
            database.session.commit()
            login_user(new_user)
            try:
                cursor.execute(f"CREATE TABLE {new_user.Username} (id INTEGER PRIMARY KEY)")
            except sqlite3.OperationalError:
                pass
            return redirect(url_for('home'))
    return render_template('register.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.Email.data
        password = form.Password.data
        user_to_login = database.session.execute(database.select(Users).where(Users.Email == email)).scalar()
        if not user_to_login:
            flash("That email does not exist, Register instead?")
            return redirect(url_for('register'))
        if check_password_hash(user_to_login.Password, password):
            login_user(user_to_login)
            return redirect(url_for('home'))
        else:
            flash("Wrong password try again")
            return redirect(url_for('login'))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/Create-list', methods=['GET', 'POST'])
def createlist():
    global title
    form = Task()
    if form.validate_on_submit():
        title = form.List_name.data
        task_list.append(form.Task.data)
        form.Task.data = ''
        print(task_list)
        redirect('index')
    return render_template('index.html', form=form, task_list=task_list)


@app.route('/view_list', methods=['GET', 'POST'])
def lists():
    global task_list, title, df, y, empty_list
    if not current_user.is_authenticated:
        return render_template('Message.html')
    else:
        y = 0
        sql = pd.read_sql_query(f"SELECT * FROM {current_user.Username}", db)
        df = pd.DataFrame(sql)
        try:
            del df[title]
        except KeyError or TypeError:
            pass
        df['id'] = df.index
        new_df = pd.DataFrame()
        new_df[title] = task_list
        task_list = []
        new_df['id'] = new_df.index
        sql_db = df.merge(new_df, on='id', how='outer')
        print(sql_db)
        cursor.execute(f'DROP TABLE {current_user.Username}')
        sql_db.to_sql(f'{current_user.Username}', con=db, if_exists='append', index=False)
        db.commit()
        empty_list.clear()
        return render_template('View_lists.html', task_list=new_df[title], title=title)


@app.route('/all_list', methods=['GET', 'POST'])
def all_lists():
    if not current_user.is_authenticated:
        return render_template('Message.html')
    else:
        sql = pd.read_sql_query(f"SELECT * FROM {current_user.Username}", db)
        df = pd.DataFrame(sql)
        return render_template('lists.html', sql_db=df)


@app.route('/show_list/<list_id>', methods=['GET', 'POST'])
def show_list(list_id):
    if not current_user.is_authenticated:
        return render_template('Message.html')
    else:
        tasks = []
        sql = pd.read_sql_query(f"SELECT * FROM {current_user.Username}", db)
        df = pd.DataFrame(sql)
        for i in list(df[list_id]):
            tasks.append(str(i))
        print(tasks)
        for _ in range(10):
            for n in tasks:
                if n == 'None':
                    tasks.remove(n)
        if request.method == "POST":
            id_list = request.form.getlist('box')
            for i in id_list:
                if i in tasks:
                    tasks.remove(i)
            del df[list_id]
            new_df = pd.DataFrame()

            new_df[list_id] = tasks
            new_df['id'] = new_df.index
            if len(new_df[list_id]) == 0:
                sql_db = df
            else:
                sql_db = df.merge(new_df, on='id', how='outer')
            cursor.execute(f'DROP TABLE {current_user.Username}')
            sql_db.to_sql(f'{current_user.Username}', con=db, if_exists='append', index=False)
        print(tasks)
        return render_template('show_list.html', list_id=tasks, title=list_id)


@app.route('/edit_list/<the_title>', methods=["GET", "POST"])
def edit_list(the_title):
    global title, task_list, df, y, empty_list
    if not current_user.is_authenticated:
        return render_template('Message.html')
    else:
        sql = pd.read_sql_query(f"SELECT * FROM {current_user.Username}", db)
        df = pd.DataFrame(sql)
        if y == 0:
            task_list = list(df[the_title])
            empty_list = []
            for n in task_list:
                empty_list.append(str(n))
            for _ in range(10):
                for x in empty_list:
                    if x == 'None':
                        empty_list.remove(x)
            y = 1
        else:
            task_list = empty_list

        print(len(empty_list))
        form = Task()
        title = the_title
        form.List_name.data = the_title
        print(task_list)
        if form.validate_on_submit():
            title = form.List_name.data
            empty_list.append(form.Task.data)
            form.Task.data = ''
            redirect('edit')
        return render_template('edit.html', form=form, task_list=empty_list)


if __name__ == '__main__':
    app.run(debug=True)
