import os
import json
import glob
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Utility: Safe JSON load ---
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Helpers for normalization ---
def normalize_str(s):
    if not s:
        return ""
    return str(s).strip().lower().replace(" ", "")


def normalize_phone(phone):
    if not phone:
        return ""
    return "".join(c for c in str(phone) if c.isdigit())[-10:]  # last 10 digits


# --- Contact metrics (improved) ---
def evaluate_contacts(pred, gold):
    tp, fp, fn = 0, 0, 0

    pred_c = pred.get("contacts", {})
    gold_c = gold.get("contacts", {})

    # Flatten nested location if needed
    if isinstance(pred_c.get("location"), dict):
        pred_c["address"] = pred_c["location"].get("raw", "")
    if "location" in pred_c:
        del pred_c["location"]

    # Convert list phone → string
    if isinstance(pred_c.get("phone"), list) and pred_c["phone"]:
        pred_c["phone"] = pred_c["phone"][0]

    fields = ["email", "phone", "address", "linkedin"]

    for f in fields:
        p = normalize_str(pred_c.get(f))
        g = normalize_str(gold_c.get(f))

        if f == "phone":
            p = normalize_phone(pred_c.get(f))
            g = normalize_phone(gold_c.get(f))

        if p and g:
            if p == g:
                tp += 1
            else:
                fp += 1
        elif p and not g:
            fp += 1
        elif g and not p:
            fn += 1

    return tp, fp, fn


# --- Section recall ---
def evaluate_sections(pred, gold):
    sections = ["education", "experience", "skills"]
    recall = {}
    for sec in sections:
        recall[sec] = 1 if sec in pred and pred[sec] else 0
    return recall


# --- Date accuracy (±1 month) ---
def within_one_month(pred_date, gold_date):
    try:
        p = datetime.strptime(pred_date, "%Y-%m")
        g = datetime.strptime(gold_date, "%Y-%m")
        return abs((p - g).days) <= 31
    except Exception:
        return False


def evaluate_dates(pred, gold):
    correct, total = 0, 0
    for p_exp, g_exp in zip(pred.get("experience", []), gold.get("experience", [])):
        if "start_date" in p_exp and "start_date" in g_exp:
            total += 1
            if within_one_month(p_exp["start_date"], g_exp["start_date"]):
                correct += 1
    return correct, total


# --- Company/role pairing ---
def evaluate_company_role(pred, gold):
    correct, total = 0, 0
    for p_exp, g_exp in zip(pred.get("experience", []), gold.get("experience", [])):
        total += 1
        if (
            normalize_str(p_exp.get("company")) == normalize_str(g_exp.get("company"))
            and normalize_str(p_exp.get("title")) == normalize_str(g_exp.get("title"))
        ):
            correct += 1
    return correct, total


# --- Main evaluator ---
def evaluate_all():
    gold_dir = os.path.join("gold_data", "labels")
    pred_dir = os.path.join("predictions")
    os.makedirs("evaluation", exist_ok=True)

    print(f" Evaluating predictions in '{pred_dir}' against gold labels in '{gold_dir}'...\n")

    rows = []
    for gold_path in glob.glob(os.path.join(gold_dir, "*.json")):
        fname = os.path.basename(gold_path)
        pred_path = os.path.join(pred_dir, fname)

        if not os.path.exists(pred_path):
            print(f"[WARN] Missing prediction for {fname}")
            continue

        gold, pred = load_json(gold_path), load_json(pred_path)

        # Contacts
        tp, fp, fn = evaluate_contacts(pred, gold)
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0

        # Sections
        section_scores = evaluate_sections(pred, gold)

        # Dates
        date_correct, date_total = evaluate_dates(pred, gold)
        date_acc = date_correct / date_total if date_total else 0

        # Company-role
        cr_correct, cr_total = evaluate_company_role(pred, gold)
        cr_acc = cr_correct / cr_total if cr_total else 0

        row = {
            "file": fname,
            "precision_contacts": precision,
            "recall_contacts": recall,
            "date_accuracy": date_acc,
            "company_role_accuracy": cr_acc,
            **section_scores
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("evaluation/report.csv", index=False)
    print(df)
    print("\nOverall averages:\n", df.mean(numeric_only=True))


if __name__ == "__main__":
    evaluate_all()
