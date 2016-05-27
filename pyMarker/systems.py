from sys import platform as _platforms, exit
from platform import architecture
from subprocess import Popen, PIPE
from signal import signal, SIGINT
from os.path import dirname, realpath


class WaterMarkerException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


def handle_exit(code, frame):
    try:
        print("WaterMarker exiting(Frame: %d)... %d" % (frame, code))
        exit(code)
    except TypeError:
        print("WaterMarker exit!!!")
        exit(1)


class System:
    def __init__(self):
        self.system = None
        self.verbosity = 3
        signal(SIGINT, handle_exit)

    def report_error(self, mess, num=1):
        raise WaterMarkerException("(Code %d, Verbose %d) %s" % (num, self.verbosity, mess))

    def verbo_print(self, mess, num, equal=False):
        if self.verbosity >= num if not equal else num == self.verbosity:
            print(mess)

    def command(self, com, ret_err=0, err_text=None):
        if not len(str(com)) > 0:
            return [False, ""]
        com_list = str(com)  # .strip(" ").split(" ") if not isinstance(com, list) else com
        try:
            child = Popen(com_list, stderr=PIPE, stdout=PIPE, shell=True)
            communicate = child.communicate()
            try:
                stream = (communicate[1] + communicate[0]) if communicate[1][0] is not None else communicate[0]
            except IndexError:
                stream = communicate[0]
            code = child.returncode
        except OSError, err:
            if ret_err == 0:
                self.verbo_print("WATER-WARNING: %s" % str(err.strerror), 2)
            else:
                self.report_error(err.strerror)
            return [False, "HANDLE"]
        if err_text is not None:
            if err_text in str(stream):
                return [False, ""]
        self.verbo_print(stream, 2)
        return [code < 1, stream]

    @staticmethod
    def get_src_folder():
        return dirname(realpath(__file__)) + "/src"

    def get_system_folder(self):
        folder = "/linux"
        if self.system == 0:
            folder = "/linux"
        elif self.system == 1:
            folder = "/mac"
        elif self.system == 2:
            folder = "/win"
        return self.get_src_folder() + folder

    def get_ffmpeg_folder(self):
        folder = self.get_system_folder()
        arch = architecture()[0]
        if "64" in arch or "x86_64" in arch:
            arch = "64/"
        else:
            arch = "32/"
        return "%s/%s" % (folder, arch if self.system != 2 else (arch + "bin/"))

    def ffmpeg(self, args, ret_err=0, err_text=None):
        folder = self.get_ffmpeg_folder()
        executable = "ffmpeg" if self.system != 2 else "ffmpeg.exe"
        working = folder + executable + " " + str(args)
        self.verbo_print("Working ffmpeg: %s" % working, 2)
        return self.command(working, ret_err, err_text)

    def exif(self, args, ret_err=0, err_text=None):
        folder = self.get_system_folder()
        executable = "/exiftool" if self.system != 2 else "/exiftool.exe"
        working = folder + executable + " " + str(args)
        self.verbo_print("Working exiftool: %s" % working, 2)
        return self.command(working, ret_err, err_text)

    def get_system(self, spec=None):
        _platform = _platforms if spec is None else spec
        if _platform == "linux" or _platform == "linux2":
            self.system = 0
            self.verbo_print("Unix system detected... %s" % str(_platform), 2)
        elif _platform == "darwin":
            self.system = 1
            self.verbo_print("Darwin system detected... %s" % str(_platform), 2)
        elif _platform == "win32":
            self.system = 2
            self.verbo_print("Windows system detected... %s" % str(_platform), 2)
        else:
            self.system = None
            self.report_error("%s system is not supported" % str(_platform))

        if self.system is not None:
            self.verbo_print("Collected system information", 1, True)

        return self.system
