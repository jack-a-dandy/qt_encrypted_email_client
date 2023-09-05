#!/usr/bin/python3
# -- coding: utf-8 --
from PyQt5.QtWidgets import QTextEdit, QWidget, QDialog, QVBoxLayout, QApplication, QFileDialog, QMessageBox, QHBoxLayout, \
                         QToolBar, QComboBox, QAction, QLineEdit, QMenu, QMainWindow, QActionGroup, \
                        QFontComboBox, QColorDialog, QInputDialog, QPushButton, QPlainTextEdit
from PyQt5.QtGui import QIcon, QPainter, QTextFormat, QColor, QTextCursor, QKeySequence, QClipboard, \
                        QTextCharFormat, QTextCharFormat, QFont, QPixmap, QFontDatabase, QFontInfo, QTextDocumentWriter, \
                        QImage, QTextListFormat, QTextBlockFormat, QTextDocumentFragment, QKeyEvent
from PyQt5.QtCore import Qt, QDir, QFile, QFileInfo, QTextStream, QSettings, QTextCodec, QSize, QMimeData, QUrl, QSysInfo, QEvent
from PyQt5 import QtPrintSupport
import sys, os, webbrowser

tab = "\t"
eof = "\n"
tableheader2 = "<table></tr><tr><td>    Column1    </td><td>    Column2    </td></tr></table>"
tableheader3 = "<table></tr><tr><td>    Column1    </td><td>    Column2    </td><td>    Column3    </td></tr></table>"

class htmlEditor(QWidget):
    def __init__(self, parent = None, text = ""):
        super(htmlEditor, self).__init__(parent)
        
        self.ed = QPlainTextEdit()
        self.btnOK = QPushButton("OK", clicked=self.sendText)
        self.btnCancel = QPushButton("Cancel", clicked=self.cancelAction)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.btnCancel)
        self.hbox.addWidget(self.btnOK)
        
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.ed)
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)
        #self.ed.setPlainText(text)
        
    def sendText(self):
        return self.ed.toPlainText()
        
    def cancelAction(self):
        self.close()

class myEditor(QMainWindow):
    def __init__(self, parent = None):
        super(myEditor, self).__init__(parent)
