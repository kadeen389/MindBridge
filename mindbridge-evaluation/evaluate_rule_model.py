import matplotlib
matplotlib.use("Agg")

from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

from model import classify_risk

test_cases = [
    {"text": "I feel okay today", "expected": "low"},
    {"text": "I am doing better now", "expected": "low"},
    {"text": "I feel fine", "expected": "low"},
    {"text": "I feel stressed with university", "expected": "medium"},
    {"text": "I am overwhelmed and anxious", "expected": "medium"},
    {"text": "I feel hopeless and exhausted", "expected": "medium"},
    {"text": "I can't cope anymore", "expected": "medium"},
    {"text": "I feel lonely and empty", "expected": "medium"},
    {"text": "I want to die", "expected": "high"},
    {"text": "I want to kill myself", "expected": "high"},
    {"text": "There is no point in living", "expected": "high"},
    {"text": "I want to end my life", "expected": "high"},
    {"text": "I am sucidal", "expected": "high"},   # intentional misspelling
    {"text": "I feel like hurting myself", "expected": "high"},
]

y_true = []
y_pred = []

print("\nRule-based classifier results:\n")

for case in test_cases:
    predicted, confidence, reasons = classify_risk(case["text"])
    y_true.append(case["expected"])
    y_pred.append(predicted)

    print(f'TEXT: {case["text"]}')
    print(f'EXPECTED: {case["expected"]}')
    print(f'PREDICTED: {predicted}')
    print(f'CONFIDENCE: {confidence}')
    print(f'REASONS: {reasons}')
    print("-" * 50)

print("\nClassification Report:\n")
print(classification_report(y_true, y_pred, labels=["low", "medium", "high"]))

cm = confusion_matrix(y_true, y_pred, labels=["low", "medium", "high"])
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["low", "medium", "high"])
disp.plot()

plt.title("Confusion Matrix - Rule-Based Risk Classifier")
plt.savefig("rule_model_confusion_matrix.png", dpi=300, bbox_inches="tight")

print("\nSaved confusion matrix as rule_model_confusion_matrix.png")