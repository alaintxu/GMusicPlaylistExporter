#!/usr/bin/env python
'''
Created on May 2, 2013

@author: aperez
'''
import sys
import re
from PyQt4 import QtGui
from PyQt4 import QtCore
import sqlite3 as lite
import subprocess
from mutagen.id3 import ID3,TIT2
from mutagen.easyid3 import EasyID3

class GMPE(object):
    musicdbpath     =   "/data/data/com.google.android.music/databases/music.db"
    #musicfolder     =   "/storage/external_SD/Android/data/com.google.android.music/files/music"
    musicfolder     =   "/data/data/com.google.android.music/files/music"
    musicfolder2     =   "/sdcard/Android/data/com.google.android.music/files/music"
    playlists       =   {}
    special_characters    =    '[:\/?]'
    GMPEdb_name        =    "gmpe.db"
    def __init__(self):
        self.androidSdkPath    =    "androidSdkPath"
        self.exportPath        =    "exportPath"
        GMPEdb            =    None
        try:
            query    =    '''
                    SELECT
                        name
                    FROM
                        sqlite_master
                    WHERE
                        type="table" AND 
                        name="variable";'''
            GMPEdb        =    lite.connect(self.GMPEdb_name)
            cur = GMPEdb.cursor()    
            cur.execute(query)
            result = cur.fetchone()
            if result==None:
                query    =    '''
                        CREATE TABLE
                            variable
                        (variable text primary key, value text)
                        '''
                cur.execute(query)
                print "'variable' table created!"
            print result
        except Exception as e:
            print e
        if GMPEdb:
            GMPEdb.close()
            
        self.androidSdkPath    =    self.getVariable("androidSdkPath")
        self.exportPath        =    self.getVariable("exportPath")
        self.playlists      =   {}
        pass

    def setAdbRoot(self):
        if self.androidSdkPath!="androidSdkPath":
            try:
                subprocess.call(['%s/platform-tools/adb' % (self.androidSdkPath),'root'])
            except Exception as e:
                print e
        pass
    def getMusicDB(self):
        self.androidSdkPath    =    self.getVariable("androidSdkPath");
        if self.androidSdkPath!="androidSdkPath":
            self.setAdbRoot()
            try:
                subprocess.call(["%s/platform-tools/adb"%(self.androidSdkPath),"pull",self.musicdbpath])
            except Exception as e:
                print e
        pass
    def remMusicDB(self):
        subprocess.call(["rm","music.db"])
        pass
    def getVariable(self,variable):
        GMPEdb    =    None
        ret    =    variable
        try:
            query    =    '''
                    SELECT
                        value
                    FROM
                        variable
                    WHERE
                        variable="%s"''' % (variable)
            GMPEdb        =    lite.connect(self.GMPEdb_name)
            cur = GMPEdb.cursor()    
            cur.execute(query)
            ret = cur.fetchone()
            print "getVariable(%s)" % (variable)
            if ret==None:
                ret=variable
            else:
                ret=ret[0]
        except Exception as e:
            print e
            ret    =    variable
        if GMPEdb:
            GMPEdb.close()
        print ret
        return ret
    def setVariable(self,variable,value):
        GMPEdb    =    None
        try:
            print "setVariable(%s,%s)" % (variable,value)
            GMPEdb        =    lite.connect(self.GMPEdb_name)
            cur = GMPEdb.cursor()
            item    =    [str(variable),str(value)]
            print item
            result    =    cur.execute("INSERT INTO variable (variable, value) VALUES(?,?)",item)
            GMPEdb.commit();
            print "result: "+str(result)
        except Exception as e:
            print "error: "+str(e)
        
        if GMPEdb:
            GMPEdb.close()
            
    def getPlaylistsFromMusicDB(self):
        con    =    None
        self.addThumbsUp()
        try:
            query   =   '''SELECT
                            l.name,
                            m.albumartist,
                            m.album,
                            m.TrackNumber,
                            m.title,
                            m.id,
                            m.year,
                            m.Rating
                FROM music as m
                JOIN listitems as li ON li.MusicId = m.id
                        JOIN lists as l ON li.listid = l.id
                        WHERE l.ListType=0
                        ORDER BY l.id, m.id;'''
            con = lite.connect('music.db')
            cur = con.cursor()    
            cur.execute(query)
            rows = cur.fetchall()
            
        
            for row in rows:
                
                if not row[0].encode('utf8') in self.playlists:
                    self.playlists[re.sub(self.special_characters, '', row[0])]    =   []
                song    =   {}
                
                
                song['albumartist'] = re.sub(self.special_characters, '', row[1])
                song['album']       = re.sub(self.special_characters, '', row[2])
                song['tracknumber'] = row[3]
                song['title']       = re.sub(self.special_characters, '', row[4])
                song['id']          = row[5]
                song['year']        = row[6]
                self.playlists[row[0]].append(song)
            if con:
                con.close()
            return self.playlists
        except Exception as e:
        
            if con:
                con.close()
            print "Unable to get playlist from music.db"
            print e
            return None
            
    def addThumbsUp(self):
        con    =    None
        try:
            
            self.playlists[u'ThumbsUp']    =    []
            query   =   '''SELECT
                            m.albumartist,
                            m.album,
                            m.TrackNumber,
                            m.title,
                            m.id,
                            m.year,
                            m.Rating
                FROM music as m
                        WHERE m.Rating=5
                        ORDER BY m.albumartist, m.year,m.album,m.TrackNumber;'''
            con = lite.connect('music.db')
            cur = con.cursor()    
            cur.execute(query)
            rows = cur.fetchall()
            
        
            for row in rows:
                song    =   {}
                
                song['albumartist'] = re.sub(self.special_characters, '', row[0])
                song['album']       = re.sub(self.special_characters, '', row[1])
                song['tracknumber'] = row[2]
                song['title']       = re.sub(self.special_characters, '', row[3])
                song['id']          = row[4]
                song['year']        = row[5]
                self.playlists[u'ThumbsUp'].append(song)
            if con:
                con.close()
        except Exception as e:
            print "Unable to add ThumbsUp playlist"
            if con:
                con.close()

    def createDirectory(self,path):
        subprocess.call(["mkdir","%s" % (path)])
        pass
    def copySong(self,plPath,song,i):
        original_song_path    = "%s/%d.mp3" % (self.musicfolder,song['id'])
        song_path        = "%s/%d-%s.mp3" % (plPath,i,song['title'])
        output  =   subprocess.call(
             ["%s/platform-tools/adb" % (self.androidSdkPath),
             "pull",
             original_song_path,
             song_path]
        )
        
        self.addID3Tag(song_path,song)
        if output==1:
            print "Problems on copySong\noriginal_song_path: %s\nsong_path: %s\n\n" % (original_song_path,song_path)
            if i==1 and not self.musicfolder==self.musicfolder2:
                self.musicfolder    =   self.musicfolder2
                print "changed device music folder"
                self.copySong(plPath,song,i)
    def addID3Tag(self,song_path,song):
        print song_path
        try:
            tags = ID3()
            tags.add(TIT2(encoding=3, text=u"An example"))
            tags.save(song_path)

            audio = EasyID3(song_path)
            audio["title"]        = song['title']
            audio["album"]        = song['album']
            audio["artist"]        = song['albumartist']
            audio["date"]        = unicode(song['year'])
            audio["tracknumber"]    = unicode(song['tracknumber'])
            audio.save()
        except Exception as e:
                print e
