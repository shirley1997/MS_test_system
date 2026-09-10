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




# import the results.csv file and obtain results inside
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



# Count the cells of one option of one variable, for example B2 = "B2a".
# Gives back four numbers: how many cells, and how many of each result.
def count_one_variable_option(valid_rows, column, variable_option):

    number_of_cells = 0
    number_malicious = 0
    number_private = 0
    number_resolution_error = 0

    for row in valid_rows:
        if row[column] == variable_option:
            number_of_cells = number_of_cells + 1

            if row[column_result] == "malicious_resolved":
                number_malicious = number_malicious + 1
            elif row[column_result] == "private_resolved":
                number_private = number_private + 1
            elif row[column_result] == "resolution_error":
                number_resolution_error = number_resolution_error + 1

    return number_of_cells, number_malicious, number_private, number_resolution_error


# The per-variable table: print the table, contains each variable options and their malicious_resolved percentages
#  and store it to step6_variable_table.csv.
def variable_table(valid_rows):

    table_rows = []

    for variable_name, column, variable_options in variables:

        total_malicious = 0

        for variable_option in variable_options:
            valid_cells_involve_this_option, malicious, private, error = count_one_variable_option(valid_rows, column, variable_option)
            malicious_rate = 100 * malicious / valid_cells_involve_this_option   # how many is the percentage of malicious cases in cells involve this variable option
            total_malicious = total_malicious + malicious

            print(variable_name, variable_option, " valid_cells_involve_this_option =", valid_cells_involve_this_option, " malicious resolved cells =", malicious,
                  " private resolved cells =", private, " resolution error cells =", error, " malicious_rate =", round(malicious_rate, 1), "%")

            table_rows.append([variable_name, variable_option, valid_cells_involve_this_option, malicious, private, error, round(malicious_rate, 1)])
    print("valid cells with malicious_resolved result: ", total_malicious)
   

    output_csv_file = script_folder / "step6_variable_table.csv"
    file = open(output_csv_file, "w", encoding="utf-8", newline="")
    writer = csv.writer(file)
    writer.writerow(["variable", "variable_option", "valid_cells_involve_this_option", "malicious resolved", "private resolved",
                     "resolution error", "malicious_resolved_rate_percentage"])
    for table_row in table_rows:
        writer.writerow(table_row)
    file.close()

    print("write output in:", output_csv_file)


# Compare cells involve A1a (public repository searched first in a nexus group repo) 
# and cells involve A1b (private repo searched first in nexus group repo).
# Every A1a cell is compared with the A1b cell that has exactly the same
# ecosystem, B1, B2 and C1 
# only one cell has A1a, one cell has A1b
# (here can print all results at once, instead using excel to compare each pair of cells manually )
def compare_A1a_A1b(valid_rows, results):

    number_compared = 0
    number_different = 0

# only search for valid rows / valid cells!!
    for row in valid_rows:
        if row[column_A] == "A1a":

            key_A1b = (row[column_ecosystem], "A1b", row[column_B1],
                       row[column_B2], row[column_C1])
            result_A1b = results[key_A1b]

            number_compared = number_compared + 1

        # if these two cells have different results, count plus 1
        # show different result and cell_id
            if row[column_result] != result_A1b:
                number_different = number_different + 1
                print("   different classification result:", row[column_cell_id],
                      row[column_result], " but A1b is", result_A1b)
     

    print("A1a / A1b valid cells are compared ", number_compared, " times")
    print("A1a / A1b cells have difference result: ", number_different)
    print("in each compared A1a /A1b cell pair, these two cells only have different options of A, other variable options are the same as each other")


# The per-variable table showed: no B2a valid cell has result "malicious_resolved".
# So version pinning seems to be necessary. Question: is it also enough to defense dependencies?
# In other words, are ALL not pinned cells (which have B2b / B2c) always have malicious_resolved?
# do these non-pinned cells always enable dependency confusion attack?
def check_not_pinned_cells(valid_rows):

    number_cell_not_pinned = 0
    number_malicious = 0
    number_private = 0
    number_error = 0

    cells_not_malicious = []

 # check cells which don't have B2a (but has B2b or B2c)
    for row in valid_rows:
        if row[column_B2] != "B2a":
            number_cell_not_pinned = number_cell_not_pinned + 1

            if row[column_result] == "malicious_resolved":
                number_malicious = number_malicious + 1
            else:
                cells_not_malicious.append(row)

                if row[column_result] == "private_resolved":
                    number_private = number_private + 1
                elif row[column_result] == "resolution_error":
                    number_error = number_error + 1

    print("number of not pinned valid cells (have B2b or B2c):", number_cell_not_pinned)
    print("Number of not pinned valid cells with result malicious_resolved:", number_malicious)
    print("Number of cells which don't have result malicious_resolved result:", len(cells_not_malicious),
          "\nin these", len(cells_not_malicious), "cells, ", number_private, "has result private_resolved. " ,
          number_error, "cells has result resolution_error" )

    return cells_not_malicious


# after running the function, check_not_pinned_cells(valid_rows)
# we found out not all not-pinned valid cells have malicious_resolved result
# 35 not-pinned valid cells have other results (private resolvd / resolution error)
# Question: what do these cells have in common?
# idea: build per-variable table among these cells too

