import pandas as pd
import re
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.tokenize import word_tokenize
import nltk
from tabulate import tabulate
from sklearn.model_selection import train_test_split
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

# import dataset dulu
path_dataset = "Sara.csv"
df_main = pd.read_csv(path_dataset, encoding='latin-1')

dictionary_path = "colloquial-indonesian-lexicon.csv"
df_dict = pd.read_csv(dictionary_path)

# drop kolom yg gak penting
df_main.columns = df_main.columns.str.strip()
df_main.drop(columns=['Username'], inplace=True)

# kalau ada yg kosong kasih string kosong
df_main['Text'] = df_main['Text'].fillna('')

df_dict.drop(columns=['In-dictionary', 'context', 'category1', 'category2', 'category3'], inplace=True)

# ngubah dictionary ke dalam format dictionary Python untuk mapping, kolom slang sbg key dan kolom formal sbg value
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

# DATA PREPROCESSING
# kalau 'Text' tidak ada di kolom dataset, raise error
if 'Text' not in df_main.columns:
    raise ValueError("Kolom 'Text' tidak ditemukan dalam dataset.")

stop_words = set(stopwords.words('indonesian'))  # stopwords untuk bahasa Indonesia
factory = StemmerFactory()
stemmer = factory.create_stemmer()

#fungsi pembersihan dan normalisasi teks (lowercase -> tokenisasi -> normalisasi kata singkatan/gaul -> stopwords -> penggabungan kata )
def clean_and_normalize_text(text):
    # tembersihkan teks dari karakter non-huruf dan mengubahnya menjadi huruf kecil
    cleaned_text = re.sub('[^a-zA-Z]', ' ', text).lower()
    #tokenisasi untuk memeriksa per kata
    tokenized_text = cleaned_text.split()
    #normalisasi kata-kata gaul
    normalized_words = [slang_dict.get(word, word) for word in tokenized_text]
     #hapus stopwords
    filtered_words = [word for word in normalized_words if word not in stop_words]
    # Menggabungkan kembali teks hasil pembersihan
    return ' '.join(filtered_words)

#apply fungsi secara bertahap
df_main['Cleaned Text'] = df_main['Text'].apply(lambda x: clean_and_normalize_text(x))
df_main['Keterangan'] = df_main['Label'].map({0: 'non-SARA', 1: 'SARA'})

def tokenize_text(text):
  tokenized_text = text.split()
  return tokenized_text

df_main['Tokens'] = df_main['Cleaned Text'].apply(lambda x: tokenize_text(x))

#fungsi stemming
def stem_and_remove_stopwords(token_list):
    processed_tokens = [stemmer.stem(token) for token in token_list if token not in stop_words]
    return " ".join(processed_tokens)

df_main['Normalized Text'] = df_main['Tokens'].apply(lambda x: stem_and_remove_stopwords(x))

# evaluasi hasil pembersihan dan normalisasi teks
#cek berapa datanya
print(f"Input data has {len(df_main)} rows and {len(df_main.columns)} columns")
print(f"Teks tidak mengandung SARA = {len(df_main[df_main['Label'] == 0])} rows")
print(f"Teks mengandung SARA = {len(df_main[df_main['Label'] == 1])} rows")
filtered_df = df_main[df_main['Normalized Text'].str.contains("²", case=False)]
print(filtered_df)

print(f"Number of null in label: {df_main['Label'].isnull().sum()}")
print(f"Number of null in text: {df_main['Text'].isnull().sum()}")#cek berapa datanya
print(f"Input data has {len(df_main)} rows and {len(df_main.columns)} columns")
print(f"Teks tidak mengandung SARA = {len(df_main[df_main['Label'] == 0])} rows")
print(f"Teks mengandung SARA = {len(df_main[df_main['Label'] == 1])} rows")
filtered_df = df_main[df_main['Normalized Text'].str.contains("²", case=False)]
print(filtered_df)

print(f"Number of null in label: {df_main['Label'].isnull().sum()}")
print(f"Number of null in text: {df_main['Text'].isnull().sum()}")

# FEATURE EXTRACTION
# pakai tf-idf buat ekstraksi fitur
#bikin model tf idf nya
tfidf_vectorizer = TfidfVectorizer(max_features=3000)

#rubah teks jadi vektor
X_tfidf = tfidf_vectorizer.fit_transform(df_main['Normalized Text'])
joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer.joblib')  # simpan model TF-IDF

X = X_tfidf
y = df_main['Label']

#splitting data nya 70 30 pake random state 42
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

#simpen ke joblib aja x y nya
joblib.dump(X_train, 'X_train.joblib')
joblib.dump(X_test, 'X_test.joblib')
joblib.dump(y_train, 'y_train.joblib')
joblib.dump(y_test, 'y_test.joblib')
