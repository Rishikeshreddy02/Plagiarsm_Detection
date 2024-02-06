from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# MongoDB Configuration
mongodb_url = "mongodb+srv://rishikeshreddy:loki1234@cluster0.w1uhnmx.mongodb.net/"
client = MongoClient(mongodb_url)
db = client['plagarism_checker']
collection = db['documents']

# Configuring upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def vectorize(Text):
    return TfidfVectorizer().fit_transform(Text).toarray()

def similarity(doc1, doc2):
    return cosine_similarity([doc1, doc2])

def read_documents_from_mongodb():
    documents = list(collection.find())
    return [doc["content"] for doc in documents]

def check_plagiarism(doc1, doc2):
    vectors = vectorize([doc1, doc2])
    sim_score = similarity(vectors[0], vectors[1])[0][1]
    return round(sim_score, 2)

@app.route('/')
def home():
    documents = collection.find()
    return render_template('home.html', documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as file_content:
            content = file_content.read()

        document = {
            'filename': filename,
            'path': os.path.join(app.config['UPLOAD_FOLDER'], filename),
            'content': content
        }

        collection.insert_one(document)

        return redirect(url_for('home'))

@app.route('/check_plagiarism')
def check_plagiarism_route():
    # Assuming there are two documents in the collection
    documents = list(collection.find(limit=2))
    
    if len(documents) == 2:
        doc1_content = documents[0]["content"]
        doc2_content = documents[1]["content"]

        similarity_score = check_plagiarism(doc1_content, doc2_content)

        return f"Similarity Score for these two documents: {similarity_score}"
    else:
        return "Please upload two documents before checking plagiarism."


if __name__ == '__main__':
    app.run(debug=True, port=5000)
