# pythonGUI4DataConsolidation
Python pyqt5 GUI for data consolidation of 2 datasets, storage in structured DB (sqlite), and exporting consolidated dataset.  

## Reason and main problem to solve

The present GUI helps store clerks to reconciliate data discrepancies between the brick-and-mortar store and the online store. The main issue is randomly entered SKU numbers into the website. This duplicates the labor to update information between the POS database and the webstore.

The GUI was designed to be used along a barcode scanner for faster retrieval of information. The GUI comprises 4 tables:

	*	POS database dump
	*	Website product information
	*	Preview of target item
	*	Saved merged information

Search POS is enabled for SKU’s (barcode) and description in up to 3 fields. Website products can be searched in based on description also in up to 3 fields.

Once a target item is identified in both datasets their information can be merged is a single row by pressing the “Gather Data” button and is shown in the MERGED DATA table. It also can be saved to a local SQLite database (Save button) that provides data persistency. Lastly SKU’s can be exported as a CSV file to update website information on a later stage.  

The data model used is very powerful (QSqlTableModel) and allows direct editing and sorting of displayed data. 

This was a faster alternative to the stated problem. Task automation and similarity comparison yielded very small results, given the lack of commonality and multiple possibilities.

## Usage

A virtual python environment is recommended, original written for windows few years ago (2019), runs fine on MacOS Monterrey. It requires pandas and pyqt5. A shebang can be added to auto execute and `python app.py` works just fine. Qt Designer was used to create the GUI. 

Sample datasets of common beverages are included for testing purposes.

### example
Clone repository, search for “pepsi” on the POS and WEB search, click on both Pepsi 1.5L (Notice different naming convention and SKU codes), click gather data, click save, click save sks2sku to generate the csv file.
![image](https://user-images.githubusercontent.com/17897299/190533651-b4eef7e1-3f8f-49cd-bb74-25d30b0db0ee.png)
