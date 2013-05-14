#!/usr/bin/env python
'''
Created on May 2, 2013

@author: aperez
'''
import sys
from PyQt4 import QtGui
import sqlite3 as lite
import commands
class GMPE(object):
    musicdbpath     =   "/data/data/com.google.android.music/databases/music.db"
    musicfolder     =   "/data/data/com.google.android.music/files/music"
    playlists       =   {}
    def __init__(self,androidSdkPath,exportPath):
        self.androidSdkPath =   androidSdkPath
        self.exportPath     =   exportPath
        self.playlists      =   {}
        pass

    def getMusicDB(self):
        command =   '%s/platform-tools/adb pull %s' % (self.androidSdkPath,self.musicdbpath);
        output = commands.getoutput(command)
        print output
        pass
    def remMusicDB(self):
        command =   'rm music.db';
        output = commands.getoutput(command)
        print output
        pass
    def getPlaylistsFromMusicDB(self):
        try:
            query   =   '''SELECT
                            l.name,
                            m.albumartist,
                            m.album,
                            m.TrackNumber,
                            m.title,
                            m.id
                        FROM listitems as li
                        JOIN music as m ON li.musicsourceid = m.SourceId
                        JOIN lists as l ON li.listid = l.id
                        WHERE l.ListType=0
                        ORDER BY l.id, li.id;'''
            con = lite.connect('music.db')
            cur = con.cursor()    
            cur.execute(query)
            rows = cur.fetchall()
        
            for row in rows:
                if not row[0].encode('utf8') in self.playlists:
                    self.playlists[row[0].encode('utf8')]    =   []
                song    =   {}
                
                song['albumartist'] = row[1]
                song['album']       = row[2]
                song['tracknumber'] = row[3]
                song['title']       = row[4]
                song['id']          =   row[5]
                self.playlists[row[0]].append(song)
            return self.playlists
        except Exception as e:
            return None

    def createDirectory(self,path):
        command =   'mkdir "%s"' % (path)
        output = commands.getoutput(command)
        print output
        pass
    def copySong(self,plPath,song,i):
        command =   '%s/platform-tools/adb pull %s/%d.mp3 "%s/%d-%s.mp3"' % (self.androidSdkPath,self.musicfolder,song['id'],plPath,i,song['title']);
        output = commands.getoutput(command)
        print output

