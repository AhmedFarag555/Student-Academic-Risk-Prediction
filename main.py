from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import numpy as np
import joblib

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# تحميل الموديل و scaler و feature_columns
model = joblib.load("model/rf_student_model.pkl")   # RandomForest Model
scaler = joblib.load("model/scaler.pkl")
feature_columns = joblib.load("model/feature_columns.pkl")

# تحميل القيم الفعلية للأعمدة النصية (dropdown)
dropdown_values = joblib.load("model/dropdown_values.pkl")

# تحميل حدود الأعمدة الرقمية
numeric_limits = joblib.load("model/numeric_limits.pkl")

# الأعمدة الأصلية + G1,G2,G3
original_columns = [
    "school", "sex", "age", "address", "famsize", "Pstatus",
    "Medu", "Fedu", "Mjob", "Fjob", "reason", "guardian",
    "traveltime", "studytime", "failures", "schoolsup", "famsup",
    "paid", "activities", "nursery", "higher", "internet",
    "romantic", "famrel", "freetime", "goout", "Dalc",
    "Walc", "health", "absences", "subject",
    "G1", "G2", "G3"
]

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("form.html", {
        "request": request,
        "columns": original_columns,
        "prediction": None,
        "dropdown_values": dropdown_values,
        "numeric_limits": numeric_limits
    })

@app.post("/", response_class=HTMLResponse)
async def predict(request: Request):
    form = await request.form()
    print("📌 Step 1: Form collected")

    # جمع البيانات من الفورم
    data = {col: form[col] for col in original_columns}
    print("📌 Step 2: Data dict", data)

    df_new = pd.DataFrame([data])
    print("📌 Step 3: DataFrame created")

    # تحويل الأعمدة الرقمية إلى float/int
    for col in df_new.columns:
        try:
            df_new[col] = pd.to_numeric(df_new[col])
        except:
            pass
    print("📌 Step 4: Numeric conversion done")

    # One-Hot Encoding
    df_encoded = pd.get_dummies(df_new)
    df_encoded = df_encoded.reindex(columns=feature_columns, fill_value=0)
    print("📌 Step 5: Encoding done", df_encoded.shape)

    # Scaling
    df_scaled = scaler.transform(df_encoded)
    print("📌 Step 6: Scaling done")

    # Prediction
    y_pred = model.predict(df_scaled)
    print("📌 Step 7: Prediction done", y_pred)

    # Mapping classes
    classes = ["Low Risk", "Medium Risk", "High Risk"]
    if isinstance(y_pred[0], (int, np.integer)):
        risk_category = classes[y_pred[0]]
    else:
        risk_category = str(y_pred[0])

    print("📌 Step 8: Risk Category:", risk_category)

    # إعادة عرض الصفحة مع النتيجة
    return templates.TemplateResponse("form.html", {
        "request": request,
        "columns": original_columns,
        "prediction": risk_category,
        "dropdown_values": dropdown_values,
        "numeric_limits": numeric_limits
    })
