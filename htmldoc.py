import os

htmldir = '../doc/code'

listfile = [os.path.join(htmldir, htmlfile)
            for htmlfile in os.listdir(htmldir) if os.path.splitext(htmlfile)[1] == '.html']

for htmlfile in listfile:
    filetext = open(htmlfile, 'r')
    print htmlfile
    htmlstr = filetext.read()
    filetext.close()
    htmlstr = htmlstr.replace('/Users/nayman/Developer/lsst/', '../../')
    filetext = open(htmlfile, 'w')
    filetext.write(htmlstr)
    filetext.close()