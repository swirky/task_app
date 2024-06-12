from flask import Flask,render_template,url_for,request,flash,g,redirect,session
from datetime import datetime
from userPass import UserPass
from userFactory import UserFactory
from config import app,app_info
from config import get_db,close_db
import sqlite3
import os
import string
import random
import binascii

        
@app.route('/init_app')
def init_app():
    """
    The init_app function is used to initialize the application.
    It checks if there are any active users in the database, and if not, it creates a new user with admin privileges.
    
    
    :return: A redirect to the index page
    :doc-author: Trelent
    """
    db=get_db()
    sql_statement='select count(*) as cnt from users where is_active and is_admin;'
    cur = db.execute(sql_statement)
    active_admins = cur.fetchone()
    
    if active_admins!=None and active_admins['cnt']>0:
        flash('Aplikacja gotowa do użycia. Znaleziono aktywnych użytkowników!')
        return redirect(url_for('index'))
    else:
        admin_user = UserFactory.create_user("admin","","")
        admin_user.get_random_user_passw()
        sql_statement = 'insert into users (name, password, is_active, is_admin) values (?, ?, True, True)'
        db.execute(sql_statement, [admin_user.user, admin_user.hashed_passwd()])
        db.commit()
        flash('Admin {} z hasłem {} został dodany'.format(admin_user.user, admin_user.password))
        return redirect(url_for('index'))
    

@app.route('/')
def index():
    """
    The index function is the default function that gets called when a user visits
    the root of the website. It renders the index.html template, which contains all
    of our HTML code for displaying content on this page.
    
    :return: The index
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()
    return render_template('index.html', active_menu='Strona główa', login=login)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    The register function is responsible for handling the registration of new users.
    It first checks if the request method is GET or POST, and if it's GET, it renders a template with an empty user dictionary.
    If the request method is POST, then we check to see if all fields are filled out correctly (i.e., no blank fields).  If they are not filled out correctly, we flash a message explaining what went wrong and render the register template again with an empty user dictionary so that they can try again.  If everything was filled out correctly in terms of form validation (i.e., no blank fields), then we create
    
    :return: A redirect to the login function
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    db=get_db()
    message = None 
    user = {}  #tablica do przechowywania danych z formularza
    
    if request.method =='GET':
        return render_template('register.html', user=user, login=login)
    else:
        user['user_name'] ="" if not 'user_name' in request.form else request.form['user_name']
        user['user_password']= "" if not 'user_password' in request.form else request.form['user_password']
        user['repeat_password']="" if not 'repeat_password' in request.form else request.form['repeat_password']
        user['user_type']= "standard" if not 'user_type' in request.form else request.form['user_type']
    
        sql_query='select count(*) as cnt from users where name=?;'
        cur = db.execute(sql_query,[user['user_name']])
        record = cur.fetchone()
        is_user_name_unique = (record['cnt']==0)

        if user['user_name']=="":
            message='Nie podano nazwy użytkownika!'
        elif user['user_password']=="":
            message='Nie podano hasła!'
        elif user['user_password']!=user['repeat_password']:
            message='Hasła nie są takie same'
        elif not is_user_name_unique:
            message="Konto z tą nazwą użytkownika już istnieje!"
            
        if not message:
            new_user = UserFactory.create_user(user['user_type'],user['user_name'], user['user_password'])
            
            sql_statement='insert into users (name,password,is_active,is_admin) values (?,?,?,?)'
            db.execute(sql_statement,[new_user.user,new_user.hashed_passwd(), new_user.is_active,new_user.is_admin])
            db.commit()
            flash('Użytkownik {} został utworzony'.format(user['user_name']))
            return redirect(url_for('login'))
        else:
            flash('Correct error: {}'.format(message))
            return render_template('register.html',user=user, login=login)



    
@app.route('/login', methods=['GET','POST'])
def login():
    """
    The login function is used to log in a user.
        It takes no arguments and returns nothing.
    
    
    :return: The login
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    if request.method=="GET":
        return render_template("login.html", active_menu='login', login=login)
    else:
        if 'user_name' not in request.form:
            user_name = ''
        else:
            user_name = request.form['user_name']
        if 'user_pass' not in request.form:
            user_pass=''
        else:
            user_pass = request.form['user_pass']
            
        login = UserPass(user_name,user_pass)
        login_record = login.login_user()
        
        if login_record!=None:
            session['user']= user_name
            flash('Zalogowano pomyślnie! Witaj {}'.format(user_name))
            return redirect(url_for('index'))
        else:
            flash('Logowanie nie powiodło się. Spróbuj ponownie.')
            return render_template('login.html', active_menu='login',login=login)
    
@app.route('/logout')
def logout():
    """
    The logout function is used to logout the user from the session.
        It checks if there is a 'user' in session, and if so it pops it out of
        the session and flashes a message that says &quot;Wylogowano&quot;. Then redirects
        to login page.
    
    :return: A redirect to the login page
    :doc-author: Trelent
    """
    if 'user' in session:
        session.pop('user',None)
        flash('Wylogowano')
    return redirect(url_for('login'))

