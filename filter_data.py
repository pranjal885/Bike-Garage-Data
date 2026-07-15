import pandas as pd
import re
from openpyxl import Workbook

# ==========================================================
# FILE PATHS
# ==========================================================

INPUT_FILE = "maharashtra_bike_garages.csv"

OUTPUT_ALL = "bike_garages_clean.csv"

OUTPUT_CONTACT = "bike_garages_with_contact.csv"

OUTPUT_NO_CONTACT = "bike_garages_without_contact.csv"

OUTPUT_EXCEL = "bike_garages.xlsx"

print("=" * 60)
print("LOADING DATASET...")
print("=" * 60)

df = pd.read_csv(INPUT_FILE, dtype={"Contact": str})

print(f"Loaded {len(df)} records.")

# ==========================================================
# BASIC CLEANING
# ==========================================================

df = df.fillna("")

for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
    )

# ==========================================================
# PHONE CLEANING
# ==========================================================

def clean_phone(phone):

    if pd.isna(phone):
        return ""

    phone = str(phone).strip()

    # Remove trailing .0 added by pandas
    if phone.endswith(".0"):
        phone = phone[:-2]

    # Keep only digits
    phone = re.sub(r"\D", "", phone)

    # Remove +91
    if len(phone) == 12 and phone.startswith("91"):
        phone = phone[2:]

    # Remove leading 0
    if len(phone) == 11 and phone.startswith("0"):
        phone = phone[1:]

    # Accept only valid Indian mobile numbers
    if len(phone) == 10 and phone[0] in "6789":
        return phone

    return ""

df["Contact"] = df["Contact"].apply(clean_phone)

# ==========================================================
# REMOVE INVALID NAMES
# ==========================================================

INVALID_NAMES = {

    "",

    "unknown",

    "null",

    "none",

    "nan",

    "-",

    ".",

    "n/a"

}

before_invalid = len(df)

df = df[
    ~df["Name"]
        .str.lower()
        .isin(INVALID_NAMES)
]

print(
    f"Removed invalid names : "
    f"{before_invalid-len(df)}"
)

# ==========================================================
# REMOVE EMPTY MAP URL
# ==========================================================

before_url = len(df)

df = df[
    df["Google Maps URL"] != ""
]

print(
    f"Removed empty URLs : "
    f"{before_url-len(df)}"
)

# ==========================================================
# REMOVE EMPTY ADDRESS
# ==========================================================

before_address = len(df)

df = df[
    df["Address"] != ""
]

print(
    f"Removed empty addresses : "
    f"{before_address-len(df)}"
)
# ==========================================================
# REMOVE DUPLICATES
# ==========================================================

print("\nRemoving duplicates...")

original_records = len(df)

# -----------------------------
# Duplicate Google Maps URL
# -----------------------------

before = len(df)

df = df.drop_duplicates(
    subset=["Google Maps URL"]
)

url_duplicates = before - len(df)

# -----------------------------
# Duplicate Name + Address
# -----------------------------

before = len(df)

df = df.drop_duplicates(
    subset=["Name", "Address"]
)

name_address_duplicates = before - len(df)

# -----------------------------
# Duplicate Phone
# -----------------------------

phones = df["Contact"] != ""

with_phone = df[phones].copy()

without_phone = df[~phones].copy()

before = len(with_phone)

with_phone = with_phone.drop_duplicates(
    subset=["Contact"]
)

phone_duplicates = before - len(with_phone)

# -----------------------------
# Duplicate Website
# -----------------------------

websites = with_phone["Website"] != ""

website_data = with_phone[websites].copy()

no_website_data = with_phone[~websites].copy()

before = len(website_data)

website_data = website_data.drop_duplicates(
    subset=["Website"]
)

website_duplicates = before - len(website_data)

with_phone = pd.concat(
    [
        website_data,
        no_website_data
    ],
    ignore_index=True
)

# Merge back

df = pd.concat(
    [
        with_phone,
        without_phone
    ],
    ignore_index=True
)

total_duplicates = (
    url_duplicates
    + name_address_duplicates
    + phone_duplicates
    + website_duplicates
)

print(f"Duplicate URLs            : {url_duplicates}")
print(f"Duplicate Name+Address    : {name_address_duplicates}")
print(f"Duplicate Phone           : {phone_duplicates}")
print(f"Duplicate Website         : {website_duplicates}")
print(f"Total Removed             : {total_duplicates}")

# ==========================================================
# SORT DATA
# ==========================================================

print("\nSorting dataset...")

df = df.sort_values(
    by=[
        "Name",
        "Address"
    ]
)

# ==========================================================
# SPLIT CONTACT / NO CONTACT
# ==========================================================

with_contact = df[
    df["Contact"] != ""
].copy()

without_contact = df[
    df["Contact"] == ""
].copy()

# ==========================================================
# WEBSITE STATISTICS
# ==========================================================

website_available = (
    df["Website"] != ""
).sum()

website_missing = (
    df["Website"] == ""
).sum()

phone_available = len(with_contact)

phone_missing = len(without_contact)

print("\n========== CONTACT STATS ==========")

print(f"Phone Available : {phone_available}")

print(f"Phone Missing   : {phone_missing}")

print(f"Website Available : {website_available}")

print(f"Website Missing   : {website_missing}")

# ==========================================================
# CITY STATISTICS
# ==========================================================

print("\n========== CITY STATISTICS ==========")

cities = [
    "Mumbai",
    "Pune",
    "Thane",
    "Navi Mumbai",
    "Nagpur",
    "Nashik",
    "Kolhapur",
    "Aurangabad",
    "Solapur",
    "Jalgaon"
]

for city in cities:

    count = df["Address"].str.contains(
        city,
        case=False,
        na=False
    ).sum()

    print(f"{city:<18} {count}")
# ==========================================================
# SAVE CSV FILES
# ==========================================================

print("\nSaving CSV files...")

df.to_csv(
    OUTPUT_ALL,
    index=False,
    encoding="utf-8-sig"
)

with_contact.to_csv(
    OUTPUT_CONTACT,
    index=False,
    encoding="utf-8-sig"
)

without_contact.to_csv(
    OUTPUT_NO_CONTACT,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================================
# EXPORT TO EXCEL
# ==========================================================

print("Creating Excel workbook...")

with pd.ExcelWriter(
    OUTPUT_EXCEL,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        sheet_name="All Garages",
        index=False
    )

    with_contact.to_excel(
        writer,
        sheet_name="With Contact",
        index=False
    )

    without_contact.to_excel(
        writer,
        sheet_name="Without Contact",
        index=False
    )

# ==========================================================
# FINAL SUMMARY
# ==========================================================

print("\n" + "=" * 65)
print("DATA CLEANING COMPLETED")
print("=" * 65)

print(f"Original Records           : {original_records}")
print(f"Final Clean Records        : {len(df)}")
print(f"Total Duplicates Removed   : {total_duplicates}")

print()

print(f"With Contact               : {len(with_contact)}")
print(f"Without Contact            : {len(without_contact)}")

print()

print(f"Website Available          : {website_available}")
print(f"Website Missing            : {website_missing}")

print()

print("Generated Files")
print("-" * 65)

print(f"✓ {OUTPUT_ALL}")
print(f"✓ {OUTPUT_CONTACT}")
print(f"✓ {OUTPUT_NO_CONTACT}")
print(f"✓ {OUTPUT_EXCEL}")

print("=" * 65)
print("DONE")
print("=" * 65)