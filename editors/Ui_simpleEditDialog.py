# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'n:\PyProjects\m3editor-python\editors\simpleEditDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(338, 156)
        font = QtGui.QFont()
        font.setFamily("PT Mono")
        Dialog.setFont(font)
        Dialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.lblSigned = QtWidgets.QLabel(Dialog)
        self.lblSigned.setObjectName("lblSigned")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lblSigned)
        self.edtSigned = QtWidgets.QLineEdit(Dialog)
        self.edtSigned.setObjectName("edtSigned")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.edtSigned)
        self.lblUnsigned = QtWidgets.QLabel(Dialog)
        self.lblUnsigned.setObjectName("lblUnsigned")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lblUnsigned)
        self.edtUnsigned = QtWidgets.QLineEdit(Dialog)
        self.edtUnsigned.setObjectName("edtUnsigned")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.edtUnsigned)
        self.lblHEX = QtWidgets.QLabel(Dialog)
        self.lblHEX.setObjectName("lblHEX")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.lblHEX)
        self.edtHex = QtWidgets.QLineEdit(Dialog)
        self.edtHex.setObjectName("edtHex")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.edtHex)
        self.verticalLayout.addLayout(self.formLayout)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setStyleSheet("color: rgb(170, 0, 0)")
        self.label.setText("")
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnOK = QtWidgets.QPushButton(Dialog)
        self.btnOK.setAutoDefault(False)
        self.btnOK.setDefault(True)
        self.btnOK.setObjectName("btnOK")
        self.horizontalLayout.addWidget(self.btnOK)
        self.btnCancel = QtWidgets.QPushButton(Dialog)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout.addWidget(self.btnCancel)
        self.btnReset = QtWidgets.QPushButton(Dialog)
        self.btnReset.setObjectName("btnReset")
        self.horizontalLayout.addWidget(self.btnReset)
        self.btnFlags = QtWidgets.QPushButton(Dialog)
        self.btnFlags.setObjectName("btnFlags")
        self.horizontalLayout.addWidget(self.btnFlags)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.lblSigned.setBuddy(self.edtSigned)
        self.lblUnsigned.setBuddy(self.edtUnsigned)
        self.lblHEX.setBuddy(self.edtHex)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.lblSigned.setText(_translate("Dialog", "Signed:"))
        self.lblUnsigned.setText(_translate("Dialog", "Unsigned:"))
        self.lblHEX.setText(_translate("Dialog", "HEX:"))
        self.btnOK.setText(_translate("Dialog", "OK"))
        self.btnCancel.setText(_translate("Dialog", "Cancel"))
        self.btnReset.setText(_translate("Dialog", "Reset"))
        self.btnFlags.setText(_translate("Dialog", "As Flags"))
