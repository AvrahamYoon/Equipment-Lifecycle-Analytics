import os
import pandas as pd
 
INPUT_DIR = "input"
OUTPUT_DIR = "Output"
 
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
def clean_equipment_file(filepath):
    df = pd.read_csv(filepath)
 
    # only keep euqipment
    df = df[
        (df["EquipmentId"].notna()) &
        (df["Name"].notna()) &
        (~df["Name"].astype(str).str.contains(r"\(Repair\)|\(PM\)", na=False))
    ]
 
    # keep key columns
    keep_cols = [
        "EquipmentId",
        "Name",
        "Location",
        "EquipType",
        "Manufacturer",
        "SerialNumber",
        "PurchaseDate",
        "DepreciationYears",
        "Cost"
    ]
 
    df = df[[col for col in keep_cols if col in df.columns]]
 
    # clean EquipmentId
    df["EquipmentId"] = (
        df["EquipmentId"]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )
 
    # clean Cost
    if "Cost" in df.columns:
        df["Cost"] = (
            df["Cost"]
            .astype(str)
            .str.replace(r"[\$,]", "", regex=True)
        )
        df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce")
 
    # clean date
    if "PurchaseDate" in df.columns:
        df["PurchaseDate"] = pd.to_datetime(df["PurchaseDate"], errors="coerce")
 
    # deduplicate
    if "PurchaseDate" in df.columns:
        df = df.sort_values(by="PurchaseDate", ascending=False)
 
    df = df.drop_duplicates(subset="EquipmentId", keep="first")
 
    # calculate age
    if "PurchaseDate" in df.columns:
        today = pd.Timestamp.today()
        df["Age"] = (today - df["PurchaseDate"]).dt.days / 365
 
    return df
 
 
def main():
    all_data = []
 
    for file in os.listdir(INPUT_DIR):
        if file.endswith(".csv"):
            filepath = os.path.join(INPUT_DIR, file)
 
            print(f"Processing: {file}")
            cleaned_df = clean_equipment_file(filepath)
 
            # single file output
            output_file = os.path.join(
                OUTPUT_DIR,
                file.replace(".csv", "_cleaned.csv")
            )
            cleaned_df.to_csv(output_file, index=False)
 
            all_data.append(cleaned_df)
 
    # merge all files
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
 
        # rededuplicate
        final_df = final_df.sort_values(by="PurchaseDate", ascending=False)
        final_df = final_df.drop_duplicates(subset="EquipmentId", keep="first")
 
        final_output = os.path.join(OUTPUT_DIR, "all_equipment_summary.csv")
        final_df.to_csv(final_output, index=False)
 
        print("✅ All files processed. Summary file created.")
 
    else:
        print("⚠️ No CSV files found in input folder.")
 
 
if __name__ == "__main__":
    main()