"""Các hàm lõi cho split, baseline, luật và đối chiếu liên kỹ thuật."""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from mlxtend.frequent_patterns import association_rules, fpgrowth
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


RANDOM_STATE = 42
TEST_SIZE = 0.20
LABELS = [1, 2, 3, 4]
SEVERE_LABELS = {3, 4}
MIN_ITEM_SUPPORT = 0.001
RULE_SUPPORT_GRID = (0.01, 0.03)
FINAL_MIN_SUPPORT = 0.01
FINAL_MIN_CONFIDENCE = 0.20
FINAL_MIN_LIFT = 1.20
MAX_ANTECEDENT_LENGTH = 3
TOP_RULES = 10
MIN_STRATUM_RULE_COUNT = 100
# Tránh lỗi dọn shared-memory của loky trên Python 3.9/Windows khi chạy notebook.
GRID_SEARCH_JOBS = 1

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "accidents_preprocessed.csv"
ARTIFACT_DIR = REPO_ROOT / "artifacts"
FIGURE_DIR = ARTIFACT_DIR / "figures"

CLASSIFICATION_FEATURES = [
    "Temperature(F)",
    "Humidity(%)",
    "Pressure(in)",
    "Visibility(mi)",
    "Wind_Speed(mph)",
    "Precipitation(in)",
    "Hour_of_Day",
    "Is_Weekend",
    "Amenity",
    "Bump",
    "Crossing",
    "Give_Way",
    "Junction",
    "No_Exit",
    "Railway",
    "Roundabout",
    "Station",
    "Stop",
    "Traffic_Calming",
    "Traffic_Signal",
    "Infra_Feature_Count",
]

INFRASTRUCTURE_ITEMS = [
    "Amenity",
    "Bump",
    "Crossing",
    "Give_Way",
    "Junction",
    "No_Exit",
    "Railway",
    "Roundabout",
    "Station",
    "Stop",
    "Traffic_Calming",
    "Traffic_Signal",
]

TRANSACTION_SOURCE_FEATURES = [
    "Start_Time",
    "Source",
    "State",
    "Temperature_Bin",
    "Weather_Condition",
    "Sunrise_Sunset",
]


def ensure_directories() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def load_source_data() -> pd.DataFrame:
    """Đọc nguồn chung, kiểm tra schema và chuẩn hóa view phân tích."""
    data = pd.read_csv(DATA_PATH)
    required = {
        "ID",
        "Severity",
        *CLASSIFICATION_FEATURES,
        *TRANSACTION_SOURCE_FEATURES,
    }
    missing_columns = sorted(required.difference(data.columns))
    if missing_columns:
        raise ValueError(f"Thiếu cột bắt buộc: {missing_columns}")
    if data["ID"].isna().any() or not data["ID"].is_unique:
        raise ValueError("ID phải đầy đủ và duy nhất cho từng vụ tai nạn.")
    if data["Severity"].isna().any():
        raise ValueError("Severity không được thiếu.")
    if not set(data["Severity"].unique()).issubset(set(LABELS)):
        raise ValueError("Severity chỉ được nhận các giá trị 1, 2, 3, 4.")

    # Snapshot Bài 1 đã làm mất một phần chuỗi thời gian khi parse định dạng
    # hỗn hợp. Không gán các dòng đó thành ngày thường; giữ missing rõ ràng.
    parsed_start = pd.to_datetime(data["Start_Time"], errors="coerce", format="mixed")
    data["Start_Time"] = parsed_start
    data["Hour_of_Day"] = parsed_start.dt.hour.astype("Float64")
    weekend = pd.Series(pd.NA, index=data.index, dtype="boolean")
    known_time = parsed_start.notna()
    weekend.loc[known_time] = parsed_start.loc[known_time].dt.weekday.ge(5)
    data["Is_Weekend"] = weekend.astype("Float64")
    data["Accident_Year"] = parsed_start.dt.year.astype("Int64")
    data["is_severe"] = data["Severity"].isin(SEVERE_LABELS).astype("int8")
    return data


def create_bias_audit(data: pd.DataFrame) -> pd.DataFrame:
    """Mô tả thay đổi nhãn theo nguồn, bang, năm và tình trạng thời gian."""
    ensure_directories()
    audit_frames = []
    audit_dimensions = {
        "Source": data["Source"].astype("string").fillna("Unknown"),
        "State": data["State"].astype("string").fillna("Unknown"),
        "Accident_Year": data["Accident_Year"].astype("string").fillna("Unknown"),
        "Time_Availability": pd.Series(
            np.where(data["Start_Time"].notna(), "Known", "Missing"),
            index=data.index,
        ),
    }
    for dimension, values in audit_dimensions.items():
        frame = pd.DataFrame({"stratum": values, "is_severe": data["is_severe"]})
        summary = (
            frame.groupby("stratum", dropna=False, observed=True)["is_severe"]
            .agg(n_events="size", n_severe="sum", severe_rate="mean")
            .reset_index()
        )
        summary.insert(0, "dimension", dimension)
        audit_frames.append(summary)
    audit = pd.concat(audit_frames, ignore_index=True)
    audit.to_csv(ARTIFACT_DIR / "data_bias_audit.csv", index=False)
    return audit


