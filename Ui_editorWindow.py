# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'n:\PyProjects\m3editor-python\editorWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_m3ew(object):
    def setupUi(self, m3ew):
        m3ew.setObjectName("m3ew")
        m3ew.resize(1002, 819)
        font = QtGui.QFont()
        font.setFamily("PT Mono")
        m3ew.setFont(font)
        self.centralwidget = QtWidgets.QWidget(m3ew)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabInfo = QtWidgets.QWidget()
        self.tabInfo.setObjectName("tabInfo")
        self.tabWidget.addTab(self.tabInfo, "")
        self.tabTreeView = QtWidgets.QWidget()
        self.tabTreeView.setObjectName("tabTreeView")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabTreeView)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.splitTreeViewH = QtWidgets.QSplitter(self.tabTreeView)
        self.splitTreeViewH.setOrientation(QtCore.Qt.Horizontal)
        self.splitTreeViewH.setObjectName("splitTreeViewH")
        self.layoutWidget = QtWidgets.QWidget(self.splitTreeViewH)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tagsTree = QtWidgets.QTreeView(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tagsTree.sizePolicy().hasHeightForWidth())
        self.tagsTree.setSizePolicy(sizePolicy)
        self.tagsTree.setMinimumSize(QtCore.QSize(250, 0))
        self.tagsTree.setMouseTracking(True)
        self.tagsTree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tagsTree.setHeaderHidden(True)
        self.tagsTree.setObjectName("tagsTree")
        self.verticalLayout_2.addWidget(self.tagsTree)
        self.treeBottomPanel = QtWidgets.QWidget(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeBottomPanel.sizePolicy().hasHeightForWidth())
        self.treeBottomPanel.setSizePolicy(sizePolicy)
        self.treeBottomPanel.setMinimumSize(QtCore.QSize(0, 40))
        self.treeBottomPanel.setObjectName("treeBottomPanel")
        self.verticalLayout_2.addWidget(self.treeBottomPanel)
        self.splitFieldTableV = QtWidgets.QSplitter(self.splitTreeViewH)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.splitFieldTableV.sizePolicy().hasHeightForWidth())
        self.splitFieldTableV.setSizePolicy(sizePolicy)
        self.splitFieldTableV.setOrientation(QtCore.Qt.Vertical)
        self.splitFieldTableV.setObjectName("splitFieldTableV")
        self.treeFieldTopPanel = QtWidgets.QWidget(self.splitFieldTableV)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.treeFieldTopPanel.sizePolicy().hasHeightForWidth())
        self.treeFieldTopPanel.setSizePolicy(sizePolicy)
        self.treeFieldTopPanel.setMinimumSize(QtCore.QSize(0, 100))
        self.treeFieldTopPanel.setObjectName("treeFieldTopPanel")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.treeFieldTopPanel)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.textFieldHint = QtWidgets.QTextBrowser(self.treeFieldTopPanel)
        self.textFieldHint.setObjectName("textFieldHint")
        self.verticalLayout_4.addWidget(self.textFieldHint)
        self.itemNaviPanel = QtWidgets.QFrame(self.treeFieldTopPanel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.itemNaviPanel.sizePolicy().hasHeightForWidth())
        self.itemNaviPanel.setSizePolicy(sizePolicy)
        self.itemNaviPanel.setMinimumSize(QtCore.QSize(0, 40))
        self.itemNaviPanel.setMaximumSize(QtCore.QSize(16777215, 40))
        self.itemNaviPanel.setFrameShape(QtWidgets.QFrame.Box)
        self.itemNaviPanel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.itemNaviPanel.setMidLineWidth(2)
        self.itemNaviPanel.setObjectName("itemNaviPanel")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.itemNaviPanel)
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnItemBack = QtWidgets.QToolButton(self.itemNaviPanel)
        self.btnItemBack.setAutoRepeat(True)
        self.btnItemBack.setArrowType(QtCore.Qt.LeftArrow)
        self.btnItemBack.setObjectName("btnItemBack")
        self.horizontalLayout_2.addWidget(self.btnItemBack)
        self.btnItemForw = QtWidgets.QToolButton(self.itemNaviPanel)
        self.btnItemForw.setAutoRepeat(True)
        self.btnItemForw.setArrowType(QtCore.Qt.RightArrow)
        self.btnItemForw.setObjectName("btnItemForw")
        self.horizontalLayout_2.addWidget(self.btnItemForw)
        self.edtItemNavi = QtWidgets.QLineEdit(self.itemNaviPanel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtItemNavi.sizePolicy().hasHeightForWidth())
        self.edtItemNavi.setSizePolicy(sizePolicy)
        self.edtItemNavi.setMinimumSize(QtCore.QSize(200, 0))
        self.edtItemNavi.setAlignment(QtCore.Qt.AlignCenter)
        self.edtItemNavi.setObjectName("edtItemNavi")
        self.horizontalLayout_2.addWidget(self.edtItemNavi)
        self.edtItemFilter = QtWidgets.QLineEdit(self.itemNaviPanel)
        self.edtItemFilter.setObjectName("edtItemFilter")
        self.horizontalLayout_2.addWidget(self.edtItemFilter)
        self.btnShowBinary = QtWidgets.QToolButton(self.itemNaviPanel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnShowBinary.sizePolicy().hasHeightForWidth())
        self.btnShowBinary.setSizePolicy(sizePolicy)
        self.btnShowBinary.setCheckable(True)
        self.btnShowBinary.setObjectName("btnShowBinary")
        self.horizontalLayout_2.addWidget(self.btnShowBinary)
        spacerItem = QtWidgets.QSpacerItem(0, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_4.addWidget(self.itemNaviPanel)
        self.fieldsTable = QtWidgets.QTreeView(self.splitFieldTableV)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(8)
        sizePolicy.setHeightForWidth(self.fieldsTable.sizePolicy().hasHeightForWidth())
        self.fieldsTable.setSizePolicy(sizePolicy)
        self.fieldsTable.setMouseTracking(True)
        self.fieldsTable.setAlternatingRowColors(True)
        self.fieldsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.fieldsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.fieldsTable.setExpandsOnDoubleClick(False)
        self.fieldsTable.setObjectName("fieldsTable")
        self.verticalLayout_3.addWidget(self.splitTreeViewH)
        self.tabWidget.addTab(self.tabTreeView, "")
        self.tab3dView = QtWidgets.QWidget()
        self.tab3dView.setObjectName("tab3dView")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.tab3dView)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.slideLightPow = QtWidgets.QSlider(self.tab3dView)
        self.slideLightPow.setMinimum(100)
        self.slideLightPow.setMaximum(4000)
        self.slideLightPow.setPageStep(100)
        self.slideLightPow.setProperty("value", 1000)
        self.slideLightPow.setOrientation(QtCore.Qt.Vertical)
        self.slideLightPow.setObjectName("slideLightPow")
        self.horizontalLayout.addWidget(self.slideLightPow)
        self.slideLightMin = QtWidgets.QSlider(self.tab3dView)
        self.slideLightMin.setMinimum(10)
        self.slideLightMin.setMaximum(80)
        self.slideLightMin.setSliderPosition(30)
        self.slideLightMin.setOrientation(QtCore.Qt.Vertical)
        self.slideLightMin.setObjectName("slideLightMin")
        self.horizontalLayout.addWidget(self.slideLightMin)
        self.split3dViewH = QtWidgets.QSplitter(self.tab3dView)
        self.split3dViewH.setOrientation(QtCore.Qt.Horizontal)
        self.split3dViewH.setObjectName("split3dViewH")
        self.gl3dView = m3glWidget(self.split3dViewH)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gl3dView.sizePolicy().hasHeightForWidth())
        self.gl3dView.setSizePolicy(sizePolicy)
        self.gl3dView.setMinimumSize(QtCore.QSize(300, 300))
        self.gl3dView.setObjectName("gl3dView")
        self.tree3dView = QtWidgets.QTreeView(self.split3dViewH)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tree3dView.sizePolicy().hasHeightForWidth())
        self.tree3dView.setSizePolicy(sizePolicy)
        self.tree3dView.setMinimumSize(QtCore.QSize(200, 0))
        self.tree3dView.setObjectName("tree3dView")
        self.tree3dView.header().setDefaultSectionSize(80)
        self.horizontalLayout.addWidget(self.split3dViewH)
        self.tabWidget.addTab(self.tab3dView, "")
        self.verticalLayout.addWidget(self.tabWidget)
        m3ew.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(m3ew)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1002, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuSimple_and_Binary_Display_Count = QtWidgets.QMenu(self.menuView)
        self.menuSimple_and_Binary_Display_Count.setObjectName("menuSimple_and_Binary_Display_Count")
        m3ew.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(m3ew)
        self.statusbar.setObjectName("statusbar")
        m3ew.setStatusBar(self.statusbar)
        self.actionOpen = QtWidgets.QAction(m3ew)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSimpleDisplayCount50 = QtWidgets.QAction(m3ew)
        self.actionSimpleDisplayCount50.setCheckable(True)
        self.actionSimpleDisplayCount50.setChecked(True)
        self.actionSimpleDisplayCount50.setObjectName("actionSimpleDisplayCount50")
        self.actionSimpleDisplayCount100 = QtWidgets.QAction(m3ew)
        self.actionSimpleDisplayCount100.setCheckable(True)
        self.actionSimpleDisplayCount100.setObjectName("actionSimpleDisplayCount100")
        self.actionSimpleDisplayCount200 = QtWidgets.QAction(m3ew)
        self.actionSimpleDisplayCount200.setCheckable(True)
        self.actionSimpleDisplayCount200.setObjectName("actionSimpleDisplayCount200")
        self.actionSimpleDisplayCount500 = QtWidgets.QAction(m3ew)
        self.actionSimpleDisplayCount500.setCheckable(True)
        self.actionSimpleDisplayCount500.setObjectName("actionSimpleDisplayCount500")
        self.actionFields_Auto_Expand_All = QtWidgets.QAction(m3ew)
        self.actionFields_Auto_Expand_All.setCheckable(True)
        self.actionFields_Auto_Expand_All.setObjectName("actionFields_Auto_Expand_All")
        self.actionReopen = QtWidgets.QAction(m3ew)
        self.actionReopen.setEnabled(False)
        self.actionReopen.setObjectName("actionReopen")
        self.actionSave = QtWidgets.QAction(m3ew)
        self.actionSave.setEnabled(False)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_as = QtWidgets.QAction(m3ew)
        self.actionSave_as.setEnabled(False)
        self.actionSave_as.setObjectName("actionSave_as")
        self.actionExit = QtWidgets.QAction(m3ew)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionReopen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_as)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuSimple_and_Binary_Display_Count.addAction(self.actionSimpleDisplayCount50)
        self.menuSimple_and_Binary_Display_Count.addAction(self.actionSimpleDisplayCount100)
        self.menuSimple_and_Binary_Display_Count.addAction(self.actionSimpleDisplayCount200)
        self.menuSimple_and_Binary_Display_Count.addAction(self.actionSimpleDisplayCount500)
        self.menuView.addAction(self.menuSimple_and_Binary_Display_Count.menuAction())
        self.menuView.addAction(self.actionFields_Auto_Expand_All)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi(m3ew)
        self.tabWidget.setCurrentIndex(1)
        self.actionExit.triggered.connect(m3ew.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(m3ew)

    def retranslateUi(self, m3ew):
        _translate = QtCore.QCoreApplication.translate
        m3ew.setWindowTitle(_translate("m3ew", "M3 Editor"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabInfo), _translate("m3ew", "Info"))
        self.btnItemBack.setText(_translate("m3ew", "..."))
        self.btnItemForw.setText(_translate("m3ew", "..."))
        self.edtItemNavi.setText(_translate("m3ew", "1234567890 - 1234567890"))
        self.edtItemFilter.setStatusTip(_translate("m3ew", "Type here to apply filter by field name"))
        self.edtItemFilter.setPlaceholderText(_translate("m3ew", "search fields"))
        self.btnShowBinary.setText(_translate("m3ew", "Show as Binary"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabTreeView), _translate("m3ew", "Tree View"))
        self.slideLightPow.setStatusTip(_translate("m3ew", "Main light power"))
        self.slideLightMin.setStatusTip(_translate("m3ew", "Minimal light value"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab3dView), _translate("m3ew", "3D View"))
        self.menuFile.setTitle(_translate("m3ew", "File"))
        self.menuView.setTitle(_translate("m3ew", "View"))
        self.menuSimple_and_Binary_Display_Count.setTitle(_translate("m3ew", "Simple and Binary Display Count"))
        self.actionOpen.setText(_translate("m3ew", "Open ..."))
        self.actionSimpleDisplayCount50.setText(_translate("m3ew", "50"))
        self.actionSimpleDisplayCount100.setText(_translate("m3ew", "100"))
        self.actionSimpleDisplayCount200.setText(_translate("m3ew", "200"))
        self.actionSimpleDisplayCount500.setText(_translate("m3ew", "500"))
        self.actionFields_Auto_Expand_All.setText(_translate("m3ew", "Fields Auto Expand All"))
        self.actionFields_Auto_Expand_All.setStatusTip(_translate("m3ew", "Expand all fields when tag tree item is selected"))
        self.actionReopen.setText(_translate("m3ew", "Reopen"))
        self.actionSave.setText(_translate("m3ew", "Save"))
        self.actionSave_as.setText(_translate("m3ew", "Save as ..."))
        self.actionExit.setText(_translate("m3ew", "Exit"))
from ui3dView import m3glWidget
