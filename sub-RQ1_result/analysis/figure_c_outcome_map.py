# Figure C: outcome map of the whole sub-RQ1 experiment matrix.
# how to run: python figure_c_outcome_map.py (use the results.csv from 08.09)
# output: figure_c_outcome_map.pdf / figure_c_outcome_map.png  (for overleaf/slide)
#
# The figure is built with imshow(), following the official matplotlib example
# "Annotated heatmap":
# https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
# imshow() puts cell [i][j] automatically at position (j, i), so this script
# does not need to calculate any coordinates itself.


import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")    # only save files, not open a window
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle


# The folder where this script file is.
# We build the path to results.csv from here, so the script works no matter
# from which folder you start it.
script_folder = Path(__file__).resolve().parent
default_csv_file = script_folder.parent / "0809" / "results.csv"

# column names
column_ecosystem = "ecosystem"
column_A = "A - private registry configuration"
column_B1 = "B1 - package manager configuration"
column_B2 = "B2 - version specifier"
column_C1 = "C - pipeline operation type"
column_result = "classification"

# test variable values
A_values = ["A1a", "A1b", "A2", "A3"]
B1_values = ["B1a", "B1b", "B1c", "B1d"]
B2_values = ["B2a", "B2b", "B2c"]
C1_values = ["C1a", "C1b", "C1c"]

# The 3 block: (name used in results.csv, title shown in the figure)
block = [("nodejs", "npm"), ("python", "Pip"), ("java", "Maven")]

# color definition
color_background = "#fcfcfb"    # background of the whole figure
color_text = "#0b0b0b"      # normal text
color_text_light = "#52514e"    # small text
color_border = "#e1e0d9"        # thin border of the hatched squares

color_malicious = "#d03b3b"
color_private = "#29bf4c"
color_error = "#E7A713FF"
color_invalid = "#d0cabe"       # invalid cells are grey

# Every result gets a number, because imshow() needs numbers, not text.
# The number is the position of the color in the color list below.
code_malicious = 0
code_private = 1
code_error = 2
code_invalid = 3

# The color list. imshow() uses it to translate the numbers back into colors.
color_map = ListedColormap([color_malicious, color_private,
                            color_error, color_invalid])



# number for each result value (imshow needs numbers)
def get_code(result):

    if result == "malicious_resolved":
        return code_malicious
    elif result == "private_resolved":
        return code_private
    elif result == "resolution_error":
        return code_error
    else:
        return code_invalid

# fill color for each result value (only used for the legend)
def get_color(result):

    if result == "malicious_resolved":
        return color_malicious
    elif result == "private_resolved":
        return color_private
    elif result == "resolution_error":
        return color_error
    else:
        return color_invalid

# abbreviation to stand the classification results, written inside each cell
def get_letter(result):

    if result == "malicious_resolved":
        return "M"
    elif result == "private_resolved":
        return "P"
    elif result == "resolution_error":
        return "E"
    else:
        return "-"

# color of the letter. The invalid cells are very light, so a white letter
# would not be readable on them. They get a dark letter instead.
def get_letter_color(result):

    if result == "invalid_configuration":
        return color_text_light
    else:
        return "white"

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



# The row labels: 4 A values x 4 B1 values = 16 rows, always in the same order.
def make_row_labels():

    row_labels = []
    for A in A_values:
        for B1 in B1_values:
            row_labels.append(A + " - " + B1)
    return row_labels


# The column labels: 3 B2 values x 3 C1 values = 9 columns.
# "\n" puts B2 and C1 on two lines, so the label stays narrow.
def make_column_labels():

    column_labels = []
    for B2 in B2_values:
        for C1 in C1_values:
            column_labels.append(B2 + "\n" + C1)
    return column_labels


# Build the table of one block (one ecosystem).
# It gives back two tables with 16 rows and 9 columns:
#   number_table -> the number of the result, this is what imshow() draws
#   result_table -> the original result text, needed for the letters
def make_tables(results, ecosystem):

    number_table = []
    result_table = []

    for A in A_values:
        for B1 in B1_values:

            number_row = []
            result_row = []

            for B2 in B2_values:
                for C1 in C1_values:

                    key = (ecosystem, A, B1, B2, C1)
                    result = results[key]

                    number_row.append(get_code(result))
                    result_row.append(result)

            number_table.append(number_row)
            result_table.append(result_row)

    return number_table, result_table



