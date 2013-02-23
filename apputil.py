#FIXME: interept window's close X button clicked and prompt for save

import os

from PyQt4 import QtCore
from PyQt4 import QtGui


class DocBase(object):
    FILEMODE = "t" # "b" for binary, "t" for text files

    def __init__(self, path=""):
        # Subclasses likely will extend this method. If so, this should
        # be super()'ed _after_ the subclass is done its thing.

        self.path = ""
        self.modified = False

        if path:
            self.loadFromPath(path)

    def dir(self):
        return os.path.dirname(self.path)

    def save(self):
        if not self.path:
            raise Exception("no path")
        self.saveToPath(self.path)

    def saveToPath(self, path):
        fp = open(path, "w%c" % self.FILEMODE)
        self.writeToHandle(fp)
        fp.close()

        self.path = path
        self.modified = False

    def loadFromPath(self, path):
        fp = open(path, "r%c" % self.FILEMODE)
        self.readFromHandle(fp)
        fp.close()

        self.path = path
        self.modified = False

    def writeToHandle(self, fp):
        raise NotImplementedError("subclasses should implement")

    def readFromHandle(self, fp):
        raise NotImplementedError("subclasses should implement")


def getController(app_name, win, doc_class):
    global _cont
    if _cont is None:
        _cont = _Cont(app_name, win, doc_class)
    return _cont
_cont = None


def getPath(action, last_path=""):
    if last_path:
        dir_ = os.path.dirname(last_path)
    else:
        dir_ = os.path.curdir

    if action == "save":
        path = QtGui.QFileDialog.getSaveFileName(caption="Save As", directory=dir_)
    elif action == "open":
        path = QtGui.QFileDialog.getOpenFileName(caption="Open", directory=dir_)
    else:
        raise Exception("invalid action \"%s\"" % str(action))

    return str(path)


def runPrompt(parent, title, text, buttons):
    buts = [ ("ok",              QtGui.QMessageBox.Ok),
             ("open",            QtGui.QMessageBox.Open),
             ("save",            QtGui.QMessageBox.Save),
             ("cancel",          QtGui.QMessageBox.Cancel),
             ("close",           QtGui.QMessageBox.Close),
             ("discard",         QtGui.QMessageBox.Discard),
             ("apply",           QtGui.QMessageBox.Apply),
             ("reset",           QtGui.QMessageBox.Reset),
             ("restoredefaults", QtGui.QMessageBox.RestoreDefaults),
             ("help",            QtGui.QMessageBox.Help),
             ("saveall",         QtGui.QMessageBox.SaveAll),
             ("yes",             QtGui.QMessageBox.Yes),
             ("yestoall",        QtGui.QMessageBox.YesToAll),
             ("no",              QtGui.QMessageBox.No),
             ("notoall",         QtGui.QMessageBox.NoToAll),
             ("abort",           QtGui.QMessageBox.Abort),
             ("retry",           QtGui.QMessageBox.Retry),
             ("ignore",          QtGui.QMessageBox.Ignore) ]
    but_str_to_val = {s: v for s, v in buts}
    but_val_to_str = {v: s for s, v in buts}

    bvals = 0x0
    for bstr in buttons.split():
        bvals |= but_str_to_val[bstr]

    return but_val_to_str[ QtGui.QMessageBox.question(parent, title, text, bvals) ]


class _Cont(QtCore.QObject):
    uiNeedsRefresh = QtCore.pyqtSignal()

    def __init__(self, app_name, win, doc_class):
        super(_Cont, self).__init__()

        self.doc = None

        self._doc_class = doc_class
        self._win = win
        self._app_name = app_name
        self._last_path = ""
        self.doc = self._doc_class()

        self._attachMenuSignals()

    def newDoc(self):
        """
        Does NOT prompt to save.
        """

        self.doc = self._doc_class()
        self._refreshUI()

    def loadDoc(self, path):
        """
        Does NOT prompt to save.
        """

        try:
            self.doc = self._doc_class(path)
        except Exception, e:
            QtGui.QErrorMessage(parent=self._win).showMessage(str(e))
            return False

        self._last_path = path
        self._refreshUI()

        return True

    def findMenuAction(self, menu_name, act_name):
        """
        Get the QAction for a menu entry. Eg: ("file", "save as")
        """

        def _cleanupMenuItemText(t):
            return str(t).lower().replace("&", "")

        menu_name = _cleanupMenuItemText(menu_name)
        act_name = _cleanupMenuItemText(act_name)

        menus = filter(lambda x: isinstance(x, QtGui.QMenu), self._win.menuBar().children())
        for m in menus:
            mname = _cleanupMenuItemText(m.title())
            if mname == menu_name:
                actions = filter(lambda x: isinstance(x, QtGui.QAction), m.children())
                for a in actions:
                    aname = _cleanupMenuItemText(a.text())
                    if aname == act_name:
                        return a

    def _attachMenuSignals(self):
        att = { ("file", "new"):     self._doNew,
                ("file", "open"):    self._doOpen,
                ("file", "save"):    self._doSave,
                ("file", "save as"): self._doSaveAs,
                ("file", "exit"):    self._doExit }

        for (menu, act), meth in att.iteritems():
            self.findMenuAction(menu, act).triggered.connect(meth)

    def _doNew(self):
        if not self._continueWithDestructiveChange():
            return False
        else:
            self.newDoc()
            return True

    def _doOpen(self):
        if not self._continueWithDestructiveChange():
            return False

        path = getPath("open", self._last_path)
        if not path:
            return False

        return self.loadDoc(path)

    def _doSave(self):
        if not self.doc.path:
            return self._doSaveAs()
        else:
            self.doc.save()
            return True

    def _doSaveAs(self):
        path = getPath("save", self._last_path)
        if not path:
            return False

        try:
            self.doc.saveToPath(path)
        except Exception, e:
            QtGui.QErrorMessage(parent=self._win).showMessage(str(e))
            return False

        self._last_path = path
        self._refreshUI()

        return True

    def _doExit(self):
        if not self._continueWithDestructiveChange():
            return False
        else:
            self._win.close()
            return True

    def _continueWithDestructiveChange(self):
        if self.doc.modified:
            a = runPrompt(self._win, "Confirm", "Save changes first?", "yes no cancel")
            if a == "cancel":
                return False
            elif a == "yes":
                if not self._doSave():
                    # abort if the doc was not saved so nothing is lost
                    return False
            elif a == "no":
                pass
            else:
                raise Exception("unhandled response \"%s\"" % str(a))
        return True

    def _refreshUI(self):
        if self.doc.path:
            docname = self.doc.path
        else:
            docname = "No Name"
        self._win.setWindowTitle("%s (%s)" % (self._app_name, docname))

        self.uiNeedsRefresh.emit()
