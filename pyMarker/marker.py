from systems import System, WaterMarkerException
from PIL import Image
from os.path import isfile
from os import remove
from re import sub


class Ratios:
    def __init__(self):
        self.throw = True

    def only_digit(self, message):
        try:
            return float(sub("[^0-9 .]", "", str(message)))
        except ValueError:
            if self.throw:
                raise WaterMarkerException("Error parsing image dimensions... contact Pseudonymous")
            return 0

    def calculate_im_size(self, video_width, video_height, im_width, im_height, aspect, real_width, real_height):
        if "%" in im_width:
            width_ratio = self.only_digit(video_width) * (self.only_digit(im_width) / 100)
        else:
            width_ratio = self.only_digit(im_width)
        if "%" in im_height:
            height_ratio = self.only_digit(video_height) * (self.only_digit(im_height) / 100)
        else:
            height_ratio = self.only_digit(im_width)

        '''
        if aspect:
            new_ratio = min(self.only_digit(real_width) / width_ratio, self.only_digit(real_height) / height_ratio)
            width_ratio = self.only_digit(video_width) * new_ratio
            height_ratio = self.only_digit(video_height) * new_ratio
        '''

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
        distance_left -= image_center_w
        distance_top -= image_center_h
        return image_w, image_h, distance_left, distance_top