#    def keyPressEvent(self, event):
#        if event.key() == Qt.Key_Tab:
#            print ("tab pressed")
        self.setStyleSheet(myStyleSheet(self))
        self.MaxRecentFiles = 5
        self.windowList = []
        self.recentFileActs = []
        self.mainText = " "
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Editor Widget ...
#        QIcon.setThemeName('gnome')
        self.editor = QTextEdit() 

        self.editor.setStyleSheet(myStyleSheet(self))
        self.editor.setTabStopWidth(14)
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.contextMenuRequested)        
        self.createActions()
        self.createTollbarActions()
        self.createToolbar()
        self.createMenubar()

    def createTollbarActions(self):
        self.repAllAct = QPushButton("replace all") 
        self.repAllAct.setIcon(QIcon.fromTheme("gtk-find-and-replace"))
        self.repAllAct.setStatusTip("replace all")
        self.repAllAct.clicked.connect(self.replaceAll)
        self.bgAct = QAction("change Background Color",self,  triggered=self.changeBGColor)
        self.bgAct.setStatusTip("change Background Color")
        self.bgAct.setIcon(QIcon.fromTheme("preferences-color-symbolic"))

    def createToolbar(self):        
        ### find / replace toolbar
        self.edit_tb = QToolBar(self)
        self.edit_tb.setIconSize(QSize(16, 16))
        self.edit_tb.setWindowTitle("Find Toolbar")   
        self.findfield = QLineEdit()
        self.findfield.addAction(QIcon.fromTheme("gtk-find"), 0)
        self.findfield.setClearButtonEnabled(True)
        self.findfield.setFixedWidth(200)
        self.findfield.setPlaceholderText("find")
        self.findfield.setStatusTip("press RETURN to find")
        self.findfield.setText("")
        self.findfield.returnPressed.connect(self.findText)
        self.edit_tb.addWidget(self.findfield)
        self.replacefield = QLineEdit()
        self.replacefield.addAction(QIcon.fromTheme("gtk-find-and-replace"), 0)
        self.replacefield.setClearButtonEnabled(True)
        self.replacefield.setFixedWidth(200)
        self.replacefield.setPlaceholderText("replace with")
        self.replacefield.setStatusTip("press RETURN to replace the first")
        self.replacefield.returnPressed.connect(self.replaceOne)
        self.edit_tb.addSeparator() 
        self.edit_tb.addWidget(self.replacefield)
        self.edit_tb.addSeparator()
        self.edit_tb.addWidget(self.repAllAct)
        self.edit_tb.addSeparator()
        self.edit_tb.addAction(self.bgAct)
        ### Format Toolbar
        self.format_tb = QToolBar(self)
        self.format_tb.setIconSize(QSize(16, 16))
        self.format_tb.setWindowTitle("Format Toolbar")
        
        self.actionTextBold = QAction(QIcon.fromTheme('format-text-bold-symbolic'), "&Bold", self, priority=QAction.LowPriority,
                shortcut=Qt.CTRL + Qt.Key_B, triggered=self.textBold, checkable=True)
        self.actionTextBold.setStatusTip("bold")
        bold = QFont()
        bold.setBold(True)
        self.actionTextBold.setFont(bold)
        self.format_tb.addAction(self.actionTextBold)    

        self.actionTextItalic = QAction(QIcon.fromTheme('format-text-italic-symbolic'), "&Italic", self, priority=QAction.LowPriority,
                shortcut=Qt.CTRL + Qt.Key_I, triggered=self.textItalic, checkable=True)
        italic = QFont()
        italic.setItalic(True)
        self.actionTextItalic.setFont(italic)
        self.format_tb.addAction(self.actionTextItalic)
        
        self.actionTextUnderline = QAction(QIcon.fromTheme('format-text-underline-symbolic'), "&Underline", self, priority=QAction.LowPriority,
                shortcut=Qt.CTRL + Qt.Key_U, triggered=self.textUnderline, checkable=True)
        underline = QFont()
        underline.setUnderline(True)
        self.actionTextUnderline.setFont(underline)
        self.format_tb.addAction(self.actionTextUnderline)
        
        self.format_tb.addSeparator()
        
        self.grp = QActionGroup(self, triggered=self.textAlign)

        if QApplication.isLeftToRight():
            self.actionAlignLeft = QAction(QIcon.fromTheme('format-justify-left-symbolic'),"&Left", self.grp)
            self.actionAlignCenter = QAction(QIcon.fromTheme('format-justify-center-symbolic'),"C&enter", self.grp)
            self.actionAlignRight = QAction(QIcon.fromTheme('format-justify-right-symbolic'),"&Right", self.grp)
        else:
            self.actionAlignRight = QAction(QIcon.fromTheme('gtk-justify-right-symbolic'),"&Right", self.grp)
            self.actionAlignCenter = QAction(QIcon.fromTheme('gtk-justify-center-symbolic'),"C&enter", self.grp)
            self.actionAlignLeft = QAction(QIcon.fromTheme('format-justify-left-symbolic'),"&Left", self.grp)
 
        self.actionAlignJustify = QAction(QIcon.fromTheme('format-justify-fill-symbolic'),"&Justify", self.grp)

        self.actionAlignLeft.setShortcut(Qt.CTRL + Qt.Key_L)
        self.actionAlignLeft.setCheckable(True)
        self.actionAlignLeft.setPriority(QAction.LowPriority)

        self.actionAlignCenter.setShortcut(Qt.CTRL + Qt.Key_E)
        self.actionAlignCenter.setCheckable(True)
        self.actionAlignCenter.setPriority(QAction.LowPriority)

        self.actionAlignRight.setShortcut(Qt.CTRL + Qt.Key_R)
        self.actionAlignRight.setCheckable(True)
        self.actionAlignRight.setPriority(QAction.LowPriority)

        self.actionAlignJustify.setShortcut(Qt.CTRL + Qt.Key_J)
        self.actionAlignJustify.setCheckable(True)
        self.actionAlignJustify.setPriority(QAction.LowPriority)

        self.format_tb.addActions(self.grp.actions())

        #self.indentAct = QAction(QIcon.fromTheme("format-indent-more-symbolic"), "indent more", self, triggered = self.indentLine, shortcut = "F8")
