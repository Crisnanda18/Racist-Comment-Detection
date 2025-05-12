from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Inisialisasi model SVM
svm = SVC(random_state=42)

# Parameter grid untuk tuning
param_grid = {
    'C': [0.1, 1, 10, 100],                  # Regularization parameter
    'kernel': ['linear', 'rbf', 'poly'], # Kernel types
    'gamma': ['scale', 'auto'],         # Kernel coefficient
    'degree': [2, 3, 4]                 # Degree for polynomial kernel
}

X_train = joblib.load('X_train.joblib')
X_test = joblib.load('X_test.joblib')
y_train = joblib.load('y_train.joblib')
y_test = joblib.load('y_test.joblib')

# GridSearchCV untuk mencari parameter terbaik
grid_search = GridSearchCV(estimator=svm, param_grid=param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=2)
grid_search.fit(X_train, y_train)

# Menampilkan parameter terbaik
print(f"Best Parameters: {grid_search.best_params_}")
print(f"Best Cross-Validation Accuracy: {grid_search.best_score_:.2%}")

# Menggunakan model terbaik dari GridSearchCV
best_svm = grid_search.best_estimator_
best_svm.fit(X_train, y_train)

# Evaluasi model pada data uji
y_pred = best_svm.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy on Test Data: {accuracy:.2%}\n")
print("Classification Report:")
print(classification_report(y_test, y_pred))