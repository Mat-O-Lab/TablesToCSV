import cv2
import numpy as np
from pdf2image import convert_from_path
try:
    from PIL import Image, ImageOps
except ImportError:
    import Image, ImageOps

class LocateTables:
    """
    localizes the coordinates of all tables in a PDF
    """
    def __init__(self):
        self.coordinates = []
        self.iteration = -1
        self.validated_tables = []

        # quality: PDFtoImage, higher values can lead to a better recognition and a worse performance
        self.dpi = 100
        # higher dpi - higher value
        self.kernel_div = 35
        # a table with very large cells might not be recognized if this value is too small
        # a graph might be recognized as a table if this value is too large
        self.max_size_cell_in_table = 14000

    def converter(self, img):
        """
        converts the image to an image where only straight lines are visible
        output: all lines, vertical lines, horizontal lines
        """
        #thresholding the image to a binary image
        thresh,img_bin = cv2.threshold(img,128,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        #inverting the image 
        img_bin = 255-img_bin

        # countcol(width) of kernel as 50th of total width
        kernel_len = np.array(img).shape[1]//self.kernel_div
        # Defining a vertical kernel to detect all vertical lines of image 
        ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
        # Defining a horizontal kernel to detect all horizontal lines of image
        hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        # A kernel of 2x2
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

        #Use vertical kernel to detect the vertical lines in a jpg
        image_1 = cv2.erode(img_bin, ver_kernel, iterations=1)
        vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=1)
        #Use horizontal kernel to detect the horizontal lines in a jpg
        image_2 = cv2.erode(img_bin, hor_kernel, iterations=3)
        horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=3)

        # Combine horizontal and vertical lines in a new third image, with both having same weight.
        img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
        #Eroding and thesholding the image
        img_vh = cv2.erode(~img_vh, kernel, iterations=1)
        thresh, img_vh = cv2.threshold(img_vh,128,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        return img_vh,vertical_lines,horizontal_lines

    def imageCrop(self, img_vh, iteration):
        """
        uses the function tableseperator to crop the image
        """
        # inverting the image
        img_vh_invert = ImageOps.invert(img_vh)
        
        w, h = img_vh_invert.size

        # using tableseperator to find vertical structures in the image
        transpose = False
        verticalSpikes, spike_values = self.tableSeperator(img_vh_invert, transpose)
        # using the vertical spikes to crop the structures out of the image
        vertical_croppedList = []
        for (y_start, y_end) in verticalSpikes:
            vertical_croppedList.append((img_vh_invert.crop((0,y_start,w,y_end)), (y_start,y_end)))
        
        # cropping the horizontal structures out of the vertical_croppedList
        transpose = True
        cropped_list = []
        for (image, (y_start,y_end)) in vertical_croppedList:
            # only consider structures that have a minimal length of 50 because smaller structures cannot be tables
            if y_end-y_start > 50:
                horizontalSpikes, spike_values = self.tableSeperator(image, transpose)
                w_cI, h_cI = image.size
                # if several tables are horizontally next to each other the vertical length needs to be adjusted
                if len(horizontalSpikes)>1:
                    for (x_start, x_end) in horizontalSpikes:
                        if(x_end-x_start>50 and y_end-y_start>50):
                            image_new = image.crop((x_start,0,x_end,h_cI))
                            verticalSpikes, spike_values = self.tableSeperator(image_new, False)
                            for (y_start_new,y_end_new) in verticalSpikes:
                                if y_end_new-y_start_new>50:
                                    cropped_list.append([image.crop((x_start,y_start_new,x_end,y_end_new)),(x_start,(y_start+y_start_new),x_end,(y_end+y_start_new)), iteration])
                else:
                    for (x_start, x_end) in horizontalSpikes:
                        if(x_end-x_start>50 and y_end-y_start>50):
                            cropped_list.append([image.crop((x_start,0,x_end,h_cI)),(x_start,y_start,x_end,y_end), iteration])
        # worked with inverted images, invert it again
        for (image, border, iter), i in zip(cropped_list, range(len(cropped_list))):
            cropped_list[i][0] = ImageOps.invert(cropped_list[i][0])
        
        return cropped_list

    def tableSeperator(self, img, transpose):
        """
        detects where vertical/horizontal lines are and give the coordinates of them back
        """
        image_array = np.array(img)
        width, height = img.size

        # transpose=True -> finding horizontal structures
        # transpose=False -> finding vertical structures
        if(transpose):
            image_array = image_array.T
            var = width
        else:
            var = height
        spike_values = []
        spikes = []
        startSpikeDetected = False
        start = 0
        end = 0
        for row in range(var):
            # detecting the start of a structure
            if(sum(image_array[row][:]) != 0 and startSpikeDetected != True):
                    start = row 
                    startSpikeDetected = True

                    spike_values.append(sum(image_array[row][:]))
            # detecting the end of the structure
            elif(sum(image_array[row][:]) == 0 and startSpikeDetected):
                    startSpikeDetected = False
                    end = row-1
                    spikes.append((start,end))
            # detecting the end of the structure
            elif(row == var-1 and startSpikeDetected):
                startSpikeDetected = False
                end = row
                spikes.append((start,end))

        return spikes, spike_values

    def validate_table(self, image):
        """
        sort out structures like graphs that got recognized as tables
        """
        table_is_valid = True
        conv_crop,vertical_lines,horizontal_lines = self.converter(np.array(image))
        horizontal_lines = Image.fromarray(horizontal_lines)
        vertical_lines = Image.fromarray(vertical_lines)
        # removing the border of structures
        borderless_image = self.remove_border(image, horizontal_lines, vertical_lines)

        # executed if the structure had a border around it
        # finding out if the structure was a box around other structures
        old_coordinates = self.coordinates[self.iteration]
        if borderless_image != []:
            # finding structures in image
            cropped_images = self.imageCrop(borderless_image, self.iteration+1)
            if len(cropped_images) == 0:
                table_is_valid = False
                borderless_image = []
                return table_is_valid, borderless_image
            # found one structure
            if len(cropped_images) == 1:
                w_new, h_new = cropped_images[0][0].size
                w_old, h_old = borderless_image.size
                # finding out if a structure is in a box
                if (w_new*h_new)/(w_old*h_old) < 0.9:
                    table_is_valid = False
                    return table_is_valid, cropped_images
                self.coordinates[self.iteration] = old_coordinates
                borderless_image = []
            # several structures in it -> found a box around content of a PDF
            else:
                table_is_valid = False
                return table_is_valid, cropped_images

        horizontal_spikes, spike_values_horizontal = self.tableSeperator(vertical_lines, True)
        vertical_spikes, spike_values_vertical = self.tableSeperator(horizontal_lines, False)

        w, h = image.size
        # maximal value that spikes can reach, 255 * w , 255 * h
        # if the line goes through 50% or more percent of the image and if it's not a border of the image it's a valid spike
        valid_spikes_vertical = vertical_spikes.copy()
        valid_spikes_horizontal = horizontal_spikes.copy()

        minimum_line_width = 255*w*0.5
        minimum_line_height = 255*h*0.5
        for (start, end), i in zip(vertical_spikes, range(len(vertical_spikes))):
            if start == 0 or end == h-1:
                valid_spikes_vertical.remove((start,end))
            elif spike_values_vertical[i] < minimum_line_width:
                valid_spikes_vertical.remove((start,end))
        
        for (start, end), i in zip(horizontal_spikes, range(len(horizontal_spikes))):
            if start == 0 or end == w-1:
                valid_spikes_horizontal.remove((start,end))
            elif spike_values_horizontal[i] < minimum_line_height:
                valid_spikes_horizontal.remove((start,end))
        

        # calculate how many cells are contained in the structure
        cells = (len(valid_spikes_vertical)+1)*(len(valid_spikes_horizontal)+1)
        table_size = w*h

        # if the average size of a cell is too large or if it doen't contain vertical or horizontal lines it is not a table
        if (table_size/cells)>self.max_size_cell_in_table or len(valid_spikes_vertical) == 0 or len(valid_spikes_horizontal) == 0:
            table_is_valid = False

        return table_is_valid, borderless_image

    def main(self, filename, INPUT_DIR):
        # extracing images of a PDF
        pages = convert_from_path(INPUT_DIR +"/"+ filename +".pdf", self.dpi, grayscale=True)
        tables = []
        # for every page in a PDF
        for page, i in zip(pages, range(len(pages))):
            # array with coordinates of tables
            self.coordinates = []
            self.iteration = -1
            # contains all validated tables
            self.validated_tables = []

            img = np.array(page)
            img_vh,vertical_lines,horizontal_lines = self.converter(img)
            img_vh = Image.fromarray(img_vh)

            w,h =  page.size
            # detecting tables
            self.detectTable([img_vh, -1], False)
            for valid in self.validated_tables:
                tables.append([i+1, valid[1],[w,h]])

        return tables, self.dpi
    
    def detect_border(self, img, transpose):
        """
        detects if the structure has a border and removes it
        similar to the function tableSeperator
        """
        image_array = np.array(img)
        width, height = img.size

        # transpose=True -> finding horizontal structures
        # transpose=False -> finding vertical structures
        if(transpose):
            image_array = image_array.T
            var = width
        else:
            var = height
        spikes = []
        startSpikeDetected = False
        start = 0
        end = 0
        # looks at the first line of the image
        # if it contains a line, it's a border
        for row in range(var):
            # detecting the start of a spike
            if(sum(image_array[row][:]) != 0 and startSpikeDetected != True):
                    start = row 
                    startSpikeDetected = True
            # detecting the end of the spike
            elif(sum(image_array[row][:]) == 0 and startSpikeDetected):
                    startSpikeDetected = False
                    end = row-1
                    spikes.append((start,end))
            # detecting the end of the spike
            elif(row == var-1 and startSpikeDetected):
                startSpikeDetected = False
                end = row
                spikes.append((start,end))
            # only looks at the first line
            if startSpikeDetected==False:
                break
        # looks at the last line of the image
        # if it contains a line, it's a border
        if spikes != []:
            startSpikeDetected = False
            start = 0
            end = 0
            for row in range(var):
                # detecting the start of a spike
                if(sum(image_array[var-row-1][:]) != 0 and startSpikeDetected != True):
                        end = var-row-1
                        startSpikeDetected = True
                # detecting the start and end of the spike
                elif(sum(image_array[var-row-1][:]) == 0 and startSpikeDetected):
                        startSpikeDetected = False
                        start = var-row-2
                        spikes.append((start,end))
                # detecting the end of the spike
                elif(row == var-1 and startSpikeDetected):
                    startSpikeDetected = False
                    start = var-row-1
                    spikes.append((start,end))
                # only looks at the first line
                if startSpikeDetected==False:
                    break
            # detects if the spike values are valid
            for spike in spikes:
                if spike[0] != 0 and spike[1] != var-1:
                    spikes=[]
                    break
        return spikes

    def remove_border(self, image, horizontal_lines, vertical_lines):
        """
        removing the border of a image
        """
        border = self.detect_border(horizontal_lines, False)
        border = border + self.detect_border(vertical_lines, True)
        # if border does not contain 4 values it's not a valid border
        if len(border) < 4:
            return []

        w,h = image.size
        # calculate the new coordinates of the table
        (x0, y0, x1, y1) = self.coordinates[self.iteration]
        (x0_new, y0_new, x1_new, y1_new) = border[2][1]+1, border[0][1]+1,(-(border[3][1]-border[3][0]))-1,(-(border[1][1]-border[1][0]))-1
        # crop the image and save the new coordinates
        image = image.crop((x0_new,y0_new,w+x1_new,h+y1_new))
        self.coordinates[self.iteration] = (x0+x0_new, y0+y0_new, x1+x0_new, y1+y0_new)

        return image

    def detectTable(self, img_vh, crop):
        """
        detecting tables in a image

        img_vh = (image, self.iteration)
        """
        if crop:
            cropped_images=img_vh
        else:
            cropped_images = self.imageCrop(img_vh[0], img_vh[1]) # first iteration (img, -1)
        for image, border, iter in cropped_images:
            # if a imagecrop gets processed for the first time iter contains a -1
            # otherwise coordinates already exist for that crop
            if iter == -1:
                self.coordinates.append(border)
            else:
                # adding the coordinates of the previous crop with the new crop
                (x1,y1,x2,y2) = border
                # previous border
                (x1_old,y1_old,x2_old,y2_old) = self.coordinates[iter]
                # calculating and appending new border
                border = (x1+x1_old,y1+y1_old,x2+x1_old,y2+y1_old)
                self.coordinates.append(border)
        
            # validate if the found structure is a table
            validation, cropped = self.validate_table(image)
            
            # recursion call to process structures in the image
            if validation == False and cropped != []:
                self.iteration += 1
                self.detectTable(cropped, True)
            # no table were found
            elif validation == False and cropped==[]:
                continue
            # structure is a valid table
            else:
                self.iteration += 1
                image = [image, self.coordinates[self.iteration]]
                self.validated_tables.append(image)