@app.route('/users')
def users():
    """
    The users function is used to display a list of all users in the database.
    It also checks if the user is logged in as an admin, and if not, redirects them to login page.
    
    :return: A rendered template, which is a string
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    if login.is_admin==False:
        flash('Nie jesteś zalogowany na konto administratora. Zaloguj się aby odwiedzić tę stronę!')
        return redirect(url_for('login'))
    else:
        db=get_db()
        sql_command='select * from users;'
        cur=db.execute(sql_command)
        users=cur.fetchall()
        return render_template('users.html', user_list=users, login=login)

@app.route('/user_status_change/<action>/<user_name>')
def user_status_change(action, user_name):
    """
    The user_status_change function is called when the user clicks on a button to change the status of another user.
    The function takes two arguments: action and user_name. The action argument can be either 'active' or 'admin'. 
    If it's active, then we toggle whether that particular user is active or not by adding 1 to their current value mod 2 (which will flip between 0 and 1). 
    If it's admin, then we do the same thing but for their admin status instead.
    
    :param action: Determine which action to take on the user
    :param user_name: Identify the user whose status is to be changed
    :return: A redirect to the users page
    :doc-author: Trelent
    """
    if not 'user' in session:
        return redirect(url_for('login'))
    login = session['user']
    
    db=get_db()
    
    if action == 'active':
        db.execute('update users set is_active =(is_active + 1) % 2 where name= ? and name <> ?',[user_name,login])
        db.commit()
    elif action =='admin':
        db.execute('update users set is_admin = (is_admin + 1) % 2 where name= ? and name <> ?',[user_name,login])
        db.commit()
    return redirect(url_for('users'))
        

@app.route('/edit_user/<user_name>', methods=['GET', 'POST'])
def edit_user(user_name):
    return 'not implemented'


@app.route('/user_delete/<user_name>', methods=['POST'])
def delete_user(user_name):
    """
    The delete_user function deletes a user from the database.
        Args:
            user_name (str): The name of the user to be deleted.
    
    
    :param user_name: Delete the user with that name from the database
    :return: A redirect to the users page
    :doc-author: Trelent
    """
    if request.method=='POST':
        
        if not 'user' in session:
            return redirect(url_for(login))
        login = session['user']
        
        db=get_db()
        sql_zapytanie='DELETE from users where name=?;'
        if user_name!=login:
            db.execute(sql_zapytanie,[user_name])
            db.commit()
        else:
            flash('Nie można usunąć konta na którym jesteś aktualnie zalogowany!')
            return redirect(url_for('users'))
        
        flash('Usunieto uzytkownika {}!'.format(user_name))
        return redirect(url_for('users'))

        
@app.route('/new_user', methods=['GET', 'POST'])
def new_user():
    """
    The new_user function is responsible for creating a new user.
    It first checks if the user is logged in as an admin, and if not, redirects them to the login page.
    If they are logged in as an admin, it then checks whether or not there was a POST request made to this function.  If so, it creates a new User object using the UserFactory class and inserts that into our database.
    
    :return: A redirect to the users page
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    if not login.is_admin:
        flash('Nie jesteś zalogowany na konto administratora. Zaloguj się aby odwiedzić tę stronę!')
        return redirect(url_for('login'))
    
    db=get_db()
    message = None 
    user = {}  #tablica do przechowywania danych z formularza
    
    if request.method =='GET':
        return render_template('new_user.html', active_menu='users', user=user, login=login)
    else:
        user['user_name'] ="" if not 'user_name' in request.form else request.form['user_name']
        user['user_password']= "" if not 'user_password' in request.form else request.form['user_password']
        user['user_type']= "" if not 'user_type' in request.form else request.form['user_type']
    
    sql_query='select count(*) as cnt from users where name=?;'
    cur = db.execute(sql_query,[user['user_name']])
    record = cur.fetchone()
    is_user_name_unique = (record['cnt']==0)

    if user['user_name']=="":
        message='Nie podano nazwy użytkownika!'
    elif user['user_password']=="":
        message='Nie podano hasła!'
    elif not is_user_name_unique:
        message="Konto z tą nazwą użytkownika już istnieje!"
    elif user['user_type']=="":
        message="Nie podano typu użytkownika (standard lub admin)"
        
    if not message:
        new_user = UserFactory.create_user(user['user_type'],user['user_name'], user['user_password'])
        
        sql_statement='insert into users (name,password,is_active,is_admin) values (?,?,?,?)'
        db.execute(sql_statement,[new_user.user,new_user.hashed_passwd(), new_user.is_active,new_user.is_admin])
        db.commit()
        flash('User {} has been created'.format(user['user_name']))
        return redirect(url_for('users'))
    else:
        flash('Correct error: {}'.format(message))
        return render_template('new_user.html', active_menu='users', user=user)
        
        
