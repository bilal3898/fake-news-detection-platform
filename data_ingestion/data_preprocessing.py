# data_ingestion/data_preprocessing.py
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from ml_core.prediction_pipeline.preprocessor import text_preprocessor

# Paths
RAW_TRUE = "dataset/raw/kaggle_true.csv"
RAW_FAKE = "dataset/raw/kaggle_fake.csv"
RAW_LIAR_TRAIN = "dataset/raw/liar/train.tsv"
RAW_LIAR_TEST = "dataset/raw/liar/test.tsv"
RAW_LIAR_VALID = "dataset/raw/liar/valid.tsv"

PROCESSED_DIR = "dataset/processed/"

def load_kaggle():
    true_df = pd.read_csv(RAW_TRUE)
    fake_df = pd.read_csv(RAW_FAKE)

    true_df["label"] = "REAL"
    fake_df["label"] = "FAKE"

    combined = pd.concat([true_df, fake_df], ignore_index=True)
    # Kaggle dataset usually has 'title' + 'text'
    combined["text"] = (combined["title"].fillna("") + " " + combined["text"].fillna("")).str.strip()
    return combined[["text", "label"]]

def load_liar():
    # Liar dataset format: label, statement, subject, speaker ...
    train_df = pd.read_csv(RAW_LIAR_TRAIN, sep="\t", header=None)
    test_df = pd.read_csv(RAW_LIAR_TEST, sep="\t", header=None)
    val_df = pd.read_csv(RAW_LIAR_VALID, sep="\t", header=None)

    liar = pd.concat([train_df, test_df, val_df], ignore_index=True)
    
    # LIAR dataset columns: 
    # 0: ID, 1: Label, 2: Statement, 3: Subject, 4: Speaker, 5: Job, 6: State, 7: Party, etc.
    liar = liar[[1, 2]]  # Use label (col 1) and statement (col 2)
    liar.columns = ["label", "text"]

    # Normalize liar labels
    fake_labels = {"false", "pants-fire", "barely-true"}
    real_labels = {"true", "mostly-true", "half-true"}
    liar["label"] = liar["label"].apply(lambda x: "FAKE" if x in fake_labels else "REAL")

    return liar

def preprocess_and_save():
    # Create processed directory if it doesn't exist
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    kaggle_df = load_kaggle()
    liar_df = load_liar()

    full_data = pd.concat([kaggle_df, liar_df], ignore_index=True)

    # Clean text using the simple preprocessor function
    full_data["clean_text"] = full_data["text"].apply(
        lambda x: text_preprocessor(str(x))
    )

    # Save one combined file
    full_data.to_csv(PROCESSED_DIR + "cleaned_news_data.csv", index=False)

    # Train-test-val split
    train, test = train_test_split(full_data, test_size=0.2, random_state=42, stratify=full_data["label"])
    val, test = train_test_split(test, test_size=0.5, random_state=42, stratify=test["label"])

    train.to_csv(PROCESSED_DIR + "train.csv", index=False)
    test.to_csv(PROCESSED_DIR + "test.csv", index=False)
    val.to_csv(PROCESSED_DIR + "val.csv", index=False)

    print("✅ Preprocessing complete. Files saved in dataset/processed/")

if __name__ == "__main__":
    preprocess_and_save()