#        self.indentLessAct = QAction(QIcon.fromTheme("format-indent-less-symbolic"), "indent less", self, triggered = self.indentLessLine, shortcut = "F9")
#        self.format_tb.addAction(self.indentAct)
#        self.format_tb.addAction(self.indentLessAct)
        
        pix = QPixmap(16, 16)
        pix.fill(Qt.black)
        self.actionTextColor = QAction(QIcon(pix), "TextColor...", self,
                triggered=self.textColor)
        self.format_tb.addSeparator()
        self.format_tb.addAction(self.actionTextColor)
        
        self.font_tb = QToolBar(self)
        self.font_tb.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        self.font_tb.setWindowTitle("Font Toolbar")
        
        self.comboStyle = QComboBox(self.font_tb)
        self.font_tb.addWidget(self.comboStyle)
        self.comboStyle.addItem("Standard")
        self.comboStyle.addItem("Bullet List (Disc)")
        self.comboStyle.addItem("Bullet List (Circle)")
        self.comboStyle.addItem("Bullet List (Square)")
        self.comboStyle.addItem("Ordered List (Decimal)")
        self.comboStyle.addItem("Ordered List (Alpha lower)")
        self.comboStyle.addItem("Ordered List (Alpha upper)")
        self.comboStyle.addItem("Ordered List (Roman lower)")
        self.comboStyle.addItem("Ordered List (Roman upper)")
        self.comboStyle.activated.connect(self.textStyle)

        self.comboFont = QFontComboBox(self.font_tb)
        self.font_tb.addSeparator()
        self.font_tb.addWidget(self.comboFont)
        self.comboFont.activated[str].connect(self.textFamily)

        self.comboSize = QComboBox(self.font_tb)
        self.font_tb.addSeparator()
        self.comboSize.setObjectName("comboSize")
        self.font_tb.addWidget(self.comboSize)
        self.comboSize.setEditable(True)

        db = QFontDatabase()
        for size in db.standardSizes():
            self.comboSize.addItem("%s" % (size))
        self.comboSize.addItem("%s" % (90))
        self.comboSize.addItem("%s" % (100))
        self.comboSize.addItem("%s" % (160))
        self.comboSize.activated[str].connect(self.textSize)
        self.comboSize.setCurrentIndex(
                self.comboSize.findText(
                        "%s" % (QApplication.font().pointSize())))     
        self.addToolBar(self.format_tb)    
#        self.addToolBarBreak(Qt.TopToolBarArea)
        self.addToolBar(self.font_tb)

    def msgbox(self,title, message):
        QMessageBox.warning(self, title, message)

    def indentLine(self):
        if not self.editor.textCursor().selectedText() == "":
            ot = self.editor.textCursor().selection().toHtml()
            self.msgbox("HTML", str(ot))
#            self.editor.textCursor().insertText(tab)
#            self.editor.textCursor().insertHtml(QTextDocumentFragment.toHtml(ot))
#            self.setModified(True)
        
    def indentLessLine(self):
        if not self.editor.textCursor().selectedText() == "":
            newline = u"\u2029"
            list = []
            ot = self.editor.textCursor().selectedText()
            theList  = ot.splitlines()
            linecount = ot.count(newline)
            for i in range(linecount + 1):
                list.insert(i, (theList[i]).replace(tab, "", 1))
            self.editor.textCursor().insertText(newline.join(list))
            self.setModified(True)    

    def createMenubar(self):        
        bar=self.menuBar()
