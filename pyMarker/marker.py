from systems import System, WaterMarkerException
from PIL import Image
from os.path import isfile
from re import sub


class Ratios:
    def __init__(self):
        self.throw = True

    def only_digit(self, message):
        try:
            return float(sub("[^0-9]", "", str(message)))
        except ValueError:
            if self.throw:
                raise WaterMarkerException("Error parsing image dimensions... contact Pseudonymous")
            return 0

    def calculate_im_size(self, video_width, video_height, im_width, im_height, aspect, real_width, real_height):
        if "%" in im_width:
            width_ratio = self.only_digit(video_width) * (self.only_digit(im_width) / 100)
            print (self.only_digit(im_width) / 100)
        else:
            width_ratio = self.only_digit(im_width)
        if "%" in im_height:
            height_ratio = self.only_digit(video_height) * (self.only_digit(im_height) / 100)
        else:
            height_ratio = self.only_digit(im_width)

        if aspect:
            print width_ratio
            print height_ratio
            new_ratio = min(self.only_digit(real_width) / width_ratio, self.only_digit(real_height) / height_ratio)
            width_ratio = self.only_digit(video_width) * new_ratio
            height_ratio = self.only_digit(video_height) * new_ratio

        return width_ratio, height_ratio, width_ratio / 2, height_ratio / 2

    def calculate_distances(self, video_width, video_height, w_perc, h_perc):
        if "%" in w_perc:
            width_ratio = self.only_digit(video_width) * (self.only_digit(w_perc) / 100)
        else:
            width_ratio = self.only_digit(w_perc)
        if "%" in h_perc:
            height_ratio = self.only_digit(video_height) * (self.only_digit(h_perc) / 100)
        else:
            height_ratio = self.only_digit(h_perc)
        return width_ratio, height_ratio

    def calulate_total(self, im_width, im_height, video_width, video_height, left, top, aspect, real_width,
                       real_height):
        image_w, image_h, image_center_w, image_center_h = self.calculate_im_size(video_width, video_height,
                                                                                  im_width, im_height, aspect,
                                                                                  real_width, real_height)
        distance_left, distance_top = self.calculate_distances(video_width, video_height, left, top)
        distance_left += image_center_w
        distance_top += image_center_h
        return image_w, image_h, distance_left, distance_top


class Marker:
    def __init__(self, verbosity=0):
        self.system = System()
        self.system.verbosity = verbosity
        self.system.get_system()
        self.system.get_src_folder()
        self.maxIcons = 20
        self.icons = [None] * self.maxIcons
        self.video_path = None
        self.video_size = [0, 0]
        self.properties = ["10%", "10%", "10%", "10%", True]
        self.extension = "PNG"

        if "ffmpeg version" not in self.system.ffmpeg("")[1]:
            self.system.report_error("Could not load ffmpeg, please make sure the src folder is in pyMarker")

    def load_image_path(self, path, ids=0):
        self.icons[ids] = None  # Overwrite list bug
        try:
            self.icons[ids]
        except (IndexError, ValueError):
            return False
        opt = [None, None]
        try:
            opt[0] = Image.open(path, "r")
            opt[1] = opt[0].size
        except IOError:
            return False
        self.icons[ids] = opt
        self.system.verbo_print("Image(%d) dimensions: %dx%d" % (ids, opt[1][0], opt[1][1]), 1)
        return opt[0] is not None

    def get_image_size(self, ids=0):
        return self.icons[ids][1][0], self.icons[ids][1][1]

    def get_video_size(self):
        return self.video_size[0], self.video_size[1]

    def load_video_path(self, path):
        if not isfile(str(path)):
            return False
        self.video_path = str(path)
        correct, get_raw = self.system.exif(path)
        if not correct:
            return False
        get_raw = str(get_raw).split("\n")
        for ind in range(0, len(get_raw)):
            if "width" in get_raw[ind].lower():
                self.video_size[0] = int(sub("[^0-9]", "", get_raw[ind]))
            if "height" in get_raw[ind].lower():
                self.video_size[1] = int(sub("[^0-9]", "", get_raw[ind]))
        self.system.verbo_print("Video dimensions: %dx%d" % (self.video_size[0], self.video_size[1]), 1)
        if self.video_size[0] == 0:
            self.system.report_error("Couldn't get video dimensions! Is exiftool working?")
            return False
        return True

    def set_properties(self, ids=0, **kwargs):
        self.properties[0] = kwargs.get("width", self.properties[0])
        self.properties[1] = kwargs.get("height", self.properties[1])
        self.properties[2] = kwargs.get("left", self.properties[2])
        self.properties[3] = kwargs.get("top", self.properties[3])
        self.properties[4] = kwargs.get("aspect", self.properties[4])
        self.system.verbo_print("Setting properties %s" % str(self.properties), 2)

    def get_properties(self):
        return self.properties

    def process(self):
        ratio = Ratios()
        for num in range(0, len(self.icons)):
            try:
                if self.icons[num] is None:
                    print "okokokok"
                    del self.icons[num]
            except IndexError:
                pass

        print self.icons

        prop_length = int(len(self.icons)) + 1

        print prop_length

        image_w = [0] * prop_length
        image_h = [0] * prop_length
        distance_left = [0] * prop_length
        distance_top = [0] * prop_length
        paths = [None] * prop_length
        filter_proc = " "

        for photo_ind in range(0, len(self.icons)):
            if self.icons[photo_ind] is not None:
                image_w[photo_ind], image_h[photo_ind], \
                    distance_left[photo_ind], distance_top[photo_ind] \
                    = ratio.calulate_total(self.properties[0], self.properties[1], self.video_size[0],
                                           self.video_size[1],
                                           self.properties[2], self.properties[3],
                                           self.properties[4],
                                           self.icons[photo_ind][1][0],
                                           self.icons[photo_ind][1][1])
                self.icons[photo_ind][0].thumbnail((image_w[photo_ind], image_h[photo_ind]), Image.ANTIALIAS)
                paths[photo_ind] = "%s/thumb_%d.%s" % (self.system.get_src_folder(), photo_ind, self.extension.lower())
                self.icons[photo_ind][0].save(paths[photo_ind], self.extension)
                filter_proc += "movie=%s [mark%d]; " % (paths[photo_ind], photo_ind)
        filter_proc += "[in]"
        for photo_ind in range(0, len(paths)):
            print photo_ind
            if paths is not None:
                filter_proc += str(("[tmp]" if photo_ind != 0 and len(distance_top) != 1 else "") +
                                   "[mark%d] overlay=%d:%d" + (" [tmp];"
                                                               if photo_ind == 0 and len(distance_top) != 1 and
                                                               distance_top[photo_ind] != distance_top[
                                                                      -1] else "")) % \
                               (int(photo_ind), int(distance_left[photo_ind]), int(distance_top[photo_ind]))
        print filter_proc


'''movie=logo1.png [logo1]; movie=logo2.png [logo2]; \
[in][logo1] overlay [tmp]; [tmp][logo2] overlay=50:50"'''

a = Marker(0)
a.set_properties()
print a.properties
if a.load_image_path("/root/Downloads/art.jpg"):
    print "Loaded image"
if a.load_video_path("/root/Downloads/video.mp4"):
    print "Loaded video"
a.process()
