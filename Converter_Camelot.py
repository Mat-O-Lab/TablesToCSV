import camelot
import Coordinates

"""
flavor -> always lattice
process background -> always false
line_size_scaling -> changeable by user
split_text -> changeable by user
flag_size -> changeable by user (super-/sub-scripts will be marked with <s> and </s>)
"""

OUTPUT_DIR = "TMP_OUT"
INPUT_DIR = "TMP_PDF"

def extract_tables(path, p, tab_ar, table_count, parse_report, line_size_scaling, split_text, flag_size, accuracy_threshold):
    """
    extracting tables out of PDF files with Camelot
    """
    # need to use lattice to extract closed tables and stream for open tables
    tables = camelot.read_pdf(
        INPUT_DIR+'/' + path + '.pdf',
        flavor='lattice',
        process_background=False,
        line_size_scaling=line_size_scaling, # increasing value detects smaller lines
        split_text =split_text,
        flag_size=flag_size, # marks subscripts/superscripts with <s>value</s>
        table_areas=tab_ar,
        pages=str(p),
    )
    if len(tables) == 0:
        filename = path + "_page_" + str(p)
        parse_report.append((filename, "Camelot may not have recognized a table"))
        found_table = False

    for table, i in zip(tables, range(len(tables))):
        filename = path + "_page_" + str(p) + "_table_" + str(table_count+1)
        found_table = True
        # generate path to output file
        path_output = OUTPUT_DIR+"/" + filename + ".csv"
        # save parsing report
        report = tables[i].parsing_report
        if report["accuracy"] <= accuracy_threshold:
            parse_report.append((filename, "There may be a problem with this table"))
        # replace , -> .
        tables[i].df.replace(to_replace=',', value='.', inplace=True, regex=True)
        # replace new lines with one whitespace
        tables[i].df.replace(to_replace='\n', value=' ', inplace=True, regex=True)
        # export csv
        tables[i].to_csv(path_output)
    return found_table

def convert_pixel_to_point(table_areas, image_size, dpi):
    """
    Coordinates.py works with pixels and Camelot uses points (PDF)
    Converting pixels to PDF_points
    """
    (width,height) = image_size

    # DPI -> PDF2Image is 200
    # one point in a PDF is 72
    # https://www.debenu.com/kb/converting-pixels-and-inches-to-postscript-points/
    pdf_width = int(width/dpi*72)
    pdf_height = int(height/dpi*72)
    conv_width = pdf_width/width
    conv_height = pdf_height/height
    
    (x_1, y_1, x_2, y_2) = table_areas
    x_1 = int(x_1*conv_width)
    x_2 = int(x_2*conv_width)

    y_1 = int(y_1*conv_height)
    y_2 = int(y_2*conv_height)
    # PDF -> y starts with 0 at the bottom
    y_1 = pdf_height-y_1
    y_2 = pdf_height-y_2

    bounding_box = '%d,%d,%d,%d' % (x_1,y_1,x_2,y_2)
    bounding_box = [bounding_box]
    return bounding_box

def main(pdf_name, settings):
    line_size_scaling = settings["line_size_scaling"]
    split_text = settings["split_text"]
    flag_size = settings["flag_size"]
    accuracy_threshold = settings["accuracy_threshold"]
    # contains accuracy of table extraction
    parse_report = []
    # modify path to be able to work with it
    pdf_name = pdf_name.replace(".pdf", "")

    try:
        # get coordinates from tables
        coord = Coordinates.LocateTables()
        tables, dpi = coord.main(pdf_name, INPUT_DIR)
    except:
        parse_report.append((pdf_name, "An error occured: LocateTables"))
        return False, parse_report

    table_count = 0
    new_page = 1
    found_at_least_one_table = False
    for page, table_areas, image_size in tables:
        # need to reset table_count if a new page gets processed
        if new_page != page:
            table_count = 0
            new_page = page

        # converting pixel to PDF_points
        bounding_box = convert_pixel_to_point(table_areas, image_size, dpi)
        # extracting tables with camelot
        try:
            found_table = extract_tables(pdf_name, page, bounding_box, table_count, parse_report, line_size_scaling, split_text, flag_size, accuracy_threshold)
        except:
            parse_report.append((pdf_name, "An error occured: Camelot"))
            return False, parse_report
        if found_table:
            table_count += 1
            found_at_least_one_table = True
    if found_at_least_one_table == False:
        parse_report.append((pdf_name, "No tables were found"))
        return False, parse_report
    return True, parse_report