#        bar.setStyleSheet(myStyleSheet(self))
        editmenu = bar.addMenu("Edit")
        editmenu.addAction(QAction(QIcon.fromTheme('edit-undo'), "Undo", self, triggered = self.editor.undo, shortcut = "Ctrl+u"))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-redo'), "Redo", self, triggered = self.editor.redo, shortcut = "Shift+Ctrl+u"))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('edit-copy'), "Copy", self, triggered = self.editor.copy, shortcut = QKeySequence.Copy))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-cut'), "Cut", self, triggered = self.editor.cut, shortcut = QKeySequence.Cut))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-paste'), "Paste", self, triggered = self.editor.paste, shortcut = QKeySequence.Paste))
        editmenu.addAction(QAction(QIcon.fromTheme('edit-delete'), "Delete", self, triggered = self.editor.cut, shortcut = QKeySequence.Delete))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('edit-select-all'), "Select All", self, triggered = self.editor.selectAll, shortcut = QKeySequence.SelectAll))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('edit-copy'), "grab selected line", self, triggered = self.grabLine))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('image'), "insert Image", self, triggered = self.insertImage))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "insert Table (2 Column)", self, triggered = self.insertTable))
        editmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "insert Table (3 Column)", self, triggered = self.insertTable3))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('text-html'), "convert from HTML", self, triggered = self.convertfromHTML, shortcut ="F10"))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('browser'), "insert Link", self, triggered = self.insertLink))
        editmenu.addAction(QAction(QIcon.fromTheme('browser'), "edit Link", self, triggered = self.editLink))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "edit body style", self, triggered = self.editBody))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "edit HTML (selected Text)", self, triggered = self.editHTML))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon.fromTheme('stock_calendar'), "insert Date", self, triggered = self.insertDate))
        editmenu.addAction(QAction(QIcon.fromTheme('stock_calendar'), "insert Time", self, triggered = self.insertTime))
        editmenu.addAction(QAction(QIcon.fromTheme('stock_calendar'), "insert Date && Time", self, triggered = self.insertDateTime))
        editmenu.addSeparator()
        editmenu.addAction(self.bgAct)

        self.formatMenu = QMenu("F&ormat", self)
        self.formatMenu.addAction(self.actionTextBold)
        self.formatMenu.addAction(self.actionTextItalic)
        self.formatMenu.addAction(self.actionTextUnderline)
        self.formatMenu.addSeparator()
        self.formatMenu.addActions(self.grp.actions())
        self.formatMenu.addSeparator()
        self.formatMenu.addAction(self.actionTextColor)
        bar.addMenu(self.formatMenu)
        # Laying out...
        layoutV = QVBoxLayout()
        layoutV.addWidget(self.edit_tb)
        layoutV.addWidget(self.editor)
        ### main window
        mq = QWidget(self)
        mq.setLayout(layoutV)
        self.setCentralWidget(mq)
        self.statusBar().showMessage("Welcome to RichTextEdit * ")
        # Event Filter ...
        self.installEventFilter(self)
        self.cursor = QTextCursor()
        self.editor.setTextCursor(self.cursor)
        
        self.editor.setPlainText(self.mainText)
        self.editor.moveCursor(self.cursor.End)
        self.editor.textCursor().deletePreviousChar()
        self.editor.document().modificationChanged.connect(self.setWindowModified)
        self.extra_selections = []
        self.fname = ""
        self.filename = ""
        self.editor.setFocus()
        self.setModified(False)
        self.fontChanged(self.editor.font())
        self.colorChanged(self.editor.textColor())
        self.alignmentChanged(self.editor.alignment())
        self.editor.document().modificationChanged.connect(
                self.setWindowModified)

        self.setWindowModified(self.editor.document().isModified())
        self.editor.setAcceptRichText(True)
        self.editor.currentCharFormatChanged.connect(
                self.currentCharFormatChanged)
        self.editor.cursorPositionChanged.connect(self.cursorPositionChanged)