def draw_one_block(ax, results, ecosystem, title, show_labels_on_left):

    number_table, result_table = make_tables(results, ecosystem)

    number_of_rows = len(number_table)         # 16
    number_of_columns = len(number_table[0])   # 9

    # Draw all 144 cells at once. imshow() puts cell [i][j] at position (j, i).
    # vmin / vmax make sure number 0 is the first color and number 3 the last one.
    ax.imshow(number_table, cmap=color_map, vmin=0, vmax=3)

    # write the letter in the middle of every cell (this is the loop from the
    # matplotlib "Annotated heatmap" example)
    for i in range(number_of_rows):
        for j in range(number_of_columns):
            result = result_table[i][j]
            ax.text(j, i, get_letter(result),
                    ha="center", va="center",
                    fontsize=7.5, color=get_letter_color(result))

    # the column labels on top
    ax.set_xticks(range(number_of_columns), labels=make_column_labels(),
                  fontsize=7, color=color_text_light)
    ax.xaxis.set_ticks_position("top")

    # the row labels on the left, only for the first block
    if show_labels_on_left:
        ax.set_yticks(range(number_of_rows), labels=make_row_labels(),
                      fontsize=7, color=color_text_light)
    else:
        ax.set_yticks([])

    ax.tick_params(length=0)          # no small lines next to the labels

    # White lines between the cells, so every cell is clearly separated.
    # The lines sit between two cells, that means at 0.5, 1.5, 2.5 ...
    # This trick also comes from the "Annotated heatmap" example.
    line_positions_x = []
    for j in range(number_of_columns + 1):
        line_positions_x.append(j - 0.5)

    line_positions_y = []
    for i in range(number_of_rows + 1):
        line_positions_y.append(i - 0.5)

    ax.set_xticks(line_positions_x, minor=True)
    ax.set_yticks(line_positions_y, minor=True)
    ax.grid(which="minor", color=color_background, linestyle="-", linewidth=2.5)
    ax.tick_params(which="minor", length=0)

    ax.set_title(title, fontsize=10.5, color=color_text, pad=26, loc="left")

    for side in ax.spines.values():   # no frame around the block
        side.set_visible(False)



def main():
    # which results file should be used?
    if len(sys.argv) > 1:
        csv_file = Path(sys.argv[1])
    else:
        csv_file = default_csv_file

    if not csv_file.exists():
        print("results.csv not found:", csv_file)
        return

    all_rows, results = read_results(csv_file)

    # create one figure with 3 block next to each other
    plt.rcParams["font.family"] = "DejaVu Sans"
    figure, axes = plt.subplots(1, 3, figsize=(10.4, 5.2),
                                facecolor=color_background)
    figure.subplots_adjust(left=0.105, right=0.995, top=0.86, bottom=0.10,
                           wspace=0.06)

    # draw the 3 block
    for block_number in range(len(block)):
        ecosystem = block[block_number][0]
        title = block[block_number][1]
        # only the first block gets the A / B1 labels on the left
        show_labels = (block_number == 0)
        draw_one_block(axes[block_number], results, ecosystem, title, show_labels)

    # --- the legend under the figure ---
    legend_boxes = [
        Rectangle((0, 0), 1, 1, facecolor=color_malicious, edgecolor="none"),
        Rectangle((0, 0), 1, 1, facecolor=color_private, edgecolor="none"),
        Rectangle((0, 0), 1, 1, facecolor=color_error, edgecolor="none"),
        Rectangle((0, 0), 1, 1, facecolor=color_invalid, edgecolor=color_border,
                  linewidth=0.6),
    ]
    legend_texts = [
        "M: malicious_resolved",
        "P: private_resolved",
        "E: resolution error",
        "-:  invalid configuration combinations",
    ]
    figure.legend(legend_boxes, legend_texts,
                  loc="lower center", ncol=4, frameon=False,
                  fontsize=8.5, labelcolor=color_text_light,
                  bbox_to_anchor=(0.5, 0.005),
                  handlelength=1.3, handleheight=1.1, columnspacing=1.8)


    pdf_file = script_folder / "figure_c_outcome_map.pdf"
    png_file = script_folder / "figure_c_outcome_map.png"
    figure.savefig(pdf_file, dpi=300, facecolor=color_background)
    figure.savefig(png_file, dpi=300, facecolor=color_background)
    print("wrote PDF", pdf_file)
    print("wrote png", png_file)

    # --- count the results, to check that the figure matches the data ---
    number_malicious = 0
    number_private = 0
    number_error = 0
    number_invalid = 0

    for row in all_rows:
        result = row[column_result]
        if result == "malicious_resolved":
            number_malicious = number_malicious + 1
        elif result == "private_resolved":
            number_private = number_private + 1
        elif result == "resolution_error":
            number_error = number_error + 1
        else:
            number_invalid = number_invalid + 1

    print()
    print("check the numbers (they must match the analysis plan):")
    print("  rows in results.csv     ", len(all_rows), "  expected 432")
    print("  malicious_resolved      ", number_malicious, "  expected 190")
    print("  private_resolved        ", number_private, "  expected 71")
    print("  resolution_error        ", number_error, "  expected 99")
    print("  invalid_configuration   ", number_invalid, "  expected 72")


main()
