import joblib  # Atau import pickle jika Anda menggunakan pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import pandas as pd
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.tokenize import word_tokenize
import nltk

loaded_model = joblib.load('logreg.joblib')
tfidf_vectorizer = joblib.load('tfidf_vectorizer.joblib')
dictionary_path = "colloquial-indonesian-lexicon.csv"
df_dict = pd.read_csv(dictionary_path)

def preprocess_text(text):
    # 1. Case Folding
    text = text.lower()

    # 2. Cleaning (Remove punctuation, numbers, etc.)
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # 3. Normalisasi (mengganti slang)
    slang_dict = pd.Series(df_dict['formal'].values, index=df_dict['slang']).to_dict()
    slang_tambahan ={
        'knp' : 'kenapa',
        'lu' : 'kamu',
        'lu??':'kamu',
        'lo': 'kamu',
        'kayak':'seperti',
        'sdm' : 'sumber daya manusia',
        'javva' : 'jawa',
        'cino' : 'cina',
        'jawir': 'jawa'
    }
    slang_dict.update(slang_tambahan)
    text = " ".join([slang_dict.get(word, word) for word in text.split()])

    # 4. Tokenization (split)
    tokens = text.split()  # Ganti word_tokenize dengan split()

    # 5. Stop Word Removal
    stop_words = set(stopwords.words('indonesian'))
    tokens = [word for word in tokens if word not in stop_words]

    # 6. Stemming
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    # Gabungkan token kembali menjadi string
    return " ".join(tokens)

# Loop utama untuk menerima input dan melakukan prediksi
while True:
    text_input = input("Masukkan teks (atau ketik 'exit' untuk keluar): ")
    if text_input.lower() == "exit":
        break

    # Preprocessing teks input
    processed_text = preprocess_text(text_input)

    # Cek apakah tfidf_vectorizer siap digunakan
    print("Transforming text:", processed_text)

    # Vectorization
    try:
        text_vector = tfidf_vectorizer.transform([processed_text])  # Transformasi teks menggunakan tfidf_vectorizer
        print("Shape of text_vector:", text_vector.shape)  # Mengecek hasil vektorisasi
    except Exception as e:
        print("Terjadi kesalahan saat transformasi:", e)
        continue

    # Prediksi
    try:
        prediction = loaded_model.predict(text_vector)[0]
        if prediction == 0:
            print("Teks terdeteksi sebagai non-SARA")
        else:
            print("Teks terdeteksi sebagai SARA")
    except Exception as e:
        print("Prediksi gagal:", e)

print("Program selesai.")