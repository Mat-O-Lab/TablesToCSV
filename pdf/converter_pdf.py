import camelot
import pathlib
import json
import os.path

OUTPUT_DIR = "TMP_OUT"
# Strip characters from text
# stream: text is far apart vertically -> edge_tol=larger number
# flag_size=True
# group rows -> row_tol=larger number
# lattice: detecting smaller lines -> line_scale=larger number

def extract_tables(pdf_path, settings_path, p, tab_ar, table_count, debug=False) -> [float]:
    accuracy = {}
    """
    extracting tables out of PDF files with Camelot
    2 modes: lattice and stream
    """
    # table_areas = list(table_areas)
    # need to use lattice to extract closed tables and stream for open tables
    with open(settings_path, "rb") as settings_file:
        settings = json.load(settings_file)

        if settings["flavor"] == "Lattice":
            tables = camelot.read_pdf(
                pdf_path,
                flavor='lattice',
                process_background=settings["process_background"],
                line_size_scaling=settings["line_size_scaling"],  # increasing value detects smaller lines
                split_text=settings["split_text"],
                flag_size=settings["flag_size"],
                table_areas=tab_ar,
                pages=str(p),
            )

        else:
            tables = camelot.read_pdf(
                pdf_path,
                flavor='stream',
                row_close_tol=settings["row_close_tol"],
                col_close_tol=settings["col_close_tol"],
                split_text=settings["split_text"],
                flag_size=settings["flag_size"],
                table_areas=tab_ar,
                pages=str(p),
            )
        # debug information
        if debug:
            for table in tables:
                camelot.plot(table, kind='grid').show()
                camelot.plot(table, kind='contour').show()


        prefix = pdf_path.replace(".pdf", "")

        for table, i in zip(tables, range(len(tables))):
            # generate path to output file
            path_output = os.path.join(OUTPUT_DIR,prefix + "_page_" + str(p) + "_table_" + str(table_count) + ".csv")
            # replace , -> .
            tables[i].df.replace(to_replace=',', value='.', inplace=True, regex=True)
            tables[i].df.replace(to_replace='\n', value=' ', inplace=True, regex=True)
            # export csv
            tables[i].to_csv(path_output)

            accuracy[prefix + "_page_" + str(p) + "_table_" + str(table_count)] = tables[i].parsing_report["accuracy"]

        return accuracy


def convert_pixel_to_point(table_areas, image_size):
    (width, height) = image_size

    # DPI -> PDF2Image is 200
    # one point in a PDF is 72
    # https://www.debenu.com/kb/converting-pixels-and-inches-to-postscript-points/
    pdf_width = int(width / 200 * 72)
    pdf_height = int(height / 200 * 72)
    conv_width = pdf_width / width
    conv_height = pdf_height / height

    (x_1, y_1, x_2, y_2) = table_areas
    x_1 = int(x_1 * conv_width)
    x_2 = int(x_2 * conv_width)

    y_1 = int(y_1 * conv_height)
    y_2 = int(y_2 * conv_height)
    # PDF -> y starts with 0 at the bottom
    y_1 = pdf_height - y_1
    y_2 = pdf_height - y_2

    bounding_box = '%d,%d,%d,%d' % (x_1, y_1, x_2, y_2)
    bounding_box = [bounding_box]
    return bounding_box
