import os

import pandas as pd

# Compuclean exports: raw downloads → cleaned outputs (run from project root)
INPUT_DIR = os.path.join("data", "equipment", "raw")
OUTPUT_DIR = os.path.join("data", "equipment", "cleaned")


def clean_equipment_file(filepath):
    df = pd.read_csv(filepath)

    # only keep equipment rows
    df = df[
        (df["EquipmentId"].notna())
        & (df["Name"].notna())
        & (~df["Name"].astype(str).str.contains(r"\(Repair\)|\(PM\)", na=False))
    ]

    keep_cols = [
        "EquipmentId",
        "Name",
        "Location",
        "EquipType",
        "Manufacturer",
        "SerialNumber",
        "PurchaseDate",
        "DepreciationYears",
        "Cost",
    ]

    df = df[[col for col in keep_cols if col in df.columns]]

    df["EquipmentId"] = (
        df["EquipmentId"].astype(str).str.replace(" ", "", regex=False).str.strip()
    )

    if "Cost" in df.columns:
        df["Cost"] = (
            df["Cost"].astype(str).str.replace(r"[\$,]", "", regex=True)
        )
        df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce")

    if "PurchaseDate" in df.columns:
        df["PurchaseDate"] = pd.to_datetime(df["PurchaseDate"], errors="coerce")

    if "PurchaseDate" in df.columns:
        df = df.sort_values(by="PurchaseDate", ascending=False)

    df = df.drop_duplicates(subset="EquipmentId", keep="first")

    if "PurchaseDate" in df.columns:
        today = pd.Timestamp.today()
        df["Age"] = (today - df["PurchaseDate"]).dt.days / 365

    return df


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []

    for file in sorted(os.listdir(INPUT_DIR)):
        if not file.endswith(".csv"):
            continue
        filepath = os.path.join(INPUT_DIR, file)

        print(f"Processing: {file}")
        cleaned_df = clean_equipment_file(filepath)

        output_file = os.path.join(
            OUTPUT_DIR,
            file.replace(".csv", "_cleaned.csv"),
        )
        cleaned_df.to_csv(output_file, index=False)

        all_data.append(cleaned_df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)

        if "PurchaseDate" in final_df.columns:
            final_df = final_df.sort_values(by="PurchaseDate", ascending=False)
        final_df = final_df.drop_duplicates(subset="EquipmentId", keep="first")

        final_output = os.path.join(OUTPUT_DIR, "all_equipment_summary.csv")
        final_df.to_csv(final_output, index=False)

        print("✅ All files processed. Summary: data/equipment/cleaned/all_equipment_summary.csv")
    else:
        print(
            f"⚠️ No CSV files in {INPUT_DIR!r}.\n"
            "   Put Compuclean equipment exports (*.csv) in data/equipment/raw/ and run again."
        )


if __name__ == "__main__":
    main()