@app.route('/new_task', methods=['GET', 'POST'])
def new_task():
    """
    The new_task function is responsible for creating a new task.
    It takes the following arguments:
        - request (object): The HTTP request object. This contains all of the information about the current HTTP request, including form data and other metadata.
        - session (dict): A dictionary containing session variables that are available across requests from a single user. These variables persist until they are explicitly removed or when a user's session expires due to inactivity.
    
    :return: A redirect to the task_content function
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()
    
    if not login.is_valid:
        flash('Nie jesteś zalogowany na konto użytkownika. Zaloguj się aby odwiedzić tę stronę!')
        return redirect(url_for('login'))
    else:    
        if request.method == 'GET':
            return render_template('new_task.html', login=login)
        else:
            task_name = request.form.get('task_name', '')
            priority = request.form.get('priority', '')
            task_content = request.form.get('task_content', '')
            status = request.form.get('status', '')
            deadline= request.form.get('deadline', '')

            if not task_name:
                flash('Zadanie musi posiadać jakiś tytuł/nazwę')
                return redirect(url_for('new_task'))
            if not deadline:
                flash('Proszę podać termin dla nowego zadania!')
                return redirect(url_for('new_task'))
            
            deadline_dt = datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
            
            flash('Utworzono taska poprawnie!')
            
            db = get_db()
            sql_command = 'INSERT INTO tasks (task_name, task_content, priority, deadline, status, user_id) VALUES (?, ?, ?, ?,?, ?)'
            db.execute(sql_command, [task_name, task_content, priority ,deadline_dt, status, login.user_id])
            db.commit()
            
            return redirect(url_for('task_content',priority=priority, task_content=task_content,deadline=deadline,task_name=task_name, status=status))

@app.route('/task_content', methods=['GET'])
def task_content():
    """
    The task_content function is used to display the content of a task.
        It takes in the following arguments:
            - login: The user's login information, which is passed from the session.get('user') function.
            - priority: The priority level of a task, which is passed from request.args.get('priority', &quot;&quot;).  This argument defaults to an empty string if no value has been assigned yet (i.e., when creating a new task).
            - task_content: The content of a given task, which is passed from request.args['task_content'].  This argument defaults to
    
    :return: The task_content
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()
    
    task_name = request.args.get('task_name', "")
    priority = request.args.get('priority', "")
    task_content = request.args.get('task_content', "")
    deadline = request.args.get('deadline', "")
    status = request.args.get('status', "")

    
    return render_template('task_content.html', 
                           login=login, 
                           priority=priority, 
                           task_content=task_content, 
                           task_name=task_name,
                           deadline=deadline,
                           status=status
                           )

@app.route('/task_list', methods=['GET','POST'])
def task_list():
    """
    The task_list function is responsible for displaying the list of tasks
        that are associated with a particular user. It first checks to see if the
        user is logged in, and if not, redirects them to the login page. If they are
        logged in, it queries the database for all tasks associated with their id and 
        displays them on a webpage.
    
    :return: A rendered template
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    if not login.is_valid:
        flash('Nie jesteś zalogowany na konto użytkownika. Zaloguj się aby odwiedzić tę stronę!')
        return redirect(url_for('login'))
    else:    
        db=get_db()
        sql_command='select * from tasks where user_id=?;'
        cur=db.execute(sql_command,[login.user_id])
            
        
        tasks=cur.fetchall()
        return render_template('task_list.html', tasks=tasks, login=login)

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    """
    The delete_task function deletes a task from the database.
        Args:
            task_id (int): The id of the task to be deleted.
        Returns: A redirect to the tasks list page.
    
    :param task_id: Identify the task to be deleted
    :return: A redirect response to the task_list view function
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    db=get_db()
    sql_zapytanie='DELETE from tasks where id=?;'
    db.execute(sql_zapytanie,[task_id])
    db.commit()
    flash('Usunięto taska!')
    return redirect(url_for('task_list'))

@app.route('/edition/<int:task_id>', methods=['GET','POST'])
def edition_task(task_id):
    """
    The edition_task function is responsible for editing a task.
    It takes the id of the task to be edited as an argument and returns a rendered template with form fields filled in with data from that particular task.
    The function also handles POST requests, which are sent when user submits changes to the database.
    
    :param task_id: Identify the task to be edited
    :return: The edition
    :doc-author: Trelent
    """
    login = UserPass(session.get('user'))
    login.get_user_info()

    if not login.is_valid:
        flash('Nie jesteś zalogowany na konto użytkownika. Zaloguj się aby odwiedzić tę stronę!')
        return redirect(url_for('login'))
    else:
        if request.method == 'GET':
            db=get_db()
            sql_zapytanie='select id,task_name,task_content,priority,deadline,status from tasks where id=?'
            cur=db.execute(sql_zapytanie,[task_id])
            task=cur.fetchone()
            return render_template('edition.html', task=task, login=login)
        else:
            if 'task_name' in request.form:
                task_name=request.form['task_name']
                
            if 'task_content' in request.form:
                task_content=request.form['task_content']

            if 'priority' in request.form:
                priority=request.form['priority']
                
            if 'deadline' in request.form:
                deadline=request.form['deadline']

            if 'status' in request.form:
                status=request.form['status']
                
            db=get_db()
            sql_command = 'update tasks set task_name=?, task_content=?,priority=?, deadline=?, status=? where id=?'
            db.execute(sql_command, [task_name,task_content, priority, deadline, status, task_id])
            db.commit()
            return redirect(url_for('task_list'))
            
        
        