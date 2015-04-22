#!/usr/bin/env python

import sys
import os, os.path
import subprocess
import time

wmctrl  = "/usr/bin/wmctrl"
wmsetbg = "/usr/bin/wmsetbg"


def getdesktops():
      s = subprocess.check_output([wmctrl, "-d"])
      lines = s.splitlines()
      
      desktops = {}

      for line in lines:
            # A remplacer par une regexp
            elts = line.split()

            desktop_id = int(elts[0])

            wgeom  = elts[3]
            welts = wgeom.split('x')
            wx = int(welts[0])
            wy = int(welts[1])
            
            # dgeom = elts[5]
            # delts = dgeom.split('x')
            # dx = int(delts[0])
            # dy = int(delts[1])
            
            # print wx, wy #, dx, dy
            
            # For an unknown reason wx,wy are not multiple of dx,dy
            # nx = wx/dx
            # vx = wx/nx
            
            # ny = wy/dy
            # vy = wy/ny
            
            # print nx, ny, vx, vy
            
            # wx,wy = whole geometry
            # vx,vy = viewport geometry
            # nx,ny = number of virtual screens

            desktops[desktop_id] = { 
                  'id': desktop_id,
                  'wx': wx,
                  'wy': wy,
                  # 'vx': vx,
                  # 'vy': vy,
                  # 'nx': nx,
                  # 'ny': ny,
                  'title': " ".join(elts[8:]) }
            
      return desktops

def setndesktop(n):
      """
      Set the number of desktop to <n>.
      """
      s = subprocess.call([wmctrl, "-n", "%d" % n])
            
                        
def setbackground(desktop, imagefile):
      """
      Set the wallpaper for desktop <desktop>.
      """
      s = subprocess.call([wmsetbg, "-w", "%d" % desktop, 
                           imagefile])


def getwindows():
      """
      Return the list of all windows
      """
      s = subprocess.check_output([wmctrl, "-l", "-G", "-p"])
      
      # 0x0260000a  0 2510   0    0    1366 768  lpnlp171 Bureau
      # 0x0340000c  0 2486   -420 -300 320  200  lpnlp171 Hud
      # 0x02c000ab  0 3258   610  52   756  707  lpnlp171 emacs@lpnlp171
      
      wins = []
      lines = s.split('\n')
      
      for line in lines:
            parts = line.split()
            if len(parts) < 9:
                  continue
            winid = parts[0]
            desktop = parts[1]
            pid = int(parts[2])
            x = int(parts[3])
            y = int(parts[4])
            w = int(parts[5])
            h = int(parts[6])
            host = parts[7]
            title = " ".join(parts[8:])

            win = {'winid': winid,
                   'desktop': desktop,
                   'pid': pid,
                   'x': x,
                   'y': y,
                   'w': w,
                   'h': h,
                   'host': host,
                   'title': title}
            wins.append(dict(win))

      return wins

      
def findwindow(pid):
      wins = getwindows()
      for win in wins:
            if win['pid'] == pid:
                  return win
      return None


def movewindow(winid, 
               desktop=None,
               x=None, y=None, w=None, h=None):
      """
      Move the window of id <winid> to desktop <desktop>
      at the specified position.
      """

      if x  == None: x = -1
      if y  == None: y = -1
      if w  == None: w = -1
      if h  == None: h = -1


      s = subprocess.call([wmctrl, "-i", 
                           "-r", winid, 
                           "-e", "0,%d,%d,%d,%d" % (x,y,w,h)])
            
      if desktop != None:
            s = subprocess.call([wmctrl, "-i", 
                                 "-r", winid, 
                                 "-t", "%d" % desktop])
            

def switch(desktop):
      """
      Switch to desktop <desktop>
      """

      s = subprocess.call([wmctrl, "-s", "%d" % desktop])


def launch(program, args=[], 
           desktop=None, 
           x=None, y=None, w=None, h=None):
      """
      Run program <program>, and move its window 
      on desktop <desktop> at the specified position.
      
      example:
      WM.launch("xclock", ["-bg", "black"], 2, 100, 200, 250, 450)
      
      """

      arguments = [program]
      if args:
            arguments.extend(args)
      print arguments
      pid = subprocess.Popen(arguments).pid

      # print pid

      time.sleep(0.5)

      # Find the window for this pid
      
      win = findwindow(pid)
      if win == None:
            print >> sys.stderr, \
                  "Warning: Cannot find the resulting window."
            return

      winid = win['winid']
      movewindow(winid, desktop, x, y, w, h)


            
