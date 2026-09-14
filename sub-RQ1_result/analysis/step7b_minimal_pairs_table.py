# build a minimal-pairs table to observe which variables flip the result
# for example: two cells with almost the same configuration combination, only ONE variable option is different 
# e.g. one cell has C1a, one cell has C1b. and compare these two cells becuase they have different results
# e.g. one cell has "private_resolved", one cell has "malicious_resolved"
# obvserve the pairs of these cell can observe which variable has isolated capability to flip the result
# the per-variable table shows some variable with average percentage, but in that table, the variable interact with each other
# so no effect of isolated cell can be observed. Therefore the minimal flip pair table is build through this script


import csv
import sys
from pathlib import Path



# The folder where this script file is.
# We build the path to results.csv from here, so the script works no matter
# from which folder you start it.
script_folder = Path(__file__).resolve().parent
result_csv_file = script_folder.parent / "0809" / "results.csv"

# column names
column_ecosystem = "ecosystem"
column_A = "A - private registry configuration"
column_B1 = "B1 - package manager configuration"
column_B2 = "B2 - version specifier"
column_C1 = "C - pipeline operation type"
column_result = "classification"


# test variable options
A_options = ["A1a", "A1b", "A2", "A3"]
B1_options = ["B1a", "B1b", "B1c", "B1d"]
B2_options = ["B2a", "B2b", "B2c"]
C1_options = ["C1a", "C1b", "C1c"]

# test variables
variables = [
    ("A",  column_A,  A_options),
    ("B1", column_B1, B1_options),
    ("B2", column_B2, B2_options),
    ("C1", column_C1, C1_options),
]

column_cell_id = "cell_id"

column_pk1_version = "pk1_version"
column_pk1_url = "pk1_url"
column_pk2_version = "pk2_version"



# import the results.csv file and obtain classification results inside
def read_results(csv_file):

    all_rows = []
    results = {}

    file = open(csv_file, encoding="utf-8", newline="")
    reader = csv.DictReader(file)
    for row in reader:
        all_rows.append(row)
        key = (row[column_ecosystem], row[column_A], row[column_B1],
               row[column_B2], row[column_C1])
        results[key] = row[column_result]
    file.close()

    return all_rows, results



# Keep only the cells that are really executed. (valid cells)
# The 72 invalid cells should not be counted anywhere. (they are not executed)
def extract_valid_rows(all_rows):

    valid_rows = []

    for row in all_rows:
        if row[column_result] != "invalid_configuration":
            valid_rows.append(row)

    return valid_rows


# only the valid cells are analyzed!!! 
# so here are only 3 categories
# a valid cell can not become a invalid cell, and vice versa
# make the result shorter as one letter (e.g. "M" means "malicious_resolved"), 
# so a pair of results can be written as "MP", "ME", "EP"
def get_letter(result):
    if result == "malicious_resolved":
        return "M"
    elif result == "private_resolved":
        return "P"
    else:
        return "E"


# "MP" and "PM" are the same result flip (a pair of cell don't have direction)
def flip_kind(result_1, result_2):
    letters = get_letter(result_1) + get_letter(result_2)
    if letters == "MP" or letters == "PM":
        return "MP"
    elif letters == "ME" or letters == "EM":
        return "EM"
    else:
        return "EP"


# The variables, with their position inside the key (ecosystem, A, B1, B2, C1).
# Position 0 is the ecosystem, and A is in 1st position, B1 at 2. position, B2 at 3, C1 at 4.
variables_with_position = [
    ("A",  1, A_options),
    ("B1", 2, B1_options),
    ("B2", 3, B2_options),
    ("C1", 4, C1_options),
]

# The key of the partner cell: the same as "key", but with ONE variable changed
# A key looks like (ecosystem, A, B1, B2, C1).
def make_partner_key(key, variable_name, new_option):

    ecosystem, A, B1, B2, C1 = key

    if variable_name == "A":
        return (ecosystem, new_option, B1, B2, C1)
    elif variable_name == "B1":
        return (ecosystem, A, new_option, B2, C1)
    elif variable_name == "B2":
        return (ecosystem, A, B1, new_option, C1)
    else:
        return (ecosystem, A, B1, B2, new_option)



# Count the minimal pairs of one variable (e.g. B1) inside one ecosystem.
# return 4 numbers: how many pairs exist and how many are specifically MP / EM / EP flips.
def count_pairs_of_one_variable(valid_rows, results, ecosystem, variable_name, column, options):


#initial value
    number_of_pairs = 0
    flips_MP = 0
    flips_EM = 0
    flips_EP = 0

    for row in valid_rows:
        if row[column_ecosystem] != ecosystem:
            continue

        my_option = row[column]
        my_result = row[column_result]
        key = (row[column_ecosystem], row[column_A], row[column_B1], row[column_B2], row[column_C1])

        for other_option in options:

            # count every pair only once: only from the cell whose option comes
            # e.g. A1a-A2 is counted, A2-A1a is skipped, because it is already counted once
            if my_option >= other_option:
                continue

            partner_key = make_partner_key(key, variable_name, other_option)

            if partner_key not in results or results[partner_key] == "invalid_configuration":
                continue       # the partner is an invalid cell, so there is no pair

            number_of_pairs = number_of_pairs + 1
            partner_result = results[partner_key]

            if my_result == partner_result:
                continue       # same result, no flip

            kind = flip_kind(my_result, partner_result)
            if kind == "MP":
                flips_MP = flips_MP + 1
            elif kind == "EM":
                flips_EM = flips_EM + 1
            else:
                flips_EP = flips_EP + 1

    return number_of_pairs, flips_MP, flips_EM, flips_EP

def main():
    csv_file = result_csv_file

    if csv_file.exists() == False:
        print("results.csv not found:", csv_file)
        return

    all_rows, results = read_results(csv_file)
    valid_rows = extract_valid_rows(all_rows)

    print("rows in results.csv: ", len(all_rows))
    print("valid (executed) cells: ", len(valid_rows))
    print()

    table_rows = []

    for ecosystem in ["nodejs", "python", "java"]:
        print(ecosystem)

        for variable_name, column, options in variables:
            pairs, MP, EM, EP = count_pairs_of_one_variable(
                valid_rows, results, ecosystem, variable_name, column, options)

            print("   ", variable_name, " pairs:", pairs,
                " MP:", MP, " EM:", EM, " EP:", EP)
            table_rows.append([ecosystem, variable_name, pairs, MP, EM, EP])

    print()

    output_csv_file = script_folder / "step7b_minimal_pairs_table.csv"
    file = open(output_csv_file, "w", encoding="utf-8", newline="")
    writer = csv.writer(file)
    writer.writerow(["ecosystem", "variable", "number_of_pairs",
                     "flips_malicious_private", "flips_malicious_error", "flips_private_error"])
    for table_row in table_rows:
        writer.writerow(table_row)
    file.close()

    print("write output in:", output_csv_file)


main()