class ExportThread(QtCore.QThread):
    def __init__(self,parent):
        QtCore.QThread.__init__(self, parent)
    def setPlaylists(self,playlists):
        self.playlists  =   playlists
    def setSelected(self,selected):
        self.selected   =   selected
    def setGMPE(self,gmpe):
        self.gmpe       =   gmpe
    def run (self):
        for plname in self.selected:
            playlist    =   self.playlists[plname]
            self.emit(QtCore.SIGNAL("copyNewPlaylist"))
            playlistPath    =  "%s/%s" % (self.gmpe.getVariable("exportPath"),plname) 
            self.gmpe.createDirectory(playlistPath)
            i   =   1
            for song in playlist:
                self.emit(QtCore.SIGNAL("copyNewSong"))
                self.gmpe.copySong(playlistPath,song,i)
                i+=1
            self.emit(QtCore.SIGNAL('allSongsFinished'))
        self.emit(QtCore.SIGNAL('allFinished'))
class UserInterface(QtGui.QMainWindow):
    gmpe            =   None
    playlists       =   {}
    def __init__(self):
        super(UserInterface, self).__init__()
        self.gmpe   =   GMPE()
        
        self.initUI()
        self.thread = ExportThread(self)
        self.connect(self.thread, QtCore.SIGNAL('copyNewPlaylist'),
                     self.handleCopyNewPlaylist)
        self.connect(self.thread, QtCore.SIGNAL('copyNewSong'),
                     self.handleCopyNewSong)
        self.connect(self.thread, QtCore.SIGNAL('allSongsFinished'),
                     self.handleAllSongsFinished)
        self.connect(self.thread, QtCore.SIGNAL('allFinished'),
                     self.handleAllFinished)
        self.load_playlists()
        
    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('music-export.png'))
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
        self.sdklabel.setText(self.gmpe.getVariable("androidSdkPath"))
        self.sdklabel.setGeometry(15,15,350,25)
        
        self.sdkBrowseBtn = QtGui.QPushButton('Browse Android SDK folder', self)
        self.sdkBrowseBtn.setToolTip('Loads playlists from android device')
        self.sdkBrowseBtn.resize(self.sdkBrowseBtn.sizeHint())
        self.sdkBrowseBtn.clicked.connect(self.changeSDKFolder)
        self.sdkBrowseBtn.move(230, 15)
        
        self.exportlabel = QtGui.QLabel(self)
        self.exportlabel.setText(self.gmpe.getVariable("exportPath"))
        self.exportlabel.setGeometry(15,40,350,25)
        
        self.exportBrowseBtn = QtGui.QPushButton('Browse output folder', self)
        self.exportBrowseBtn.setToolTip('Loads playlists from android device')
        self.exportBrowseBtn.resize(self.exportBrowseBtn.sizeHint())
        self.exportBrowseBtn.clicked.connect(self.changeExportFolder)
        self.exportBrowseBtn.move(230, 40)
        
        self.reloadPlaylistsBtn    =    QtGui.QPushButton('Reload Playlists',self)
        self.reloadPlaylistsBtn.resize(self.reloadPlaylistsBtn.sizeHint())
        self.reloadPlaylistsBtn.clicked.connect(self.reload_playlists)
        self.reloadPlaylistsBtn.move(180, 70)
        
        
        self.list   =   QtGui.QListWidget(self)
        self.list.setSelectionMode(QtGui.QAbstractItemView.MultiSelection);
        self.list.setGeometry(15,100,450,235)
        
        self.exportBtn = QtGui.QPushButton('Export Selected Playlists', self)
        self.exportBtn.setEnabled(0)
        self.exportBtn.setToolTip('Exports playlists from android device')
        self.exportBtn.resize(self.exportBtn.sizeHint())
        self.exportBtn.clicked.connect(self.export_playlists)
        self.exportBtn.move(15, 345)
        
        self.cancelBtn = QtGui.QPushButton('Cancel exporting', self)
        self.cancelBtn.setEnabled(0)
        self.cancelBtn.setToolTip('Cancels exporting thread')
        self.cancelBtn.resize(self.cancelBtn.sizeHint())
        self.cancelBtn.clicked.connect(self.cancel_exporting)
        self.cancelBtn.move(200, 345)
        
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
            if not self.gmpe == None:
                self.gmpe.remMusicDB()
            event.accept()
        else:
            event.ignore()
    def changeSDKFolder(self):
        androidSdkPath = QtGui.QFileDialog.getExistingDirectory(self, 'Select SDK folder')
        self.gmpe.setVariable("androidSdkPath",androidSdkPath)
        self.sdklabel.setText(androidSdkPath)
        self.load_playlists()
    def changeExportFolder(self):
        exportPath    =    QtGui.QFileDialog.getExistingDirectory(self, 'Select Export folder')
        self.gmpe.setVariable("exportPath",exportPath)
        self.exportlabel.setText(exportPath)
        self.exportBtn.setEnabled(1)
    def reload_playlists(self):
        self.load_playlists()
    def load_playlists(self):
        androidSdkPath    =    self.gmpe.getVariable("androidSdkPath")
        if androidSdkPath!="androidSdkPath":

            # Create and display the splash screen
            splash_pix = QtGui.QPixmap('loading.gif')
            splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
            splash.setMask(splash_pix.mask())
            splash.show()

            
            self.gmpe.getMusicDB()
            self.playlists   =   self.gmpe.getPlaylistsFromMusicDB()
            self.list.clear()
            if not self.playlists==None:
                for plname,playlist in self.playlists.items():
                    print "Playlist:%s\nNofSongs:%d\n\n" % (plname,len(playlist))
                    item    =   QtGui.QListWidgetItem(plname)
                    self.list.addItem(item)
                self.list.show()
            else:
                QtGui.QMessageBox.question(self,'Error','Device not found or no playlist available',QtGui.QMessageBox.Ok)
                splash.finish(self)
    def export_playlists(self):
        self.selected    =   []
        for item in self.list.selectedItems():
            self.selected.append(str(item.text()))
        if len(self.selected)==0:
            QtGui.QMessageBox.question(self,'Error','Please, select the playlist(s) you want to export',QtGui.QMessageBox.Ok)
        else:
            self.i=0
            self.j=0
            self.thread.setSelected(self.selected)
            self.thread.setPlaylists(self.playlists)
            self.thread.setGMPE(self.gmpe)
            self.cancelBtn.setEnabled(1)
            self.exportBtn.setEnabled(0)
            self.thread.terminate()
            self.thread.start()
    def cancel_exporting(self):
        self.cancelBtn.setEnabled(0)
        self.thread.terminate()
        self.pllabel.setText("Cancelled")
        self.plpbar.setValue(0)
        self.slabel.setText("Cancelled")
        self.spbar.setValue(0)
        self.exportBtn.setEnabled(1)
    def handleCopyNewPlaylist(self):
        currentPlaylistName =   self.selected[self.i]
        nofplaylists        =   len(self.selected)
        self.pllabel.setText("%s %d/%d" % (currentPlaylistName,self.i+1,nofplaylists))
        self.plpbar.setValue(100*self.i/nofplaylists)
    def handleCopyNewSong(self):
        currentPlaylistName =   self.selected[self.i]
        currentPlaylist     =   self.playlists[currentPlaylistName.encode('utf8')]
        nofsongs            =   len(currentPlaylist)
        song                =   currentPlaylist[self.j]
        self.slabel.setText("%s %d/%d" % (song['title'],self.j+1,len(currentPlaylist)))
        self.spbar.setValue(100*self.j/nofsongs)
        self.j+=1
    def handleAllSongsFinished(self):
        self.slabel.setText("Finished")
        self.spbar.setValue(100)
        self.j = 0
        self.i+=1
    def handleAllFinished(self):
        self.pllabel.setText("Finished")
        self.plpbar.setValue(100)
        self.cancelBtn.setEnabled(0)
        self.exportBtn.setEnabled(1)
        self.i = 0
def main():
    app = QtGui.QApplication(sys.argv)
    ex = UserInterface()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
    pass