#        QApplication.clipboard().dataChanged.connect(self.clipboardDataChanged)

    def insertDate(self):
        import time
        from datetime import date
        today = date.today().strftime("%A, %d.%B %Y")
        self.editor.textCursor().insertText(today)

    def insertTime(self):
        import time
        from datetime import date
        today = time.strftime("%H:%M Uhr")
        self.editor.textCursor().insertText(today)

    def insertDateTime(self):
        self.insertDate()
        self.editor.textCursor().insertText(eof)
        self.insertTime()
        self.editor.textCursor().insertText(eof)

    def changeBGColor(self):
        all = self.editor.document().toHtml()
        bgcolor = all.partition("<body style=")[2].partition(">")[0].partition('bgcolor="')[2].partition('"')[0]
        if not bgcolor == "":
            col = QColorDialog.getColor(QColor(bgcolor), self)
            if not col.isValid():
                return
            else:
                colorname = col.name()
                new = all.replace("bgcolor=" + '"' + bgcolor + '"', "bgcolor=" + '"' + colorname + '"')
                self.editor.document().setHtml(new)
        else:
            col = QColorDialog.getColor(QColor("#FFFFFF"), self)
            if not col.isValid():
                return
            else:
                all = self.editor.document().toHtml()
                body = all.partition("<body style=")[2].partition(">")[0]
                newbody = body + "bgcolor=" + '"' + col.name() + '"'
                new = all.replace(body, newbody)    
                self.editor.document().setHtml(new)

    def getHTML(self):
        all = self.editor.document().toHtml()
        clipboard = QApplication.clipboard()
        clipboard.setText(all)
        self.statusBar().showMessage("HTML is in clipboard")

    def editHTML(self):
        rtext = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body>""" + '\n'
        btext = """<!--EndFragment--></p></body></html>"""
        all = self.editor.textCursor().selection().toHtml()
        #dlg = QInputDialog(self, Qt.Window)

        #dlg.setOption(QInputDialog.UsePlainTextEditForTextInput, True)
        #new, ok = dlg.getMultiLineText(self, 'change HTML', "edit HTML", all.replace(rtext, ""))
        #if ok:
        #    self.editor.textCursor().insertHtml(new)
        #    self.statusBar().showMessage("HTML changed")
        #else:
        #    self.statusBar().showMessage("HTML not changed")
        
        self.heditor = htmlEditor()
        self.heditor.ed.setPlainText(all.replace(rtext, "").replace(btext, ""))
        self.heditor.setGeometry(0, 0, 800, 600)
        self.heditor.show()

    def editBody(self):
        all = self.editor.document().toHtml()
        body = all.partition("<body style=")[2].partition(">")[0]
        dlg = QInputDialog()
        mybody, ok = dlg.getText(self, 'change body style', "", QLineEdit.Normal, body, Qt.Dialog)
        if ok:
            new = all.replace(body, mybody)    
            self.editor.document().setHtml(new)
            self.statusBar().showMessage("body style changed")
        else:
            self.statusBar().showMessage("body style not changed")
        
    def insertTable(self):
        self.editor.textCursor().insertHtml(tableheader2)

    def insertTable3(self):
        self.editor.textCursor().insertHtml(tableheader3)

    def handleBrowser(self):
        if self.editor.toPlainText() == "":
            self.statusBar().showMessage("no text")
        else:
            if not self.editor.document().isModified() == True:
                webbrowser.open(self.filename, new=0, autoraise=True)
            else:
                myfilename = "/tmp/browser.html"
                writer = QTextDocumentWriter(myfilename)
                success = writer.write(self.editor.document())
                if success:
                    webbrowser.open(myfilename, new=0, autoraise=True)
                return success

    def contextMenuRequested(self,point):
        cmenu = QMenu()
        cmenu = self.editor.createStandardContextMenu()
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('edit-copy'), "grab this line", self, triggered = self.grabLine))
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('image-x-generic'), "insert Image", self, triggered = self.insertImage))
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "insert Table (2 Column)", self, triggered = self.insertTable))
        cmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "insert Table (3 Column)", self, triggered = self.insertTable3))#
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('text-html'), "convert from HTML", self, triggered = self.convertfromHTML))
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('text-plain'), "convert to Text", self, triggered = self.convertToHTML))
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('browser'), "insert Link", self, triggered = self.insertLink))
        cmenu.addAction(QAction(QIcon.fromTheme('browser'), "edit Link", self, triggered = self.editLink))
        cmenu.addSeparator()
        cmenu.addAction(QAction(QIcon.fromTheme('input-tablet'), "edit HTML (selected Text)", self, triggered = self.editHTML))
        cmenu.addSeparator()
        cmenu.addAction(self.bgAct)
        cmenu.exec_(self.editor.mapToGlobal(point))

    def editLink(self):
        if not self.editor.textCursor().selectedText() == "":
            mt = self.editor.textCursor().selectedText()
            mytext = QTextDocumentFragment.toHtml(self.editor.textCursor().selection())
            myurl = mytext.partition('<a href="')[2].partition('">')[0]
            dlg = QInputDialog()
            dlg.setOkButtonText("Change")
            mylink, ok = dlg.getText(self, 'change URL', "", QLineEdit.Normal, str(myurl), Qt.Dialog)
            if ok:
                if mylink.startswith("http"):
                    self.editor.textCursor().insertHtml("<a href='" + mylink + "' target='_blank'>" + mt + "</a>")
                    self.statusBar().showMessage("link added")
                else:
                    self.statusBar().showMessage("this is no link")
            else:
                self.statusBar().showMessage("not changed")
        else:
            self.statusBar().showMessage("no text selected")

    def insertLink(self):
        if not self.editor.textCursor().selectedText() == "":
            mytext = self.editor.textCursor().selectedText()
            dlg = QInputDialog()
            mylink, ok = dlg.getText(self, 'insert URL', "", QLineEdit.Normal, "", Qt.Dialog)
            if ok:
                if str(mylink).startswith("http"):
                    self.editor.textCursor().insertHtml("<a href='" + mylink + "' target='_blank'>" + mytext + "</a>")
                    self.statusBar().showMessage("link added")
                else:
                    self.statusBar().showMessage("this is no link")
            else:
                self.statusBar().showMessage("no link added")
        else:
            self.statusBar().showMessage("no text selected")

    def convertfromHTML(self):
        oldtext = self.editor.textCursor().selectedText()
        self.editor.textCursor().insertHtml(oldtext)
        self.statusBar().showMessage("converted to html")

    def convertToHTML(self):
        oldtext = QTextDocumentFragment.fromHtml(self.editor.textCursor().selectedText())
        self.editor.textCursor().insertText(oldtext.toPlainText())
        self.statusBar().showMessage("converted to plain text")

    def insertImage(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Pictures/",
                    "Images (*.png *.PNG *.jpg *.JPG *.bmp *.BMP *.xpm *.gif *.eps)")
        if path:
            #self.editor.append("<img src='" + path + "'/>")
            self.editor.textCursor().insertImage("file://" + path)
            self.statusBar().showMessage("'" + path + "' inserted")
        else:
            self.statusBar().showMessage("no image")
    
    def grabLine(self):
        text = self.editor.textCursor().block().text()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
    def createActions(self):
        pass
    
    def findText(self):
        word = self.findfield.text()
        if self.editor.find(word):
            return
        else:
            self.editor.moveCursor(QTextCursor.Start)            
            if self.editor.find(word):
                return

    def document(self):
        return self.editor.document
        
    def isModified(self):
        return self.editor.document().isModified()

    def setModified(self, modified):
        self.editor.document().setModified(modified)

    def setLineWrapMode(self, mode):
        self.editor.setLineWrapMode(mode)

    def clear(self):
        self.editor.clear()

    def setPlainText(self, *args, **kwargs):
        self.editor.setPlainText(*args, **kwargs)

    def setDocumentTitle(self, *args, **kwargs):
        self.editor.setDocumentTitle(*args, **kwargs)

    def set_number_bar_visible(self, value):
        self.numbers.setVisible(value)
        
    def replaceAll(self):
        oldtext = self.findfield.text()
        newtext = self.replacefield.text()
        if not oldtext == "":
            h = self.editor.toHtml().replace(oldtext, newtext)
            self.editor.setText(h)
            self.setModified(True)
            self.statusBar().showMessage("all replaced")
        else:
            self.statusBar().showMessage("nothing to replace")
        
    def replaceOne(self):
        oldtext = self.findfield.text()
        newtext = self.replacefield.text()
        if not oldtext == "":
            h = self.editor.toHtml().replace(oldtext, newtext, 1)
            self.editor.setText(h)
            self.setModified(True)
            self.statusBar().showMessage("one replaced")
        else:
            self.statusBar().showMessage("nothing to replace")
        
    def strippedName(self, fullFileName):
        return QFileInfo(fullFileName).fileName()

    def textBold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(self.actionTextBold.isChecked() and QFont.Bold or QFont.Normal)
        self.mergeFormatOnWordOrSelection(fmt)

    def textUnderline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.actionTextUnderline.isChecked())
        self.mergeFormatOnWordOrSelection(fmt)

    def textItalic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.actionTextItalic.isChecked())
        self.mergeFormatOnWordOrSelection(fmt)

    def textFamily(self, family):
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        self.mergeFormatOnWordOrSelection(fmt)

    def textSize(self, pointSize):
        pointSize = float(self.comboSize.currentText())
        if pointSize > 0:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(pointSize)
            self.mergeFormatOnWordOrSelection(fmt)

    def textStyle(self, styleIndex):
        cursor = self.editor.textCursor()
        if styleIndex:
            styleDict = {
                1: QTextListFormat.ListDisc,
                2: QTextListFormat.ListCircle,
                3: QTextListFormat.ListSquare,
                4: QTextListFormat.ListDecimal,
                5: QTextListFormat.ListLowerAlpha,
                6: QTextListFormat.ListUpperAlpha,
                7: QTextListFormat.ListLowerRoman,
                8: QTextListFormat.ListUpperRoman,
                        }

            style = styleDict.get(styleIndex, QTextListFormat.ListDisc)
            cursor.beginEditBlock()
            blockFmt = cursor.blockFormat()
            listFmt = QTextListFormat()

            if cursor.currentList():
                listFmt = cursor.currentList().format()
            else:
                listFmt.setIndent(1)
                blockFmt.setIndent(0)
                cursor.setBlockFormat(blockFmt)

            listFmt.setStyle(style)
            cursor.createList(listFmt)
            cursor.endEditBlock()
        else:
            bfmt = QTextBlockFormat()
            bfmt.setObjectIndex(-1)
            cursor.mergeBlockFormat(bfmt)

    def textColor(self):
        col = QColorDialog.getColor(self.editor.textColor(), self)
        if not col.isValid():
            return

        fmt = QTextCharFormat()
        fmt.setForeground(col)
        self.mergeFormatOnWordOrSelection(fmt)
        self.colorChanged(col)

    def textAlign(self, action):
        if action == self.actionAlignLeft:
            self.editor.setAlignment(Qt.AlignLeft | Qt.AlignAbsolute)
        elif action == self.actionAlignCenter:
            self.editor.setAlignment(Qt.AlignHCenter)
        elif action == self.actionAlignRight:
            self.editor.setAlignment(Qt.AlignRight | Qt.AlignAbsolute)
        elif action == self.actionAlignJustify:
            self.editor.setAlignment(Qt.AlignJustify)

    def currentCharFormatChanged(self, format):
        self.fontChanged(format.font())
        self.colorChanged(format.foreground().color())

    def cursorPositionChanged(self):
        self.alignmentChanged(self.editor.alignment())

    def clipboardDataChanged(self):
        self.actionPaste.setEnabled(len(QApplication.clipboard().text()) != 0)

    def mergeFormatOnWordOrSelection(self, format):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)

        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)

    def fontChanged(self, font):
        self.comboFont.setCurrentIndex(
                self.comboFont.findText(QFontInfo(font).family()))
        self.comboSize.setCurrentIndex(
                self.comboSize.findText("%s" % font.pointSize()))
        self.actionTextBold.setChecked(font.bold())
        self.actionTextItalic.setChecked(font.italic())
        self.actionTextUnderline.setChecked(font.underline())

    def colorChanged(self, color):
        pix = QPixmap(26, 20)
        pix.fill(color)
        self.actionTextColor.setIcon(QIcon(pix))

    def alignmentChanged(self, alignment):
        if alignment & Qt.AlignLeft:
            self.actionAlignLeft.setChecked(True)
        elif alignment & Qt.AlignHCenter:
            self.actionAlignCenter.setChecked(True)
        elif alignment & Qt.AlignRight:
            self.actionAlignRight.setChecked(True)
        elif alignment & Qt.AlignJustify:
            self.actionAlignJustify.setChecked(True)

    def handlePaintRequest(self, printer):
        printer.setDocName(self.filename)
        document = self.editor.document()
        document.print_(printer)
  
def myStyleSheet(self):
    return """
QTextEdit
{
background: #fafafa;
color: #202020;
border: 1px solid #1EAE3D;
selection-background-color: #729fcf;
selection-color: #ffffff;
}
QMenuBar
{
background: transparent;
border: 0px;
}
QToolBar
{
background: transparent;
border: 0px;
}
QMainWindow
{
     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
}

    """       
