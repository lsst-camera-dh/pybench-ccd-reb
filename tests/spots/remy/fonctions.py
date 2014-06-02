# Fonctions pour faire le focus et manipuler des images

def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments """
    data = data + 0.0000000000000001
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    col = data[:, int(y)]
    col_sum = col.sum()

    if col_sum == 0:
        col_sum = 0.00000000000000001

    width_x = sqrt(abs((np.arange(col.size)-y)**2*col).sum()/col_sum)
    row = data[int(x), :]
    row_sum = row.sum()

    if row_sum == 0:
        row_sum = 0.00000000000000001

    width_y = sqrt(abs((np.arange(row.size)-x)**2*row).sum()/row_sum)
    height = data.max()
    return height, x, y, width_x, width_y

def fitgaussian(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: ravel(gaussian(*p)(*np.indices(data.shape)) - data)
    p, success = opt.optimize.leastsq(errorfunction, params)
    
    return p

def CUTS(data): #On coupe l'image pour ne garder que la region central

    lines = np.shape(data)[0]
    rows = np.shape(data)[1]

    down = 15
    up = 17
    div = 30

    x_min_cut = down*rows/div
    y_min_cut = down*lines/div

    x_max_cut = up*rows/div
    y_max_cut = up*lines/div

    cuts = data[y_min_cut:y_max_cut,x_min_cut:x_max_cut]

    return cuts

def PF(cuts, max_i): # Obtient le flux dans les pixels voisin sous la forme [SUD,OUEST,EST,NORD]
    pixels_flux = [cuts[max_i[0] - 1][max_i[1]], cuts[max_i[0]][max_i[1] -1], cuts[max_i[0]][max_i[1] + 1], cuts[max_i[0] + 1][max_i[1]]]

    return pixels_flux

def PCF(cuts, max_i):
    pcf = cuts[max_i[0]][max_i[1]]
    
    return pcf

def RATIO(pixels_flux, nb_flux, pixel_central_flux):
    ratio = float(pixels_flux[3])/pixel_central_flux
    
    return ratio

def FOCUS(interval=0.005, pas=0.001, expo = 0.05, trou = "20micron"):
    ''' Fait le focus pour un interval, un pas et un trou donne.
    Attention : moteurs et camera doivent etre initialises
    @param interval: autour d'un point d'origine, distance avant et apres ce point sur laquelle travailler
    @param pas: pas de prise d'image, doit etre inferieur a interval
    @param trou: trou de travail
    @param expo: temps d'exposition desire
    
    '''
    borne = int(interval/pas)

    print("Attention : voulez vous supprimer le contenu de ./focus (y/n) ? : ")
    suppr = input()

    if suppr == 'y':
        commande = "rm -f ./focus/*.fits"
        os.system(commande)

    mov.move(dy=-interval)
    
    for i in range(0,2*borne):

        XPOS = mov.x_axis.get_position()
        YPOS = mov.y_axis.get_position()
        ZPOS = mov.z_axis.get_position()

        mov.move(dy=pas)
        name = "./focus/" + str(time.time()) + "_" + trou 
        cam.capture_and_save(exposure = expo, filename = name, filetype = "FITS")

        update = py.open(name)
        update[0].header.update('xpos', XPOS)
        update[0].header.update('ypos', YPOS)
        update[0].header.update('zpos', ZPOS)
        update.close()

def VKE(interval = 0.02, pas = 0.0002, sens = "z", expo = 0.05 trou = "20micron"):
    '''Deplace le spot verticalement ou horizontalement, et prend une image a chaque pas
    @param interval: distance sur laquelle faire l'aller et le retour en mm
    @param pas: division de l'interval de travail, doit etre inferieur a interval en mm
    @param sens: horizontal (x) ou vertical (z)
    @param trou: trou de travail
    @param expo: temps d'exposition desire en seconde
    '''
    borne = int(interval/pas)

    print("Attention : voulez vous supprimer le contenu de ./vke_beta (y/n) ? : ")
    suppr = input()

    if suppr == 'y':
        commande = "rm -f ./vke_beta/*.fits"
        os.system(commande)

    if sens == "z":
        for i in range(0,borne):

            ZPOS = mov.z_axis.get_position()

            name = "./vke_beta/aller_z_" + str(time.time()) + "_z=" + str(ZPOS) + "_" + trou 
            cam.capture_and_save(exposure = expo, filename = name, filetype = "FITS")
            mov.move(dz=pas)

            update = py.open(name)
            update[0].header.update('zpos', ZPOS)
            update.close()

        for i in range(0,borne):

            ZPOS = mov.z_axis.get_position()

            mov.move(dz=-pas)
            name = "./vke_beta/retour_z_" + str(time.time()) + "_z=" + str(ZPOS) + "_" + trou
            cam.capture_and_save(exposure = expo, filename = name , filetype = "FITS")

            update = py.open(name)
            update[0].header.update('zpos', ZPOS)
            update.close()

    elif sens == "x":
        for i in range(0,borne):

            XPOS = mov.x_axis.get_position()

            name = "./vke_beta/aller_x_" + str(time.time()) + "_x=" + str(XPOS) + "_" + trou 
            cam.capture_and_save(exposure = expo, filename = name, filetype = "FITS")
            mov.move(dx=pas)

            update = py.open(name)
            update[0].header.update('xpos', XPOS)
            update.close()

        for i in range(0,borne):

            XPOS = mov.x_axis.get_position()

            mov.move(dx=-pas)
            name = "./vke_beta/retour_x_" + str(time.time()) + "_x=" + str(XPOS) + "_" + trou
            cam.capture_and_save(exposure = expo, filename = name , filetype = "FITS")

            update = py.open(name)
            update[0].header.update('xpos', XPOS)
            update.close()
