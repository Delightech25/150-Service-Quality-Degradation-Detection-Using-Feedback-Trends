import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, redirect
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

app = Flask(__name__)


# Load feedback dataset
df = pd.read_csv("dataset/feedback.csv", encoding='latin1')

# Clean Rating
df['Rating'] = df['Rating'].str.extract('(\d+\.?\d*)')
df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')

# Convert Date
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

df = df.dropna(subset=['Rating','Date','Comments'])


# ML Model
df['Quality'] = df['Rating'].apply(lambda x: "Poor" if x<=2 else "Good")

vectorizer = CountVectorizer()

X = vectorizer.fit_transform(df['Comments'])

y = df['Quality']

model = MultinomialNB()

model.fit(X,y)



# Login Page
@app.route('/')
def login():
    return render_template("login.html")



# Login Check
@app.route('/login',methods=['POST'])
def login_check():

    username = request.form['username'].strip()
    password = request.form['password'].strip()

    users = pd.read_csv("dataset/users.csv")

    # Remove spaces
    users['username'] = users['username'].astype(str).str.strip()
    users['password'] = users['password'].astype(str).str.strip()

    user = users[
        (users['username'] == username) &
        (users['password'] == password)
    ]

    if len(user) > 0:
        return redirect("/dashboard")
    else:
        return "Invalid Login"


# Register Page
@app.route('/register')
def register():
    return render_template("register.html")



# Register Save
@app.route('/register_user',methods=['POST'])
def register_user():

    username=request.form['username']
    password=request.form['password']

    users=pd.read_csv("dataset/users.csv")

    new_user=pd.DataFrame([[username,password]],
                          columns=['username','password'])

    users=pd.concat([users,new_user])

    users.to_csv("dataset/users.csv",index=False)

    return redirect("/")



# Dashboard
@app.route('/dashboard')
def dashboard():

    total_reviews=len(df)

    avg_rating=round(df['Rating'].mean(),2)

    low_rating=len(df[df['Rating']<=2])

    high_rating=len(df[df['Rating']>=4])


    # Trend Detection

    df_sorted=df.sort_values('Date')

    old=df_sorted.head(50)['Rating'].mean()

    recent=df_sorted.tail(50)['Rating'].mean()

    if recent<old:
        status="Degrading"
    else:
        status="Stable"



    # Trend Chart

    trend=df.groupby(df['Date'].dt.month)['Rating'].mean()

    plt.figure()

    trend.plot()

    plt.title("Rating Trend")

    plt.savefig("static/trend.png")

    plt.close()



    # Category Chart

    cat=df['Category'].value_counts()

    plt.figure()

    cat.plot(kind='bar')

    plt.title("Category Distribution")

    plt.savefig("static/category.png")

    plt.close()



    return render_template("dashboard.html",
                           total_reviews=total_reviews,
                           avg_rating=avg_rating,
                           low_rating=low_rating,
                           high_rating=high_rating,
                           status=status)



# Prediction
@app.route('/predict',methods=['GET','POST'])
def predict():

    result=""

    if request.method=="POST":

        text=request.form['feedback']

        vec=vectorizer.transform([text])

        result=model.predict(vec)[0]

    return render_template("predict.html",result=result)



@app.route('/logout')
def logout():

    return redirect('/')



if __name__=="__main__":
    app.run(debug=True)