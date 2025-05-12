import joblib
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# load data hasil preprocessing.py
X_train = joblib.load('X_train.joblib') #ngeload data training yang sudah di preprocessing
X_test = joblib.load('X_test.joblib') #ngeload data testing yang sudah di preprocessing
y_train = joblib.load('y_train.joblib') #ngeload label training yang sudah di preprocessing
y_test = joblib.load('y_test.joblib') #ngeload label testing yang sudah di preprocessing

# hyperparameter tuning untuk model knn dengan grid search 
param_grid = {
    'n_neighbors': list(range(1, 30)), #cari range dari 1-30 
    'weights': ['uniform', 'distance'], #cari weight uniform dan distance
    'metric': ['euclidean', 'manhattan', 'minkowski'] #cari metric dengan jarak euclidean, manhattan, dan minkowski
}

# grid search untuk mencari hyperparameter terbaik dari parameter grid
knn = KNeighborsClassifier() #panggil model knn
grid_search = GridSearchCV(knn, param_grid, cv=5, scoring='accuracy', verbose=1, n_jobs=-1)
grid_search.fit(X_train, y_train) #cari grid model knn utk mencari hyperparameter terbaik

print("Best Parameters:", grid_search.best_params_)
print("Best Cross-Validation Accuracy:", grid_search.best_score_)

# train model knn terbaik
best_knn_model = grid_search.best_estimator_
best_knn_model.fit(X_train, y_train) #fitting/latih model knn terbaik dengan data training

y_pred = best_knn_model.predict(X_test) #prediksi data testing dgn model knn yg udh dilatih

# evaluasi model knn
accuracy = accuracy_score(y_test, y_pred) #akurasi dari perbandingan label asli dan label prediksi
print(f"Accuracy: {accuracy * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

#confusion matrix
cm = confusion_matrix(y_test, y_pred) 
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Non-SARA', 'SARA'])
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.show()

joblib.dump(best_knn_model, 'knn_best_model.joblib')
print("Best KNN model saved as 'knn_best_model.joblib'")