class UserInterface(QtGui.QMainWindow):
    
    androidSdkPath  =   "Select android SDK folder"
    exportPath      =   "Select export folder"
    gmpe            =   None
    playlists       =   {}
    def __init__(self):
        super(UserInterface, self).__init__()
        
        self.initUI()
        
    def initUI(self):
        changeSDK = QtGui.QAction('Change SDK folder', self)
        changeSDK.setStatusTip('Change SDK folder')
        changeSDK.triggered.connect(self.changeSDKFolder)
        
        
        changeExport = QtGui.QAction('Change Export folder', self)
        changeExport.setStatusTip('Change Export folder')
        changeExport.triggered.connect(self.changeExportFolder)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Change folders')
        fileMenu.addAction(changeSDK)    
        fileMenu.addAction(changeExport)    
        
        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        
        self.sdklabel = QtGui.QLabel(self)
        self.sdklabel.setText(self.androidSdkPath)
        self.sdklabel.setGeometry(15,15,350,25)
        
        self.sdkBrowseBtn = QtGui.QPushButton('Browse Android SDK folder', self)
        self.sdkBrowseBtn.setToolTip('Loads playlists from android device')
        self.sdkBrowseBtn.resize(self.sdkBrowseBtn.sizeHint())
        self.sdkBrowseBtn.clicked.connect(self.changeSDKFolder)
        self.sdkBrowseBtn.move(230, 15)
        
        self.exportlabel = QtGui.QLabel(self)
        self.exportlabel.setText(self.exportPath)
        self.exportlabel.setGeometry(15,40,350,25)
        
        self.exportBrowseBtn = QtGui.QPushButton('Browse output folder', self)
        self.exportBrowseBtn.setToolTip('Loads playlists from android device')
        self.exportBrowseBtn.resize(self.exportBrowseBtn.sizeHint())
        self.exportBrowseBtn.clicked.connect(self.changeExportFolder)
        self.exportBrowseBtn.move(230, 40)
        
        self.list   =   QtGui.QListWidget(self)
        self.list.setSelectionMode(QtGui.QAbstractItemView.MultiSelection);
        self.list.setGeometry(15,100,450,235)
        
        self.exportBtn = QtGui.QPushButton('Export Selected Playlists', self)
        self.exportBtn.setEnabled(0)
        self.exportBtn.setToolTip('Exports playlists from android device')
        self.exportBtn.resize(self.exportBtn.sizeHint())
        self.exportBtn.clicked.connect(self.export_playlists)
        self.exportBtn.move(15, 345)
        
        self.pllabel = QtGui.QLabel(self)
        self.pllabel.setText("Waiting")
        self.pllabel.setGeometry(15,375,450,25)
        self.plpbar = QtGui.QProgressBar(self)
        self.plpbar.setGeometry(15, 400, 450, 25)
        
        self.slabel = QtGui.QLabel(self)
        self.slabel.setText("Waiting")
        self.slabel.setGeometry(15,425,450,25)
        self.spbar = QtGui.QProgressBar(self)
        self.spbar.setGeometry(15, 450, 450, 25)
        
        
        self.resize(500, 500)
        self.setWindowTitle('GMusic Playlist Exporter')
        self.center()    
    
        self.show()
    def center(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def closeEvent(self, event):
        
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.gmpe.remMusicDB()
            event.accept()
        else:
            event.ignore()
    def changeSDKFolder(self):
        self.androidSdkPath = QtGui.QFileDialog.getExistingDirectory(self, 'Select SDK folder')
        self.sdklabel.setText(self.androidSdkPath)
        self.load_playlists()
    def changeExportFolder(self):
        self.exportPath = QtGui.QFileDialog.getExistingDirectory(self, 'Select Export folder')
        self.exportlabel.setText(self.exportPath)
        self.exportBtn.setEnabled(1);
    def load_playlists(self):
        self.gmpe   =   GMPE(self.androidSdkPath,self.exportPath)
        self.gmpe.getMusicDB()
        self.playlists   =   self.gmpe.getPlaylistsFromMusicDB()
        self.list.clear()
        if not self.playlists==None:
            for plname,playlist in self.playlists.items():
                item    =   QtGui.QListWidgetItem(plname)
                self.list.addItem(item)
            self.list.show()
        else:
            QtGui.QMessageBox.question(self,'Error','Device not found or no playlist available',QtGui.QMessageBox.Ok)
            
    def export_playlists(self):
        ret={}
        ret['ok']   =   0
        ret['wrong']=   0
        nofplaylists    =   len(self.list.selectedItems())
        i_pl        =   1
        
        selected    =   []
        for item in self.list.selectedItems():
            selected.append(item.text())
            
        for plname,playlist in self.playlists.items():
            if plname in selected:
                self.pllabel.setText("%d/%d - %s" % (i_pl,nofplaylists,plname))
                self.plpbar.setValue(100*(i_pl-1)/nofplaylists)
                playlistPath    =  "%s/%s" % (self.gmpe.exportPath,plname) 
                self.gmpe.createDirectory(playlistPath)
                nofsongs    =   len(playlist)
                i   =   1
                for song in playlist:
                    self.slabel.setText("%d/%d - %s" % (i,nofsongs,song['title']))
                    self.spbar.setValue(100*(i-1)/nofsongs)
                    self.gmpe.copySong(playlistPath,song,i)
                    i+=1
                self.spbar.setValue(100)
                i_pl+=1
        
        self.plpbar.setValue(100)
        self.pllabel.setText("Finished")
        self.slabel.setText("Finished")
        pass

def main():
    app = QtGui.QApplication(sys.argv)
    ex = UserInterface()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
    pass