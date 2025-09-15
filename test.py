#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 17:59:16 2025

@author: suresh
"""
import json
import csv
from tableauhyperapi import (
    HyperProcess, Connection, Telemetry,
    TableDefinition, SqlType, TableName,
    CreateMode, Inserter, NOT_NULLABLE, NULLABLE
)

# -----------------------------
# Helper: Map JSON types to Hyper SqlType
# -----------------------------
def map_sqltype(json_type: str) -> SqlType:
    json_type = json_type.lower()
    if json_type.startswith("decimal"):
        precision, scale = json_type.replace("decimal", "").strip("()").split(",")
        return SqlType.numeric(int(precision), int(scale))
    elif json_type == "integer":
        return SqlType.int()
    elif json_type == "string":
        return SqlType.text()
    elif json_type in ["float", "double"]:
        return SqlType.double()
    else:
        raise ValueError(f"Unsupported type: {json_type}")
    
def map_sqltype(json_type: str) -> SqlType:
    json_type = json_type.lower()
 
#  HyperException: This database does not support 128-bit numerics. 
#    if json_type.startswith("decimal"):
#        precision, scale = json_type.replace("decimal", "").strip("()").split(",")
#        return SqlType.numeric(int(precision), int(scale))
 
#Convert to string    
    if json_type.startswith("decimal"):
        precision, scale = json_type.replace("decimal", "").strip("()").split(",")
        if int(precision) > 18:
            return SqlType.text()   # fallback to text
        return SqlType.numeric(int(precision), int(scale))

# covert in to 18
#    if json_type.startswith("decimal"):
#        precision, scale = json_type.replace("decimal", "").strip("()").split(",")
#        precision, scale = int(precision), int(scale)
#        if precision > 18:
#            precision = 18  # cap at Hyper's max
#        return SqlType.numeric(precision, scale)
    elif json_type == "integer":
        return SqlType.int()
    elif json_type == "string":
        return SqlType.text()
    elif json_type in ["float", "double"]:
        return SqlType.double()
    else:
        raise ValueError(f"Unsupported type: {json_type}")


# -----------------------------
# Create Hyper with COPY
# -----------------------------
def create_merged_hyper(csv_files, json_schema_file, output_hyper="output.hyper"):
    # Load schema
    with open(json_schema_file, "r") as f:
        schema = json.load(f)
    fields = schema["fields"]

    table_name = TableName("Extract", "Extract")

    # Define table
    table_def = TableDefinition(table_name)
    for field in fields:
        sql_type = map_sqltype(field["type"])
        nullability = NULLABLE if field.get("nullable", True) else NOT_NULLABLE
        table_def.add_column(field["name"], sql_type, nullability)

    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(endpoint=hyper.endpoint,
                        database=output_hyper,
                        create_mode=CreateMode.CREATE_AND_REPLACE) as connection:

            connection.catalog.create_schema("Extract")
            connection.catalog.create_table(table_def)

            # COPY each CSV
            for csv_file in csv_files:
                print(f"📥 Loading {csv_file} ...")
                connection.execute_command(
                    command=f"""
                        COPY {table_name}
                        FROM {csv_file!r}
                        WITH
                            (format csv, delimiter ',', header false, null '', encoding 'utf-8')
                    """
                )

    print(f"✅ Hyper file created with merged data: {output_hyper}")
# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    csv_files = ["/Users/suresh/Downloads/table1.csv", "/Users/suresh/Downloads/table2.csv", "/Users/suresh/Downloads/table3.csv"]  # your CSVs
    json_schema_file = "/Users/suresh/Downloads/schema.json"
    create_merged_hyper(csv_files, json_schema_file, "/Users/suresh/Downloads/merged_output.hyper")
