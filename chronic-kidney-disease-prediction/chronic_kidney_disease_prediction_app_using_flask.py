from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import joblib,pickle
import os
from sklearn.preprocessing import LabelEncoder
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the model and dataset
model = pickle.load(open(r"C:\sudhanshu_projects\project-task-training-course\chronic-kidney-disease-prediction\chronic_kidney_disease_prediction.pkl","rb"))
df = pd.read_csv('kidney_disease.csv')

# Print the columns to debug the KeyError
print("Columns in the dataset:", df.columns)

# Encoder for categorical data
categorical_cols = ['rbc', 'pc', 'pcc', 'ba','pcv', 'wc', 'rc', 'htn', 'dm', 'cad','appet', 'pe', 'ane']  # Adjust based on your CSV
encoder = LabelEncoder()
for col in categorical_cols:
    df[col] = encoder.fit_transform(df[col])

# Placeholder for user credentials
users = pd.DataFrame(columns=['username', 'password'])

@app.route('/')
def home():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users.loc[len(users)] = [username, password]
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users[(users['username'] == username) & (users['password'] == password)]
        if not user.empty:
            session['username'] = username
            return redirect(url_for('predict'))
        else:
            return render_template('login.html', error='Login failed. Please check your credentials.')
    return render_template('login.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_input = {}
        for col in df.columns:
            if col not in ['id', 'classification']:
                user_input[col] = request.form.get(col)
        email = request.form['email']
        
        # Convert user input into DataFrame
        user_input_df = pd.DataFrame([user_input])
        
        # Transform categorical columns
        for col in categorical_cols:
            if col in user_input_df.columns:
                user_input_df[col] = encoder.fit_transform(user_input_df[col])
        
        # Make prediction
        prediction = model.predict(user_input_df)
        result = 'chronic kidney disease' if prediction[0] == 1 else 'no chronic kidney disease'
         
        
        # Generate PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Chronic Kidney Disease Prediction Report", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Username: {session['username']}", ln=True)
        pdf.cell(200, 10, txt=f"Email: {email}", ln=True)
        for col, val in user_input.items():
            pdf.cell(200, 10, txt=f"{col}: {val}", ln=True)
        pdf.cell(200, 10, txt=f"Prediction: {result}", ln=True)
        pdf.output("static/report.pdf")

        return render_template('result.html', username=session['username'], email=email, result=result, user_input=user_input)
    
    return render_template('predict.html', columns=[col for col in df.columns if col not in ['id', 'classification']])

@app.route('/download_report')
def download_report():
    return send_file('static/report.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)