def create_common_split(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tạo split một lần theo ID, stratify theo bốn mức Severity."""
    ensure_directories()
    splitter = StratifiedShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    train_index, test_index = next(splitter.split(data, data["Severity"]))
    split = data[["ID", "Severity", "is_severe"]].copy()
    split["split"] = "train"
    split.loc[test_index, "split"] = "test"
    split.to_csv(ARTIFACT_DIR / "split_us_accidents.csv", index=False)

    distribution = (
        split.groupby(["split", "Severity"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=LABELS, fill_value=0)
    )
    distribution.columns = [f"Severity_{label}" for label in distribution.columns]
    distribution.insert(0, "n_events", distribution.sum(axis=1))
    distribution["severe_3_4"] = (
        split.groupby("split", observed=True)["is_severe"].sum().astype(int)
    )
    distribution["severe_rate"] = distribution["severe_3_4"] / distribution["n_events"]
    distribution = distribution.reset_index()
    distribution.to_csv(ARTIFACT_DIR / "split_distribution.csv", index=False)
    return split, distribution


def attach_split(data: pd.DataFrame, split: pd.DataFrame) -> pd.DataFrame:
    merged = data.merge(
        split[["ID", "split"]],
        on="ID",
        how="left",
        validate="one_to_one",
    )
    if merged["split"].isna().any():
        raise ValueError("Có sự kiện không được gán train/test.")
    return merged


def _classification_pipeline(model, scale: bool) -> Pipeline:
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scaler", StandardScaler()))
    preprocessor = ColumnTransformer(
        [("features", Pipeline(numeric_steps), CLASSIFICATION_FEATURES)],
        remainder="drop",
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def _multiclass_model_metrics(
    name: str,
    model,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    predictions = model.predict(x_test)
    report = classification_report(
        y_test,
        predictions,
        labels=LABELS,
        output_dict=True,
        zero_division=0,
    )
    result = {
        "model": name,
        "accuracy": accuracy_score(y_test, predictions),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "f1_macro": f1_score(y_test, predictions, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_test, predictions, average="weighted", zero_division=0),
    }
    for label in LABELS:
        result[f"precision_s{label}"] = report[str(label)]["precision"]
        result[f"recall_s{label}"] = report[str(label)]["recall"]
        result[f"f1_s{label}"] = report[str(label)]["f1-score"]
    return result


def _binary_model_metrics(
    name: str,
    model,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, list(model.classes_).index(1)]
    return {
        "model": name,
        "accuracy": accuracy_score(y_test, predictions),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "precision_severe": precision_score(y_test, predictions, zero_division=0),
        "recall_severe": recall_score(y_test, predictions, zero_division=0),
        "f1_severe": f1_score(y_test, predictions, zero_division=0),
        "f1_macro": f1_score(y_test, predictions, average="macro", zero_division=0),
        "average_precision": average_precision_score(y_test, probabilities),
        "roc_auc": roc_auc_score(y_test, probabilities),
    }


def run_baseline_classification(
    data_with_split: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    """Đánh giá nền đa lớp và chọn model nhị phân cho phần tổng hợp."""
    ensure_directories()
    train = data_with_split.loc[data_with_split["split"] == "train"].copy()
    test = data_with_split.loc[data_with_split["split"] == "test"].copy()
    x_train = train[CLASSIFICATION_FEATURES]
    x_test = test[CLASSIFICATION_FEATURES]
    y_train_multiclass = train["Severity"]
    y_test_multiclass = test["Severity"]
    y_train_binary = train["is_severe"]
    y_test_binary = test["is_severe"]

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    multiclass_logistic_search = GridSearchCV(
        _classification_pipeline(
            LogisticRegression(
                class_weight="balanced",
                max_iter=2500,
                random_state=RANDOM_STATE,
            ),
            scale=True,
        ),
        {"model__C": [0.1, 1.0, 10.0]},
        scoring="f1_macro",
        cv=cv,
        n_jobs=GRID_SEARCH_JOBS,
    )
    multiclass_tree_search = GridSearchCV(
        _classification_pipeline(
            DecisionTreeClassifier(
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            scale=False,
        ),
        {
            "model__max_depth": [4, 6, 8, 10, 12],
            "model__min_samples_leaf": [20, 50, 100],
        },
        scoring="f1_macro",
        cv=cv,
        n_jobs=GRID_SEARCH_JOBS,
    )
    multiclass_logistic_search.fit(x_train, y_train_multiclass)
    multiclass_tree_search.fit(x_train, y_train_multiclass)
    multiclass_dummy = _classification_pipeline(
        DummyClassifier(strategy="most_frequent"),
        scale=False,
    )
    multiclass_dummy.fit(x_train, y_train_multiclass)
    multiclass_candidates = {
        "Dummy - most frequent": multiclass_dummy,
        "Logistic Regression balanced": multiclass_logistic_search.best_estimator_,
        "Decision Tree balanced": multiclass_tree_search.best_estimator_,
    }
    multiclass_cv_scores = {
        "Logistic Regression balanced": float(multiclass_logistic_search.best_score_),
        "Decision Tree balanced": float(multiclass_tree_search.best_score_),
    }
    selected_multiclass_name = max(multiclass_cv_scores, key=multiclass_cv_scores.get)
    selected_multiclass_model = multiclass_candidates[selected_multiclass_name]
    multiclass_rows = []
    for name, model in multiclass_candidates.items():
        row = _multiclass_model_metrics(name, model, x_test, y_test_multiclass)
        row["best_cv_f1_macro"] = multiclass_cv_scores.get(name, np.nan)
        multiclass_rows.append(row)
    multiclass_metrics = pd.DataFrame(multiclass_rows).sort_values(
        "f1_macro",
        ascending=False,
    )
    multiclass_metrics.to_csv(
        ARTIFACT_DIR / "classification_metrics_multiclass.csv",
        index=False,
    )

    binary_logistic_search = GridSearchCV(
        _classification_pipeline(
            LogisticRegression(
                class_weight="balanced",
                max_iter=2500,
                random_state=RANDOM_STATE,
            ),
            scale=True,
        ),
        {"model__C": [0.1, 1.0, 10.0]},
        scoring="average_precision",
        cv=cv,
        n_jobs=GRID_SEARCH_JOBS,
    )
    binary_tree_search = GridSearchCV(
        _classification_pipeline(
            DecisionTreeClassifier(
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            scale=False,
        ),
        {
            "model__max_depth": [4, 6, 8, 10, 12],
            "model__min_samples_leaf": [20, 50, 100],
        },
        scoring="average_precision",
        cv=cv,
        n_jobs=GRID_SEARCH_JOBS,
    )
    binary_logistic_search.fit(x_train, y_train_binary)
    binary_tree_search.fit(x_train, y_train_binary)
    binary_dummy = _classification_pipeline(
        DummyClassifier(strategy="prior"),
        scale=False,
    )
    binary_dummy.fit(x_train, y_train_binary)
    binary_candidates = {
        "Dummy - prior": binary_dummy,
        "Logistic Regression balanced": binary_logistic_search.best_estimator_,
        "Decision Tree balanced": binary_tree_search.best_estimator_,
    }
    binary_cv_scores = {
        "Logistic Regression balanced": float(binary_logistic_search.best_score_),
        "Decision Tree balanced": float(binary_tree_search.best_score_),
    }
    selected_binary_name = max(binary_cv_scores, key=binary_cv_scores.get)
    selected_binary_model = binary_candidates[selected_binary_name]
    binary_rows = []
    for name, model in binary_candidates.items():
        row = _binary_model_metrics(name, model, x_test, y_test_binary)
        row["best_cv_average_precision"] = binary_cv_scores.get(name, np.nan)
        binary_rows.append(row)
    metrics = pd.DataFrame(binary_rows).sort_values("average_precision", ascending=False)

    output = test[
        ["ID", "Source", "State", "Accident_Year", "Severity", "is_severe"]
    ].copy()
    output = output.rename(columns={"Severity": "Severity_true"})
    for name, model in multiclass_candidates.items():
        slug = {
            "Dummy - most frequent": "dummy",
            "Logistic Regression balanced": "logistic",
            "Decision Tree balanced": "tree",
        }[name]
        output[f"Severity_pred_{slug}"] = model.predict(x_test)
    output["selected_multiclass_model"] = selected_multiclass_name
    output["Severity_pred"] = selected_multiclass_model.predict(x_test)

    for name, model in binary_candidates.items():
        slug = {
            "Dummy - prior": "dummy",
            "Logistic Regression balanced": "logistic",
            "Decision Tree balanced": "tree",
        }[name]
        output[f"is_severe_pred_{slug}"] = model.predict(x_test).astype("int8")

    calibrated_model = CalibratedClassifierCV(
        selected_binary_model,
        method="sigmoid",
        cv=5,
    )
    calibrated_model.fit(x_train, y_train_binary)
    probabilities = calibrated_model.predict_proba(x_test)
    severe_probability_index = list(calibrated_model.classes_).index(1)
    output["selected_model"] = selected_binary_name
    output["risk_severe"] = probabilities[:, severe_probability_index]
    output["is_pred_severe"] = selected_binary_model.predict(x_test).astype("int8")
    output["is_false_negative_severe"] = (
        (output["is_severe"] == 1) & (output["is_pred_severe"] == 0)
    ).astype("int8")
    output["is_false_positive_severe"] = (
        (output["is_severe"] == 0) & (output["is_pred_severe"] == 1)
    ).astype("int8")
    output.to_csv(ARTIFACT_DIR / "model_predictions_baseline.csv", index=False)

    brier = brier_score_loss(output["is_severe"], output["risk_severe"])
    metrics["brier_severe"] = np.nan
    metrics.loc[metrics["model"] == selected_binary_name, "brier_severe"] = brier
    metrics.to_csv(ARTIFACT_DIR / "classification_metrics.csv", index=False)

    observed_rate, predicted_rate = calibration_curve(
        output["is_severe"], output["risk_severe"], n_bins=10, strategy="quantile"
    )
    calibration = pd.DataFrame(
        {
            "mean_predicted_severe": predicted_rate,
            "observed_severe_rate": observed_rate,
        }
    )
    calibration.to_csv(ARTIFACT_DIR / "baseline_calibration.csv", index=False)
    plt.figure(figsize=(6.4, 5.2))
    plt.plot([0, 1], [0, 1], linestyle="--", color="#777777", label="Hiệu chỉnh hoàn hảo")
    plt.plot(
        predicted_rate,
        observed_rate,
        marker="o",
        color="#276f94",
        label=selected_binary_name,
    )
    plt.xlabel("Xác suất ảnh hưởng giao thông cao dự báo trung bình")
    plt.ylabel("Tỷ lệ Severity 3-4 quan sát")
    plt.title("Calibration cho nhãn Severity 3-4")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "calibration_baseline.png", dpi=180)
    plt.close()

    binary_prediction = output["is_pred_severe"]
    cm = confusion_matrix(y_test_binary, binary_prediction, labels=[0, 1])
    plt.figure(figsize=(6.4, 5.2))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Severity 1-2", "Severity 3-4"],
        yticklabels=["Severity 1-2", "Severity 3-4"],
    )
    plt.title(f"Ma trận nhầm lẫn nhị phân - {selected_binary_name}")
    plt.xlabel("Nhóm dự báo")
    plt.ylabel("Nhóm thực tế")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "confusion_matrix_baseline.png", dpi=180)
    plt.close()

    multiclass_prediction = output["Severity_pred"]
    multiclass_cm = confusion_matrix(
        y_test_multiclass,
        multiclass_prediction,
        labels=LABELS,
    )
    plt.figure(figsize=(6.4, 5.2))
    sns.heatmap(
        multiclass_cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=LABELS,
        yticklabels=LABELS,
    )
    plt.title(f"Ma trận nhầm lẫn đa lớp - {selected_multiclass_name}")
    plt.xlabel("Severity dự báo")
    plt.ylabel("Severity thực tế")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "confusion_matrix_multiclass.png", dpi=180)
    plt.close()

    search_summary = {
        "analysis_target": "is_severe = 1 khi Severity thuộc 3-4",
        "selected_model": selected_binary_name,
        "selection_rule": "Average precision CV cao nhất trên train",
        "binary_logistic_best_params": binary_logistic_search.best_params_,
        "binary_logistic_best_cv_average_precision": float(
            binary_logistic_search.best_score_
        ),
        "binary_tree_best_params": binary_tree_search.best_params_,
        "binary_tree_best_cv_average_precision": float(binary_tree_search.best_score_),
        "multiclass_selected_model": selected_multiclass_name,
        "multiclass_selection_rule": "F1-macro CV cao nhất trên train",
        "multiclass_logistic_best_params": multiclass_logistic_search.best_params_,
        "multiclass_logistic_best_cv_f1_macro": float(
            multiclass_logistic_search.best_score_
        ),
        "multiclass_tree_best_params": multiclass_tree_search.best_params_,
        "multiclass_tree_best_cv_f1_macro": float(multiclass_tree_search.best_score_),
        "excluded_early_prediction_feature": "Distance(mi)",
        "probability_calibration": (
            "CalibratedClassifierCV, sigmoid, cv=5 trên train; "
            "nhãn cứng lấy từ model nhị phân được chọn"
        ),
        "brier_severe_test": float(brier),
    }
    (ARTIFACT_DIR / "baseline_search_summary.json").write_text(
        json.dumps(search_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    models = {
        "binary": binary_candidates,
        "multiclass": multiclass_candidates,
        "calibrated_binary": calibrated_model,
    }
    return metrics, output, models, search_summary


def _hour_to_bucket(value) -> str:
    if pd.isna(value):
        return "Unknown"
    hour = int(value)
    if 5 <= hour <= 10:
        return "Sang"
    if 11 <= hour <= 16:
        return "Trua_Chieu"
    if 17 <= hour <= 20:
        return "Toi"
    return "Dem"


def _weather_to_group(value) -> str:
    if pd.isna(value):
        return "Unknown"
    weather = str(value).lower()
    if any(token in weather for token in ("snow", "sleet", "ice", "hail")):
        return "Tuyet_Bang"
    if any(token in weather for token in ("rain", "drizzle", "shower")):
        return "Mua"
    if any(token in weather for token in ("fog", "haze", "mist", "smoke")):
        return "Suong_Mu"
    if any(token in weather for token in ("thunder", "storm")):
        return "Bao"
    if any(token in weather for token in ("cloud", "overcast")):
        return "Nhieu_May"
    if any(token in weather for token in ("clear", "fair")):
        return "Quang_Dang"
    return "Khac"


def _weekend_to_group(value) -> str:
    if pd.isna(value):
        return "Unknown"
    return "CuoiTuan" if bool(value) else "NgayThuong"


def build_transactions(data: pd.DataFrame) -> pd.DataFrame:
    """Tạo transaction theo đúng quy ước Bài 1 và giữ ID ở index."""
    transaction = data.set_index("ID")
    infra = transaction[INFRASTRUCTURE_ITEMS].fillna(False).astype(bool)
    time_items = pd.get_dummies(
        transaction["Hour_of_Day"].map(_hour_to_bucket),
        prefix="GioTrongNgay",
        dtype=bool,
    )
    day_items = pd.get_dummies(
        transaction["Is_Weekend"].map(_weekend_to_group),
        prefix="LoaiNgay",
        dtype=bool,
    )
    temperature_items = pd.get_dummies(
        transaction["Temperature_Bin"].fillna("Unknown"),
        prefix="NhietDo",
        dtype=bool,
    )
    weather_items = pd.get_dummies(
        transaction["Weather_Condition"].map(_weather_to_group),
        prefix="ThoiTiet",
        dtype=bool,
    )
    light_items = pd.get_dummies(
        transaction["Sunrise_Sunset"].fillna("Unknown"),
        prefix="AnhSang",
        dtype=bool,
    )
    severity_items = pd.DataFrame(
        {
            "MucDo_Nang": transaction["Severity"].isin(SEVERE_LABELS),
            "MucDo_Nhe": ~transaction["Severity"].isin(SEVERE_LABELS),
        },
        index=transaction.index,
    )
    return pd.concat(
        [infra, time_items, day_items, temperature_items, weather_items, light_items, severity_items],
        axis=1,
    ).astype(bool)


def _serialize_itemset(values: Iterable[str]) -> str:
    return json.dumps(sorted(values), ensure_ascii=False)


def _remove_redundant_rules(rules: pd.DataFrame) -> pd.DataFrame:
    """Loại luật dài không cải thiện confidence và lift so với luật con."""
    keep = []
    records = list(rules.sort_values(["antecedent_len", "lift"], ascending=[True, False]).iterrows())
    for index, candidate in records:
        redundant = False
        for kept_index in keep:
            shorter = rules.loc[kept_index]
            if (
                shorter["antecedents"].issubset(candidate["antecedents"])
                and shorter["confidence"] >= candidate["confidence"]
                and shorter["lift"] >= candidate["lift"]
            ):
                redundant = True
                break
        if not redundant:
            keep.append(index)
    return rules.loc[keep].copy()


def mine_training_rules(
    data_with_split: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Mine rules trên train; test chưa được dùng trong lựa chọn luật."""
    ensure_directories()
    train = data_with_split.loc[data_with_split["split"] == "train"].copy()
    test = data_with_split.loc[data_with_split["split"] == "test"].copy()
    train_transactions = build_transactions(train)
    test_transactions = build_transactions(test)

    support = train_transactions.mean()
    selected_columns = support[support >= MIN_ITEM_SUPPORT].index.tolist()
    for outcome in ("MucDo_Nang", "MucDo_Nhe"):
        if outcome not in selected_columns:
            selected_columns.append(outcome)
    train_transactions = train_transactions.reindex(columns=selected_columns, fill_value=False)
    test_transactions = test_transactions.reindex(columns=selected_columns, fill_value=False)

    threshold_rows = []
    frequent_by_support = {}
    for min_support in RULE_SUPPORT_GRID:
        start = time.perf_counter()
        frequent = fpgrowth(
            train_transactions,
            min_support=min_support,
            use_colnames=True,
            max_len=4,
        )
        elapsed = time.perf_counter() - start
        frequent_by_support[min_support] = frequent
        generated = association_rules(
            frequent,
            metric="confidence",
            min_threshold=FINAL_MIN_CONFIDENCE,
        )
        severe_count = generated[generated["consequents"] == frozenset({"MucDo_Nang"})].shape[0]
        threshold_rows.append(
            {
                "min_support": min_support,
                "frequent_itemsets": len(frequent),
                "all_rules": len(generated),
                "rules_to_severe": severe_count,
                "runtime_seconds": elapsed,
            }
        )
    threshold_summary = pd.DataFrame(threshold_rows)
    threshold_summary.to_csv(ARTIFACT_DIR / "rule_threshold_comparison.csv", index=False)

    rules = association_rules(
        frequent_by_support[FINAL_MIN_SUPPORT],
        metric="confidence",
        min_threshold=FINAL_MIN_CONFIDENCE,
    )
    rules["antecedent_len"] = rules["antecedents"].map(len)
    rules = rules[
        (rules["consequents"] == frozenset({"MucDo_Nang"}))
        & (rules["lift"] >= FINAL_MIN_LIFT)
        & (rules["antecedent_len"] <= MAX_ANTECEDENT_LENGTH)
        & ~rules["antecedents"].map(lambda values: any("Unknown" in item for item in values))
        & ~rules["antecedents"].map(lambda values: bool({"MucDo_Nang", "MucDo_Nhe"}.intersection(values)))
    ].copy()
    rules = _remove_redundant_rules(rules)
    rules = rules.sort_values(["lift", "support", "confidence"], ascending=False).head(TOP_RULES)

    export = rules[
        [
            "antecedents",
            "consequents",
            "antecedent support",
            "consequent support",
            "support",
            "confidence",
            "lift",
            "leverage",
            "conviction",
            "antecedent_len",
        ]
    ].copy()
    export.insert(0, "rule_id", [f"R{index:02d}" for index in range(1, len(export) + 1)])
    export["antecedents"] = export["antecedents"].map(_serialize_itemset)
    export["consequents"] = export["consequents"].map(_serialize_itemset)
    export = export.rename(
        columns={
            "antecedent support": "antecedent_support_train",
            "consequent support": "consequent_support_train",
            "support": "support_train",
            "confidence": "confidence_train",
            "lift": "lift_train",
            "leverage": "leverage_train",
            "conviction": "conviction_train",
        }
    )
    export.to_csv(ARTIFACT_DIR / "rules_train.csv", index=False)
    return export, threshold_summary, train_transactions, test_transactions


def _bootstrap_rate_difference(
    group_values: np.ndarray,
    comparison_values: np.ndarray,
    iterations: int = 1000,
) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(RANDOM_STATE)
    group_rates = np.empty(iterations)
    differences = np.empty(iterations)
    for index in range(iterations):
        group_sample = rng.choice(group_values, size=len(group_values), replace=True)
        comparison_sample = rng.choice(comparison_values, size=len(comparison_values), replace=True)
        group_rates[index] = group_sample.mean()
        differences[index] = group_sample.mean() - comparison_sample.mean()
    group_low, group_high = np.quantile(group_rates, [0.025, 0.975])
    diff_low, diff_high = np.quantile(differences, [0.025, 0.975])
    return float(group_low), float(group_high), float(diff_low), float(diff_high)


def _build_stratified_rule_audit(
    rules_train: pd.DataFrame,
    test_evaluation: pd.DataFrame,
) -> pd.DataFrame:
    """Kiểm tra hướng chênh lệch theo nguồn, bang và năm."""
    rows = []
    for rule in rules_train.itertuples(index=False):
        antecedents = json.loads(rule.antecedents)
        rule_mask = test_evaluation[antecedents].all(axis=1)
        for dimension in ("Source", "State", "Accident_Year"):
            strata = test_evaluation[dimension].astype("string").fillna("Unknown")
            for stratum in sorted(strata.unique()):
                stratum_mask = strata.eq(stratum)
                group = test_evaluation.loc[stratum_mask & rule_mask]
                comparison = test_evaluation.loc[stratum_mask & ~rule_mask]
                if group.empty or comparison.empty:
                    continue
                observed_difference = (
                    group["is_severe"].mean() - comparison["is_severe"].mean()
                )
                model_difference = (
                    group["risk_severe"].mean() - comparison["risk_severe"].mean()
                )
                rows.append(
                    {
                        "rule_id": rule.rule_id,
                        "dimension": dimension,
                        "stratum": str(stratum),
                        "n_stratum": int(stratum_mask.sum()),
                        "n_rule_group": len(group),
                        "n_comparison_group": len(comparison),
                        "severe_rate_rule": float(group["is_severe"].mean()),
                        "severe_rate_comparison": float(
                            comparison["is_severe"].mean()
                        ),
                        "observed_rate_difference": float(observed_difference),
                        "model_risk_rule": float(group["risk_severe"].mean()),
                        "model_risk_comparison": float(
                            comparison["risk_severe"].mean()
                        ),
                        "model_risk_difference": float(model_difference),
                        "eligible_main_stratum": bool(
                            dimension in {"Source", "State"}
                            and len(group) >= MIN_STRATUM_RULE_COUNT
                            and len(comparison) >= MIN_STRATUM_RULE_COUNT
                        ),
                    }
                )
    audit = pd.DataFrame(rows)
    audit.to_csv(ARTIFACT_DIR / "rules_stratified_robustness.csv", index=False)
    return audit


def integrate_rules_and_model(
    rules_train: pd.DataFrame,
    test_transactions: pd.DataFrame,
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Đối chiếu rules-model và kiểm tra độ bền theo các tầng dữ liệu."""
    test_evaluation = predictions.set_index("ID").join(
        test_transactions,
        how="inner",
        validate="one_to_one",
    )
    base_rate = test_evaluation["is_severe"].mean()
    stratified_audit = _build_stratified_rule_audit(rules_train, test_evaluation)
    rows = []

    for rule in rules_train.itertuples(index=False):
        antecedents = json.loads(rule.antecedents)
        mask = test_evaluation[antecedents].all(axis=1)
        group = test_evaluation.loc[mask]
        comparison = test_evaluation.loc[~mask]
        if group.empty or comparison.empty:
            continue

        severe_count = int(group["is_severe"].sum())
        severe_rate = float(group["is_severe"].mean())
        lift_test = severe_rate / base_rate if base_rate else np.nan
        comparison_rate = float(comparison["is_severe"].mean())
        model_risk = float(group["risk_severe"].mean())
        comparison_model_risk = float(comparison["risk_severe"].mean())
        predicted_severe_rate = float(group["is_pred_severe"].mean())
        recall_in_rule = (
            float(group.loc[group["is_severe"] == 1, "is_pred_severe"].mean())
            if severe_count
            else np.nan
        )
        ci_low, ci_high, diff_low, diff_high = _bootstrap_rate_difference(
            group["is_severe"].to_numpy(),
            comparison["is_severe"].to_numpy(),
        )

        _, _, model_diff_low, model_diff_high = _bootstrap_rate_difference(
            group["risk_severe"].to_numpy(),
            comparison["risk_severe"].to_numpy(),
        )

        rule_strata = stratified_audit.loc[
            (stratified_audit["rule_id"] == rule.rule_id)
            & stratified_audit["eligible_main_stratum"]
        ]
        n_eligible_strata = len(rule_strata)
        n_positive_strata = int(rule_strata["observed_rate_difference"].gt(0).sum())
        n_model_positive_strata = int(
            rule_strata["model_risk_difference"].gt(0).sum()
        )
        strata_consistent = bool(
            n_eligible_strata >= 2
            and n_positive_strata == n_eligible_strata
            and n_model_positive_strata == n_eligible_strata
        )

        stable_rule = lift_test >= 1.10 and diff_low > 0
        model_aligned = model_diff_low > 0
        if stable_rule and model_aligned and strata_consistent:
            relation = "Đồng hướng và ổn định ở các tầng chính"
        elif stable_rule and model_aligned:
            relation = "Đồng hướng trên mẫu gộp, không ổn định theo tầng"
        elif stable_rule:
            relation = "Rule đồng hướng, model không đồng hướng"
        else:
            relation = "Chưa bền trên test"

        rows.append(
            {
                "rule_id": rule.rule_id,
                "antecedents": rule.antecedents,
                "n_test_covered": len(group),
                "coverage_test": len(group) / len(test_evaluation),
                "n_severe_test": severe_count,
                "severe_rate_test": severe_rate,
                "severe_rate_comparison": comparison_rate,
                "severe_rate_ci95_low": ci_low,
                "severe_rate_ci95_high": ci_high,
                "rate_difference_ci95_low": diff_low,
                "rate_difference_ci95_high": diff_high,
                "confidence_test": severe_rate,
                "lift_test": lift_test,
                "risk_severe_model_mean": model_risk,
                "risk_severe_model_comparison": comparison_model_risk,
                "model_risk_difference": model_risk - comparison_model_risk,
                "model_risk_difference_ci95_low": model_diff_low,
                "model_risk_difference_ci95_high": model_diff_high,
                "predicted_severe_rate": predicted_severe_rate,
                "recall_severe_in_rule": recall_in_rule,
                "false_negative_severe_in_rule": int(group["is_false_negative_severe"].sum()),
                "n_eligible_main_strata": n_eligible_strata,
                "n_positive_main_strata": n_positive_strata,
                "n_model_positive_main_strata": n_model_positive_strata,
                "strata_consistent": strata_consistent,
                "relation": relation,
            }
        )

    integrated = pd.DataFrame(rows)
    integrated = integrated.merge(
        rules_train[["rule_id", "support_train", "confidence_train", "lift_train"]],
        on="rule_id",
        how="left",
        validate="one_to_one",
    )
    output_path = ARTIFACT_DIR / "rules_model_test.csv"
    try:
        integrated.to_csv(output_path, index=False)
    except PermissionError as error:
        # Excel trên Windows khóa file đang mở. Chỉ tái sử dụng artifact nếu
        # kết quả mới hoàn toàn tương đương; tuyệt đối không bỏ qua bản khác.
        if not output_path.exists():
            raise
        existing = pd.read_csv(output_path)
        try:
            pd.testing.assert_frame_equal(
                existing,
                integrated,
                check_dtype=False,
                check_exact=False,
                rtol=1e-9,
                atol=1e-12,
            )
        except AssertionError as mismatch:
            raise PermissionError(
                f"{output_path.name} đang bị khóa và kết quả mới khác artifact hiện có. "
                "Hãy đóng file trong Excel rồi chạy lại cell."
            ) from mismatch
        print(f"Lưu ý: {output_path.name} đang mở; kết quả mới trùng artifact hiện có nên không ghi đè.")

    if not integrated.empty:
        plot_data = integrated.sort_values("lift_test", ascending=True)
        plt.figure(figsize=(8.2, max(4.2, len(plot_data) * 0.48)))
        plt.barh(plot_data["rule_id"], plot_data["lift_test"], color="#276f94")
        plt.axvline(1.0, color="#a33d36", linestyle="--", linewidth=1.2)
        plt.xlabel("Lift trên tập test")
        plt.ylabel("Luật")
        plt.title("Lift của luật đối với mức ảnh hưởng giao thông cao")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / "rule_lift_test.png", dpi=180)
        plt.close()
    return integrated, stratified_audit


def write_environment_lock() -> Path:
    import imblearn
    import matplotlib
    import mlxtend
    import sklearn
    import seaborn

    ensure_directories()
    lines = [
        f"python=={platform.python_version()}",
        f"pandas=={pd.__version__}",
        f"numpy=={np.__version__}",
        f"scikit-learn=={sklearn.__version__}",
        f"matplotlib=={matplotlib.__version__}",
        f"seaborn=={seaborn.__version__}",
        f"mlxtend=={mlxtend.__version__}",
        f"imbalanced-learn=={imblearn.__version__}",
    ]
    path = ARTIFACT_DIR / "environment.lock.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_analysis_pipeline() -> dict:
    """Chạy trọn phần D.2-D.6 và trả lại các bảng để notebook hiển thị."""
    data = load_source_data()
    bias_audit = create_bias_audit(data)
    split, split_distribution = create_common_split(data)
    data_with_split = attach_split(data, split)
    metrics, predictions, models, search_summary = run_baseline_classification(data_with_split)
    rules, threshold_summary, train_transactions, test_transactions = mine_training_rules(data_with_split)
    integrated, stratified_audit = integrate_rules_and_model(
        rules,
        test_transactions,
        predictions,
    )
    environment_path = write_environment_lock()
    return {
        "data": data,
        "bias_audit": bias_audit,
        "split": split,
        "split_distribution": split_distribution,
        "data_with_split": data_with_split,
        "classification_metrics": metrics,
        "predictions": predictions,
        "models": models,
        "search_summary": search_summary,
        "rules_train": rules,
        "rule_threshold_summary": threshold_summary,
        "train_transactions": train_transactions,
        "test_transactions": test_transactions,
        "rules_model_test": integrated,
        "rules_stratified_robustness": stratified_audit,
        "environment_path": environment_path,
    }
