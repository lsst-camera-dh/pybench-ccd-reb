import dmk41au02as as d

cam = d.Camera()
cam.open()
cam.capture_and_save(exposure = 1, filename = "20micron", filetype = "FITS")
