from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:  #sessionda giriş yapıldı bilgisi varsa kontrol panelini erişime açıyor.
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın!","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kulanıcı Kayıt Formu

class RegisterForm(Form):
    #isim alanın sınırlandırılması 
    name = StringField("İsim Soyisim",validators=[validators.length(min = 4,max = 25)])
    username = StringField("Kullanıcı Adı",validators=[validators.length(min = 2,max = 35),validators.DataRequired()])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Geçerli Bir Email ADresi Giriniz..")])
    password = PasswordField("Parola:",validators=[

        validators.DataRequired(message = "Lütfen Bir Parola Belirleyin"),
        validators.EqualTo(fieldname ="confirm", message = "Şifreleri aynı giriniz")
    ])
    confirm = PasswordField("Parolayı Tekrar Giriniz",validators =[validators.DataRequired()])


#Giriş Formu
class LoginForm(Form):

    username = StringField("Kullanıcı Adı",validators=[validators.length(min = 2,max = 35),validators.DataRequired()])
    password = PasswordField("Parola:")

#Database
app = Flask(__name__)
app.secret_key="asblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "asblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#ASBlog
@app.route("/")
def index():
    return render_template("index.html")

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0 :

        articles = cursor.fetchall()
        
        return render_template("articles.html",articles = articles)

    else:

        return render_template("articles.html")



#Kayıt Olma Fonksiyonu
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) #parola şifreleme


        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Kaydınız başarıyla alınmıştır.","success")
        
       


        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)


#Giriş Yapma Fonksiyonu        
@app.route("/login",methods =["POST","GET"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" :
        username =form.username.data
        password_entered = form.password.data        

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password): #girilen parolayle gerçek parolanın kontrolünü yapıyor.
                flash("Başarıyla giriş yaptınız.","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("dashboard"))    
            else:
                    flash("Parola yanlış girildi.","danger")
                    return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor!","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form)

#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    try:
        int(id)

        if result > 0 :
            article = cursor.fetchone()
            return render_template("article.html",article = article)
        else:
            return render_template("article.html")

    except ValueError:
        return redirect(url_for(id))       
#Makale Güncelleme










#Makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id)) #makalenin giriş yapan kullanıcıya ait olup olmadığını anlamak için

    if result > 0 :

        sorgu2 = "Delete  From articles where id = %s"
        
        cursor.execute(sorgu2,(id,))
        
        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok veya Bu işleme yetkiniz yok!","danger")
        
        return redirect(url_for("index"))

#Çıkış Yapma Fonksiyonu
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Hakkımda
@app.route("/about")
def about():
    return render_template("about.html")    

#Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s"
    
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0 :
        
        article = cursor.fetchall()

        return render_template("dashboard.html",articles = article)


    else:

    
        return render_template("dashboard.html")

#Makale Ekleme
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
               
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        
        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()
        
        flash("Makale Başarıyla Eklendi.","warning")

        cursor.close()

        

        return  redirect(url_for("dashboard"))

    

    return render_template("addarticle.html",form = form)


#Makale Formu  
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators = [validators.length(min = 5, max = 100)])
    content = TextAreaField("Makale İçeriği",validators = [validators.length(min = 10)])




if __name__ =="__main__":
    app.run(debug=True)


