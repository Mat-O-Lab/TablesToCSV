import camelot
import pathlib
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

def extract_tables(path, p, tab_ar, table_count, parsing_report, line_size_scaling, split_text, flag_size):
    """
    extracting tables out of PDF files with Camelot
    """
    #table_areas = list(table_areas)
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
    """
    # debug information
    if debug:
        #for table in tables:
        #    camelot.plot(table, kind='grid').show()
        #    camelot.plot(table, kind='contour').show()
        for table, i in zip(tables, range(len(tables))):
            #print(tables[i])
            parsing_report.append(tables[i].parsing_report)
            #print(tables[i].df.head())
    """
    for table, i in zip(tables, range(len(tables))):
        filename = path + "_page_" + str(p) + "_table_" + str(table_count)
        # generate path to output file
        path_output = OUTPUT_DIR+"/" + filename + ".csv"
        # save parsing report
        parsing_report.append((filename, tables[i].parsing_report))
        # replace , -> .
        tables[i].df.replace(to_replace=',', value='.', inplace=True, regex=True)
        # replace new lines with one whitespace
        tables[i].df.replace(to_replace='\n', value=' ', inplace=True, regex=True)
        # export csv
        tables[i].to_csv(path_output)

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

def main(line_size_scaling=15, split_text=True, flag_size=False):
    # contains accuracy of table extraction
    parsing_report = []
    for path in pathlib.Path(INPUT_DIR).iterdir():
        # modify path to be able to work with it
        path = str(path)
        path = path.replace(".pdf", "")
        pdf_name = path.replace(INPUT_DIR+"\\", "")

        # get coordinates from tables
        coord = Coordinates.LocateTables()
        tables, dpi = coord.main(pdf_name, INPUT_DIR)

        table_count = 1
        new_page = 1
        for page, table_areas, image_size in tables:
            # need to reset table_count if a new page gets processed
            if new_page != page:
                table_count = 1
            new_page = page

            # converting pixel to PDF_points
            bounding_box = convert_pixel_to_point(table_areas, image_size, dpi)
            # extracting tables with camelot
            extract_tables(pdf_name, page, bounding_box, table_count, parsing_report, line_size_scaling, split_text, flag_size)
            table_count += 1
    return parsing_report