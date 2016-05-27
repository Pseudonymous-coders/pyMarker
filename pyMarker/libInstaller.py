from systems import System

if __name__ == "__main__":
    print("py-water-marker depends installer")
    sys = System()
    sys.get_system()
    sys.verbosity = 4
    src_folder = sys.get_src_folder()
    sys.verbo_print("Working folder %s" % str(src_folder), 1)
    if sys.system == 0:  # Unix
        unix_work = "%s/linux/" % src_folder
        code, stream = sys.command('printf "\n\n\n" | sudo add-apt-repository ppa:mc3man/trusty-media')
        if not code and "HANDLE" != stream:
            sys.verbo_print("Error(%d): %s" % (int(code), stream), 1)
            print("Failed the installation please manually install ffmpeg")
        code, stream = sys.command('printf "\n\n\n" | sudo apt-get update;printf "\n\n\n" | ' +
                                   'sudo apt-get dist-upgrade;printf "\n\n\n" | sudo apt-get install ffmpeg')
        if not code and "HANDLE" != stream:
            sys.verbo_print("Error(%d): %s" % (int(code), stream), 1)
            print("Failed the installation please manually install ffmpeg")
