import math

class CropsCoordinates(object):
    """
    Holds the functions to calculate crops coordinates when cutting up a large image and also transformation of a
    crop back into the original image coordinates.
    function: get_crops_coordinates
    """

    def __init__(self, settings):
        self.settings = settings

        #self.scale_ratio_of_attention_crop = 1.0
        #self.crop_size_in_attention = 0

        settings.horizontal_splits
        settings.overlap_px
        settings.attention_horizontal_splits
        settings.attention
        settings.w
        settings.h

    def get_crops_coordinates(self, type):
        crops_coords, scale_full_img, crop_size = self.crop_from_one_img(type)

        if type == 'attention':
            self.scale_ratio_of_attention_crop = scale_full_img
            self.crop_size_in_attention = crop_size
        elif type == 'evaluation':
            self.scale_ratio_of_evaluation_crop = scale_full_img
            self.crop_size_in_evaluation = crop_size

        if self.settings.verbosity >= 3:
            print("Crop coordinates for stage `"+type+"` generated with one crop sized",crop_size)
        return crops_coords

    def project_evaluation_back(self, attention_evaluation, type):
        """
        Explain + Format
        :param attention_evaluation:
        :param type:
        :return:
        """
        projected_evaluation = []
        for id, bboxes in attention_evaluation:
            bboxes_in_img = self.project_back_to_original_image(id, bboxes, type)
            projected_evaluation += bboxes_in_img
        return projected_evaluation

    def project_coordinates_back(self, coordinates, type):
        # coordinates come in array of [[id, (0, 0, 608, 608)], ... ]
        # just / scale to each value
        projected_coordinates = []
        for id, coordinate in coordinates:
            if type == 'attention':
                scale = self.scale_ratio_of_attention_crop
            elif type == 'evaluation':
                scale = self.scale_ratio_of_evaluation_crop

            projected_coordinate = [int(i / scale) for i in coordinate]

            projected_coordinates.append([id,projected_coordinate])
        return projected_coordinates

    def project_back_to_original_image(self,id,bboxes,type):
        # bboxes is array of dictionaries like:
        # {'label': 'person', 'confidence': 0.19, 'topleft': {'x': 141, 'y': 301}, 'bottomright': {'x': 153, 'y': 331}}

        # crops is array of :
        # [[0, (0, 0, 608, 608)], ...]

        if type == 'attention':
            crops = self.last_attention_crops[id]
            scale = self.scale_ratio_of_attention_crop
        elif type == 'evaluation':
            crops = self.last_evalutaion_crops[id]
            scale = self.scale_ratio_of_evaluation_crop

        area = crops[1] # area in (0, 0, 608, 608), (472, 0, 1080, 608), ...
        # area is LEFT, TOP, RIGHT, BOTTOM

        for bbox in bboxes:
            bbox["topleft"]["x"] = (area[0] + bbox["topleft"]["x"]) / scale
            bbox["topleft"]["y"] = (area[1] + bbox["topleft"]["y"]) / scale
            bbox["bottomright"]["x"] = (area[0] + bbox["bottomright"]["x"]) / scale
            bbox["bottomright"]["y"] = (area[1] + bbox["bottomright"]["y"]) / scale

        return bboxes

    ## could be better:
    def best_squares_overlap(self, w, h, horizontal_splits, overlap_px):
        #print("called best_squares_overlap, with [w, h, horizontal_splits, overlap_px]:", w, h, horizontal_splits, overlap_px)

        crop = int((h + overlap_px * (horizontal_splits - 1)) / horizontal_splits)

        row_list = []
        for i in range(0, horizontal_splits):
            row_list.append([int(i * (crop - overlap_px)), int(i * (crop - overlap_px) + crop)])

        n_v = math.ceil((w - crop) / (crop - overlap_px) + 1)
        loc = (w - crop) / (n_v - 1)

        column_list = []

        column_list.append([0, crop])
        for i in range(1, n_v - 1):
            column_list.append([int(i * (loc)), int(i * (loc) + crop)])
        column_list.append([w - crop, w])

        # print(len(column_list) * len(row_list))

        return column_list, row_list

    def crop_from_one_img(self, type):
        if type == 'attention':
            horizontal_splits = self.settings.attention_horizontal_splits
        elif type == 'evaluation':
            horizontal_splits = self.settings.horizontal_splits

        nh = 608 + (608 - self.settings.overlap_px) * (horizontal_splits - 1)
        scale_full_img = nh / self.settings.h
        nw = int(self.settings.w * scale_full_img)
        nh = int(nh)

        overlap_px = self.settings.overlap_px
        w_crops, h_crops = self.best_squares_overlap(nw, nh, horizontal_splits, overlap_px)
        # w_crops: [[0, 608], [517, 1125], [1035, 1643], [1553, 2161]]
        # h_crops: [[0, 608], [608, 1216]]
        crop_size = w_crops[0][1] - w_crops[0][0]

        crops = []
        i = 0
        for w_crop in w_crops:
            for h_crop in h_crops:
                area = (int(w_crop[0]), int(h_crop[0]), int(w_crop[0] + crop_size), int(h_crop[0] + crop_size))
                crops.append([i, area])
                i += 1

        """
        returns
        crops = array of [[0, (0, 0, 608, 608)] 
        """

        if type == 'attention':
            self.last_attention_crops = crops
        elif type == 'evaluation':
            self.last_evalutaion_crops = crops

        return crops, scale_full_img, crop_size
