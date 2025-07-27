import pandas as pd
import numpy as np
import os

directory = "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards/"
product_data_file = "ccrz__E_Product__c-7_22_2025.csv"
order_data_file = "ccrz__E_Order__c-7_22_2025.csv"
invoice_data_file = "ccrz__E_Invoice__c-7_23_2025 (2).csv"
materials_data_file = "Materials__c-7_22_2025.csv"
duet_invoice_data_file = "duet_invoice_cleaned.csv"

product_df = pd.read_csv(os.path.join(directory, product_data_file))
order_df = pd.read_csv(os.path.join(directory, order_data_file))
invoice_df = pd.read_csv(os.path.join(directory, invoice_data_file))
materials_df = pd.read_csv(os.path.join(directory, materials_data_file))
duet_invoice_df = pd.read_csv(os.path.join(directory, duet_invoice_data_file))

print(len(product_df.columns), "product")
print(len(order_df.columns), "order")
print(len(invoice_df.columns), "invoice")
print(len(materials_df.columns), "materials")
print(len(duet_invoice_df.columns), "DUET invoice")

print(product_df.shape, "product")
print(order_df.shape, "order")
print(invoice_df.shape, "invoice")
print(materials_df.shape, "materials")
print(duet_invoice_df.shape, "DUET invoice")

print(list(product_df.columns), "product")
print(list(order_df.columns), "order")
print(list(invoice_df.columns), "invoice")
print(list(materials_df.columns), "materials")
print(list(duet_invoice_df.columns), "DUET invoice")
print("-..-..-..-..-..-..-..-..-..-..-..-..-..-..-..-..-..-..-..")
list_df = [product_df, order_df, invoice_df, materials_df, duet_invoice_df]
for df in list_df:
    if '_' in df.columns:
        df.drop(columns=['_'], inplace=True)

all_cols = {
    'product': set(product_df.columns),
    'order': set(order_df.columns),
    'invoice': set(invoice_df.columns),
    'materials': set(materials_df.columns),
    'duet': set(duet_invoice_df.columns),
}

# ids_product = set(product_df['Id'])
# ids_order = set(order_df['Id'])
# ids_invoice = set(invoice_df['Id'])
# ids_materials = set(materials_df['Id'])
# ids_duet_invoice = set(duet_invoice_df['Id'])
#
# # Find common IDs across all 4 tables
# common_ids = ids_product & ids_order & ids_invoice & ids_materials & ids_duet_invoice
# print(f"Common IDs: {common_ids}")

for a in all_cols:
    for b in all_cols:
        if a != b:
            print(f"Columns in {a} but not in {b}:", all_cols[a] - all_cols[b])
            print("-------------************-------------************-------------************-------------************-------------************-------------************")
            print("\n")

category_summary = product_df.groupby('Category__c')['Id'].count()
print(category_summary)
ship_summary = order_df['ccrz__ShipMethod__c'].value_counts()
print(ship_summary)
filtered = product_df[product_df['Packaging_Type__c'] == 'Drum']
print(filtered.head())

print(list(product_df.columns), "product")
print(list(order_df.columns), "order")
print(list(invoice_df.columns), "invoice")
print(list(materials_df.columns), "materials")
print(list(duet_invoice_df.columns), "DUET invoice")

product_sample = product_df.sample(15, random_state=40)
order_sample = order_df.sample(15, random_state=40)
invoice_sample = invoice_df.sample(15, random_state=40)
materials_sample = materials_df.sample(15, random_state=40)
duet_invoice_sample = duet_invoice_df.sample(15, random_state=40)

product_sample.to_csv(os.path.join(directory, "product_sample.csv"), index=False)
order_sample.to_csv(os.path.join(directory, "order_sample.csv"), index=False)
invoice_sample.to_csv(os.path.join(directory, "invoice_sample.csv"), index=False)
materials_sample.to_csv(os.path.join(directory, "materials_sample.csv"), index=False)
duet_invoice_sample.to_csv(os.path.join(directory, "duet_invoice_sample.csv"), index=False)

print("Sample files saved to:", directory)