class Marker:
    def __init__(self, verbosity=0):
        self.system = System()
        self.system.verbosity = verbosity
        self.system.get_system()
        self.system.get_src_folder()
        self.maxIcons = 20
        self.icons = [None] * self.maxIcons
        self.video_path = ""
        self.video_size = [0, 0]
        self.frame_count = 0
        self.video_length = 0
        self.properties = [["10%", "10%", "10%", "10%", True, 1, 0, -1, 0, (False, 0, 0),
                            (False, 0, 0)]] * self.maxIcons
        self.extension = "PNG"
        self.out_vid_extension = "mp4"

        if "ffmpeg version" not in self.system.ffmpeg("")[1]:
            self.system.report_error("Could not load ffmpeg, please make sure the src folder is in pyMarker")

    def load_overlay_path(self, path, ids=0):
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
        made_it = opt[0] is not None
        self.system.verbo_print("Loaded overlay Image! %d" % ids
                                if made_it else "Failed to load overlay Image! %d" % ids, 1)
        return made_it

    def get_image_size(self, ids=0):
        return self.icons[ids][1][0], self.icons[ids][1][1]

    def get_video_size(self):
        return self.video_size[0], self.video_size[1]

    def get_video_duration(self):
        return float(self.video_length)

    def set_video_extension(self, ext="mp4"):
        self.out_vid_extension = ext

    def set_image_extension(self, ext="PNG"):
        self.extension = ext

    def load_background_video_path(self, path):
        if not isfile(str(path)):
            self.system.verbo_print("Video file not found!", 1)
            return False
        self.video_path = str(path)
        correct, get_raw = self.system.ffprobe(
            "-v error -of flat=s=_ -select_streams v:0 -show_entries stream=height,width %s" % str(path))
        if not correct:
            self.system.verbo_print("Could not get video size!", 1)
            return False
        get_raw = str(get_raw).split("\n")
        for ind in range(0, len(get_raw)):
            if "width" in get_raw[ind].lower():
                self.video_size[0] = int(sub("[^0-9]", "", get_raw[ind][get_raw[ind].index("width"):]))
            if "height" in get_raw[ind].lower():
                self.video_size[1] = int(sub("[^0-9]", "", get_raw[ind][get_raw[ind].index("height"):]))
        self.system.verbo_print("Video dimensions: %dx%d" % (self.video_size[0], self.video_size[1]), 1)
        if self.video_size[0] == 0:
            self.system.report_error("Couldn't get video dimensions! Is ffprobe working?")
            return False

        correct, get_raw = self.system.ffprobe(
            "-v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames "
            "-of default=nokey=1:noprint_wrappers=1 %s" % str(path))

        if not correct:
            self.system.verbo_print("Couldn't get video frame count setting default...", 1)
            self.video_length = 2000
        digits = sub("[^0-9 .]", "", str(get_raw))
        self.frame_count = float(digits)
        self.system.frames = self.frame_count
        self.system.verbo_print("Video frames: %d" % self.frame_count, 2)

        correct, get_raw = self.system.ffprobe("-v quiet -of csv=p=0 -show_entries" +
                                               " format=duration %s" % str(path))
        if not correct:
            self.system.verbo_print("Couldn't get video length setting default...", 1)
            self.video_length = 2000
        digits = sub("[^0-9 .]", "", str(get_raw))
        self.video_length = float(digits) + 1
        self.system.verbo_print("Video time(s): %d" % (self.video_length - 1), 2)
        for indent in range(0, len(self.icons)):
            try:
                self.properties[indent][7] = self.video_length if self.properties[indent][7] == -1 \
                    else self.properties[indent][7]
            except (IndexError, ValueError, TypeError):
                pass
        self.system.verbo_print("Background video loaded!", 1)
        return True

    '''
    def load_video_path(self, path, ids=0):
        if not isfile(str(path)):
            return False
        self.icons[ids] = None
        correct, get_raw = self.system.exif(path)
        opt = [path, None]
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
        opt

        return True
    '''

    def fade_in(self, ids=0, start_time=0, duration=2):
        self.set_properties(ids, fadein=(True, start_time, duration))

    def fade_out(self, ids=0, start_time=0, duration=2):
        self.set_properties(ids, fadeout=(True, start_time, duration))

    def set_properties(self, ids=0, **kwargs):
        temp_prop = [kwargs.get("width", self.properties[ids][0]), kwargs.get("height", self.properties[ids][1]),
                     kwargs.get("left", self.properties[ids][2]), kwargs.get("top", self.properties[ids][3]),
                     kwargs.get("aspect", self.properties[ids][4]), kwargs.get("alpha", self.properties[ids][5]),
                     kwargs.get("start", self.properties[ids][6]), kwargs.get("end", self.properties[ids][7]),
                     kwargs.get("rotate", self.properties[ids][8]), kwargs.get("fadein", self.properties[ids][9]),
                     kwargs.get("fadeout", self.properties[ids][10])]
        if temp_prop[7] < 0 < self.video_length:
            temp_prop[7] = self.video_length
        self.properties[ids] = temp_prop
        self.system.verbo_print("Setting properties %s" % str(self.properties), 2)

    def get_properties(self):
        return self.properties

    def process(self, output=None):
        ratio = Ratios()
        for num in range(0, len(self.icons)):
            try:
                if self.icons[num] is None:
                    del self.icons[num]
            except IndexError:
                pass
        prop_length = int(len(self.icons)) + 1

        image_w = [0] * prop_length
        image_h = [0] * prop_length
        distance_left = [0] * prop_length
        distance_top = [0] * prop_length
        paths = [None] * prop_length
        filter_proc = ""

        for photo_ind in range(0, len(self.icons)):
            try:
                point = self.icons[photo_ind][1]
                del point
                self.icons[photo_ind][0] = self.icons[photo_ind][0].convert("RGBA")
                if self.properties[photo_ind][8] > 0 or self.properties[photo_ind][8] < 0:
                    self.icons[photo_ind][0] = self.icons[photo_ind][0].rotate(self.properties[photo_ind][8],
                                                                               expand=True)
                    self.system.verbo_print("Rotating image %d by %d degress" % (photo_ind,
                                                                                 int(self.properties[photo_ind][8])), 1)
                image_w[photo_ind], image_h[photo_ind], \
                distance_left[photo_ind], distance_top[photo_ind] \
                    = ratio.calulate_total(self.properties[photo_ind][0], self.properties[photo_ind][1],
                                           self.video_size[0],
                                           self.video_size[1],
                                           self.properties[photo_ind][2],
                                           self.properties[photo_ind][3],
                                           self.properties[photo_ind][4],
                                           self.icons[photo_ind][1][0],
                                           self.icons[photo_ind][1][1])
                if self.properties[photo_ind][4]:
                    self.icons[photo_ind][0].thumbnail((int(image_w[photo_ind]), int(image_h[photo_ind])),
                                                       Image.ANTIALIAS)
                else:
                    self.system.verbo_print("Not using aspect ratio...", 2)
                    self.icons[photo_ind][0] = \
                        self.icons[photo_ind][0].resize((int(image_w[photo_ind]), int(image_h[photo_ind])),
                                                        Image.ANTIALIAS)
                paths[photo_ind] = "%s/thumb_%d.%s" % (self.system.get_src_folder(), photo_ind, self.extension.lower())
                self.icons[photo_ind][0].save(paths[photo_ind], self.extension)
                filter_proc += "movie=%s [mark%d]; " % (paths[photo_ind], photo_ind)
            except (IndexError, ValueError, TypeError):
                pass

        filter_proc += "[in]"
        for photo_ind in range(0, len(paths)):
            try:
                point = self.icons[photo_ind][1]
                del point
                # print "Distances: %dx%d" % (distance_left[photo_ind], distance_top[photo_ind])
                # print "Photo %d top_d %d" % (photo_ind, len(distance_top))
                # print photo_ind
                filter_proc += str(("[tmp]" if photo_ind != 0 and len(distance_top) != 1 else "") +
                                   "[mark%d]" +
                                   #(" format=rgba," if self.properties[photo_ind][9][0] or
                                                       #self.properties[photo_ind][10][0] else "") +
                                   (" fade=in:0:25,fade=out:975:25 [tmp];"#("format=rgba,fade=out:73:1:alpha=1 [tmp];" #% (float(self.properties[photo_ind][9][1]),
                                                                     #float(self.properties[photo_ind][9][2]))
                                    if self.properties[photo_ind][9][0]
                                    else "") +# ("," if self.properties[photo_ind][9][0]
                                                       #and self.properties[photo_ind][9][0] else "") +
                                   #("fade=out:%d:%d:alpha=1 [tmp];" % (float(self.properties[photo_ind][10][1]),
                                           #                           float(self.properties[photo_ind][10][2]))
                                   # if self.properties[photo_ind][9][0]
                                   # else "") +
                                   "[tmp] overlay=%d:%d:enable='between(t,%d,%d)'" + (" [tmp];"
                                                                                if (photo_ind != len(paths) - 1
                                                                                    and len(distance_top) != 1)
                                                                                   or not photo_ind <= len(
                    distance_top) else "")) % (
                                   int(photo_ind),
                                   int(distance_left[photo_ind]),
                                   int(distance_top[photo_ind]),
                                   int(self.properties[photo_ind][6]),
                                   int(self.properties[photo_ind][7]))
            except(IndexError, ValueError, TypeError):
                pass
        if "[tmp]" in filter_proc[-7:]:
            filter_proc = filter_proc[:filter_proc.rfind("[tmp];")]

        if output is None:
            output_path = "%s.%s" % (self.video_path[:self.video_path.rfind(".")], self.out_vid_extension)
            if output_path == self.video_path or isfile(output_path):
                self.system.verbo_print("Input is equal to ouput renaming...", 2)
                num = 0
                while isfile(output_path):
                    num += 1
                    output_path = "%s(%d).%s" % (self.video_path[:self.video_path.rfind(".")], num,
                                                 self.out_vid_extension)
                self.system.verbo_print("This was done %d times!?" % num, 2)
        else:
            output_path = output
            if output_path == self.video_path:
                self.system.verbo_print("No memory holster yet bud... sorry (Input can't equal output)", 1)
                output_path = output_path[:output_path.rfind(".") - 1] + "2." + output_path[output_path.rfind("."):]

        if isfile(output_path):
            remove(output_path)  # Cleanup file

        final_procs = "-i %s -vf \"%s\" \"%s\"" % (self.video_path, filter_proc, output_path)
        self.system.verbo_print("ffmpeg command: ffmpeg %s" % final_procs, 3)
        response = self.system.ffmpeg(final_procs)
        self.system.verbo_print("Finished processing video... (exit: %d)" % int(not response[0]), 1)
        return response[0]


a = Marker(4)
a.set_properties(0, width="10%", height="10%", left="20%", top="20%")
a.fade_in(0, 0, 3)
# a.set_properties(1, left="50%", top="50%")
# a.set_properties(2, left="80%", top="80%")
# print a.properties
a.load_overlay_path("/root/Downloads/art.jpg", 0)
if a.load_background_video_path("/root/Downloads/video.mp4"):
    a.process()
else:
    print "video fail"