# count_one_variable_option gives back four numbers; here only the first one
# (how many cells) is interesting.
def group_cells_by_variable(cells):

    for variable_name, column, variable_options in variables:

        for variable_option in variable_options:
            number_of_cells, malicious, private, error = count_one_variable_option(
                cells, column, variable_option)
            print("  ", variable_name, variable_option, ":", number_of_cells)

        print()



# Count the cells per A / B1 combination.
# "counts" is a dictionary: the key is one (A, B1) combination,
# the value is how many cells have it. Same idea as the results dictionary
# in read_results, only that here we count instead of storing a result.
def group_cells_by_A_and_B1(cells):

    counts = {}

    for row in cells:
        key = (row[column_A], row[column_B1])

        if key in counts:
            counts[key] = counts[key] + 1
        else:
            counts[key] = 1

    for key in sorted(counts):
        print("   A =", key[0], " B1 =", key[1], " cells:", counts[key])


# Check the candidate condition in the other direction:
# among ALL not pinned cells with this A and B1 combination,
# is there any cell that is malicious_resolved after all?
def check_combination(valid_rows, A_option, B1_option):

    number_of_cells = 0
    number_malicious = 0

    for row in valid_rows:
        if (row[column_B2] != "B2a"
                and row[column_A] == A_option
                and row[column_B1] == B1_option):

            number_of_cells = number_of_cells + 1

            if row[column_result] == "malicious_resolved":
                number_malicious = number_malicious + 1
                print("   still malicious:", row[column_cell_id])

    print("A =", A_option, " B1 =", B1_option,
          " not pinned cells:", number_of_cells,
          " in these cells, ", number_malicious, "has result malicious resolved")

# after running the previous checks, look at the leftover cells one by one.
def print_cells_of_B1_option(cells, B1_option):

    for row in cells:
        if row[column_B1] == B1_option:
            print("   ", row[column_cell_id], row[column_result])



# The rule, written as code.
# the function returns true if the rule says: this cell should be malicious_resolved.
def rule_about_malicious(row):

    # condition 1: a pinned version was never compromised
    if row[column_B2] == "B2a":
        return False

    # exception 2: pip B1d x C1b never reaches the operation under test,
    # because the C1b setup phase cannot obtain version 1.0.0 (harness, not PyPI)
    if (row[column_ecosystem] == "python"
            and row[column_B1] == "B1d"
            and row[column_C1] == "C1b"):
        return False

    # exception 1: in Maven A3 x B1a the repository id is not "central",
    # so the real Maven Central from the super POM leaks in and the resolver
    # can reach a public source after all
    if (row[column_ecosystem] == "java"
            and row[column_A] == "A3"
            and row[column_B1] == "B1a"):
        return True

    # condition 2: one single private registry, no public source reachable
    if row[column_B1] == "B1a" and (row[column_A] == "A2" or row[column_A] == "A3"):
        return False

    return True


# Test the rule against every valid cell (360 cells) and count how often it is wrong.
def test_rule(valid_rows):

    number_tested = 0
    number_wrong = 0
    wrong_rows = []

    for row in valid_rows:
        number_tested = number_tested + 1

        rule_result = rule_about_malicious(row)
        real_result = (row[column_result] == "malicious_resolved")

        if rule_result != real_result:
            number_wrong = number_wrong + 1
            wrong_rows.append(row)
            print("   rule is wrong for", row[column_cell_id],
                  " real result:", row[column_result],
                  " rule says malicious:", rule_result)

    print("cells tested:", number_tested)
    print("cells where the rule is wrong:", number_wrong)

    csv_file = script_folder / "step7_rule_misclassifications.csv"
    file = open(csv_file, "w", encoding="utf-8", newline="")
    writer = csv.writer(file)
    writer.writerow(["cell_id", "classification", "rule_about_malicious"])
    for row in wrong_rows:
        writer.writerow([row[column_cell_id], row[column_result],
                         rule_about_malicious(row)])
    file.close()

    print("write output in:", csv_file)


# -------------------------------------------- main () ---------------------------------
def main():
    #if len(sys.argv) > 1:
        #csv_file = Path(sys.argv[1])
    #else:
    csv_file = result_csv_file

    if csv_file.exists() == False:
        print("results.csv not found:", csv_file)
        return

    all_rows, results = read_results(csv_file)
    valid_rows = extract_valid_rows(all_rows)

    print("rows in results.csv: ", len(all_rows))
    print("valid (executed) cells: ", len(valid_rows))

    #variable_table(valid_rows)
    #compare_A1a_A1b(valid_rows, results)
    #check_not_pinned_cells(valid_rows)
    cells_not_malicious = check_not_pinned_cells(valid_rows)
    group_cells_by_variable(cells_not_malicious)
    group_cells_by_A_and_B1(cells_not_malicious)
    check_combination(valid_rows, "A2", "B1a")
    check_combination(valid_rows, "A3", "B1a")
    print_cells_of_B1_option(cells_not_malicious, "B1d")
    #rule_about_malicious(row)
    test_rule(valid_rows)




main()