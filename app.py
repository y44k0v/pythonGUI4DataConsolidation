# Manually combines 2 datasets on specific attributes
# By Yaakov Yosef Miller
# Started on 08142019
# Last modified on 09152022

__version__ = "1.1"

from PyQt5 import uic 
from PyQt5.QtWidgets import (QApplication, QMessageBox, QMainWindow, qApp)
import sys
import sqlite3
import pandas as pd

from PyQt5.QtSql import (QSqlTableModel,QSqlDatabase, QSqlQuery,QSqlRelationalTableModel,QSqlRelation,
QSqlRelationalDelegate,QSqlRecord)
from PyQt5.QtCore import Qt

# loads GUI created with QT designer
qtDesignerFile = "pos2web_skus.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtDesignerFile)

class MyApp(QMainWindow, Ui_MainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        ############ DATA BASE CREATION ################
        tables  = """
        CREATE TABLE IF NOT EXISTS POS (ID_P INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                        SKU_P TEXT,
                                        NAME_P TEXT,
                                        PRICE_P REAL,
                                        USE_P INT);
        CREATE TABLE IF NOT EXISTS WEB (ID_W INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                        SKU_W TEXT,
                                        NAME_W TEXT,
                                        PRICE_W REAL,
                                        USE_W INT);
        CREATE TABLE IF NOT EXISTS PREVIEW (ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                        SKU_P TEXT,
                                        SKU_W TEXT,
                                        NAME_P TEXT,
                                        NAME_W TEXT,
                                        PRICE_P REAL,
                                        PRICE_W REAL);
        CREATE TABLE IF NOT EXISTS MERGED (ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                        SKU_P TEXT,
                                        SKU_W TEXT,
                                        NAME_P TEXT,
                                        NAME_W TEXT,
                                        PRICE_P REAL,
                                        PRICE_W REAL);

        """ 
        # Check for DB and create if none creates SKUS empty DB
        try:
            dburi = "file:skus.db?mode=rw"
            con = sqlite3.connect(dburi, uri=True)
            print("Database present")
            con.close()
        except sqlite3.OperationalError:
            con = sqlite3.connect("skus.db")
            cursor = con.cursor()
            cursor.executescript(tables)
            con.commit()
            con.close()
            print("database created")

        ########## LOADING DATA TO DB ######################
        # Dataset 1 POS database dump - Sample file 3 columns
        pos0 = pd.read_csv("POSsample.csv", quotechar='"', encoding='latin1', 
        skiprows=2, names=["ProdNo", "Description", "Price1"])
        # Dataset 2 Website product catalog download sample
        web0 = pd.read_csv("WEBsample.csv")

        # Datasets formating
        # Most the columns are unused for this application
        web1 = web0[(web0["sku"].isnull() == False ) & (web0["name"].isnull() == False)  & (web0["price"].isnull() == False)]
        

        web3 = web1[["sku","name", "price"]]

       

        pos2 = pos0[(pos0["ProdNo"].isnull() == False ) & (pos0["Description"].isnull() == False) & (pos0["Price1"]>0.0)] # fixed () on last &
        
        # Flags to select which datasets will predominate (0 - not used, 1 - used)
        web3["USE_P"] = 0
        pos2["USE_W"] = 0
        
        self.colsp = ["SKU_P","NAME_P", "PRICE_P", "USE_P"]
        self.colsw = ["SKU_W","NAME_W", "PRICE_W", "USE_W"]

        pos2.columns = self.colsp
        web3.columns = self.colsw

        print(pos2.head(2))
        print(pos2.shape)
        print(web3.head(2))
        print(web3.shape)

        ### Loading dataframes to sqlite dbs 
        try:
            dburi = "file:skus.db?mode=rw"
            con = sqlite3.connect(dburi, uri=True)
            tables = ["POS", "WEB"] 
            try:
                pos2.to_sql(tables[0], con=con, if_exists='replace', index=False)
                con.commit()
                QMessageBox.about(self, "Data Loading", """POS data loaded\n succesfully in table"""+tables[0])
            except:
                QMessageBox.critical(self, "Loading ERROR","Column Mismatch, rearrange columns",
                    QMessageBox.Ok)
            try:
                web3.to_sql(tables[1], con=con, if_exists='replace', index=False)
                con.commit()
                QMessageBox.about(self, "Data Loading", """Web data loaded\n succesfully in table"""+tables[1])
            except:
                QMessageBox.critical(self, "Loading ERROR","Column Mismatch, rearrange columns",
                    QMessageBox.Ok)
                    
        except sqlite3.Error as error:
            QMessageBox.about(self, "Database ERROR","Unexpected Error: {}".format(error))
            
        con.close()
        ### End of  Loading data

        # =================== TABLES FORMAT ======================

        self.setTableFormat(self.posTable)
        self.setTableFormat(self.webTable)
        self.setTableFormat(self.previewTable)
        self.setTableFormat(self.mergedTable)

        # =================== FILLING TABLE VIEWS ================

        self.fillingTables()
        
        # ============ CONNECTIONS ======================
        ##### Search buttons
        self.barCodeSrchButton.clicked.connect(self.onClickSrchBC)
        self.bclineEdit.textChanged.connect(self.onClickSrchBC)
        self.posSrchButton.clicked.connect(self.onClickSrchPos)
        self.webSrchButton.clicked.connect(self.onClickSrchWeb)
        ### Table data
        self.posTable.clicked.connect(lambda: self.getData(Tbl = "pos"))
        self.webTable.clicked.connect(lambda: self.getData(Tbl = "web"))

        #### MERGED BUTTONS
        self.dictMerged = dict()
        self.gatherDataButton.clicked.connect(self.gatherData)
        self.save2MButton.clicked.connect(self.saveToMerged)
        self.saveSKUSButton.clicked.connect(self.saveSKUS)



    ##################################################################
    ########################### FUNCTIONS ############################
    ##################################################################

    # Saves skus from merged data to a 2 column CSV file that ca be used to 
    # update incorrectly assigned SKU into the website DB
    def saveSKUS(self):
        print("#### SAVING sku2sku CSV #####")
        dburi = "file:skus.db?mode=rw"
        con = sqlite3.connect(dburi, uri=True)
        skusDF = pd.read_sql("SELECT SKU_W, SKU_P FROM MERGED", con=con)
        con.close()
        print(skusDF.head())
        skusCSV = skusDF.to_csv ('sku2sku.csv', index = None, header=False)
    
    # Saves manually selected rows from POS and WEB 
    # in the merged dataframe to the local DB

    def saveToMerged(self):
        self.dB.close()
        dburi = "file:skus.db?mode=rw"
        con = sqlite3.connect(dburi, uri=True)
        mergedDF = pd.DataFrame()
        mergedDF = mergedDF.append(self.dictMerged, ignore_index = True)
        mergedDF.to_sql("MERGED", con=con, if_exists='append', index=False)
        con.commit()
        con.close()
        self.fillingTables()

    # Populates tables in the GUI
    def fillingTables(self):
        self.dB = self.createConnection()
        self.posModel = QSqlTableModel()
        self.webModel = QSqlTableModel()
        self.previewModel = QSqlTableModel()
        self.mergedModel = QSqlTableModel()
        self.modelSetup("POS", self.posModel, self.posTable)
        self.modelSetup("WEB", self.webModel, self.webTable)
        self.modelSetup("PREVIEW", self.previewModel, self.previewTable)
        self.modelSetup("MERGED", self.mergedModel, self.mergedTable)

    # Combines manually selected rows in POS and WEB datasets to a single one in the 
    # merged table
    def gatherData(self):
        self.dB.close()
        print(self.dictMerged)
        dburi = "file:skus.db?mode=rw"
        con = sqlite3.connect(dburi, uri=True)
        previewDF = pd.DataFrame()
        previewDF = previewDF.append(self.dictMerged, ignore_index = True)
        previewDF.to_sql("PREVIEW", con=con, if_exists='replace', index=False)
        con.commit()
        con.close()
        self.fillingTables()
        
        
    # Obtains row data from POS and WEB datasets
    def getData(self, Tbl):
        
        if Tbl == "pos":
            index_p = self.posTable.currentIndex().row()
            print("index POS table: ", index_p)
            model = self.posModel
            for col in self.colsp[:-1]:
                self.dictMerged[col] =  model.record(index_p).value(col)
                print(col, ": ", self.dictMerged[col])

        elif Tbl == "web":
            index_w = self.webTable.currentIndex().row()
            print("index WEB table: ", index_w)
            model = self.webModel
            for col in self.colsw[:-1]: 
                
                self.dictMerged[col] =  model.record(index_w).value(col)
                print(col, ": ", self.dictMerged[col])

    # the following 3 onClickSrchX search the datasets by
    # barcode (POS)
    # up to 3 different identifiers on product name (POS)
    # Up to 3 different identifiers on porduct name (WEB) 
    def onClickSrchBC(self):
        barCode = self.bclineEdit.text()
        #print(barCode)
        try:
            if barCode == "":
                QMessageBox.critical(self, "SEARCH ERROR","NO BAR CODE ENTERED",
                                    QMessageBox.Ok)
            else:
                model = self.posModel
                filterSrch = "SKU_P LIKE '%{}%'".format(barCode)
                #print(filterSrch)
                model.setFilter(filterSrch)
                model.select()
                self.queryFromSearchBC = model.selectStatement()
                print(self.queryFromSearchBC)
        except:
            pass
    
    def onClickSrchPos(self):
        p1 = self.pos1lineEdit.text()
        p2 = self.pos2lineEdit.text()
        p3 = self.pos3lineEdit.text()
        # print(p1, p2, p3)
        try:
            if (p1=="") and (p2 =="") and (p3==""):
                QMessageBox.critical(self, "SEARCH ERROR","NO TEXT ENTERED",
                                    QMessageBox.Ok)
            else:
                model = self.posModel
                filterSrch = "NAME_P LIKE '%{}%' AND NAME_P LIKE '%{}%' AND NAME_P LIKE '%{}%'".format(\
                p1, p2, p3)
                # print(filterSrch)
                model.setFilter(filterSrch)
                model.select()
                self.queryFromSearchPos = model.selectStatement()
                print(self.queryFromSearchPos)
        except:
            pass


    def onClickSrchWeb(self):
        w1 = self.web1lineEdit.text()
        w2 = self.web2lineEdit.text()
        w3 = self.web3lineEdit.text()
        # print(w1, w2, w3)
        try:
            if (w1=="") and (w2 =="") and (w3==""):
                QMessageBox.critical(self, "SEARCH ERROR","NO TEXT ENTERED",
                                    QMessageBox.Ok)
            else:
                model = self.webModel
                filterSrch = "NAME_W LIKE '%{}%' AND NAME_W LIKE '%{}%' AND NAME_W LIKE '%{}%'".format(\
                w1, w2, w3)
                # print(filterSrch)
                model.setFilter(filterSrch)
                model.select()
                self.queryFromSearchWeb = model.selectStatement()
                print(self.queryFromSearchWeb)
        except:
            pass

    def setTableFormat(self, table):
        table.horizontalHeader().setHighlightSections(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(20)
        table.setContextMenuPolicy(Qt.CustomContextMenu)  
        table.resizeColumnsToContents()
        #table.setColumnWidth(1, 250)
        table.setSortingEnabled(True)
        table.setShowGrid(True)

    def findrow(self, i):
        self.delrow = i.row()

    def modelSetup(self, TableName, model, tableView):
        model
        self.selrow=-1
        model.setTable(TableName) 
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.select()
        tableView.setModel(model)
        tableView.clicked.connect(self.findrow)

    # Connect to the local DB
    def createConnection(self):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName("skus.db")
        if not db.open():
            QMessageBox.critical(None,qApp.tr("Cannot open database"),
               qApp.tr("Unable to establish a database connection.\n"
                              
                              "Click Cancel to exit."),
               QMessageBox.Cancel)
            return False
        return db # was True

    




# Runs the GUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())