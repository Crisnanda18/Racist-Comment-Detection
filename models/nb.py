from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import joblib
import matplotlib.pyplot as plt

param_grid = {
    'alpha': [0.1, 0.5, 1.0, 5.0, 10.0], #cari alpha dgn 0.1, 0.5, 1.0, 5.0, 10.0 untuk mencegah 0
}

X_train = joblib.load('X_train.joblib') #load data training dari hasil preprocessing
X_test = joblib.load('X_test.joblib') #load data testing dari hasil preprocessing
y_train = joblib.load('y_train.joblib') #load label training dari hasil preprocessing
y_test = joblib.load('y_test.joblib') #load label testing dari hasil preprocessing

nb_model = MultinomialNB() #panggil model naive bayes

grid_search = GridSearchCV(nb_model, param_grid, cv=5, scoring='accuracy', verbose=1, n_jobs=-1)
grid_search.fit(X_train, y_train)

print("Best Parameters:", grid_search.best_params_)
print("Best Cross-Validation Accuracy:", grid_search.best_score_)

best_nb_model = grid_search.best_estimator_
best_nb_model.fit(X_train, y_train)

y_pred = best_nb_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

#confusion matrix
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Non-SARA', 'SARA'])
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.show()