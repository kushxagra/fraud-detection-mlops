import pandas as pd
import requests
import time

API_URL = "http://localhost:8000/predict"  # Replace with your FastAPI endpoint URL

df=pd.read_csv("creditcard.csv")
sample = df.sample(n=100, random_state=1)

success = 0
failed = 0

for _,row in sample.iterrows():
    payload = {
        "Time": float(row["Time"]),
        "Amount": float(row["Amount"]),
    }
    for i in range(1, 29):
        payload[f"V{i}"] = float(row[f"V{i}"])

    response = requests.post(API_URL, json = payload)

    if response.status_code == 200:
        success += 1
    else:
        failed += 1
        print(f"Failed: {response.status_code} - {response.text}")

    time.sleep(0.02)

print(f"Done. {success} succeeded, {failed} failed.")
 