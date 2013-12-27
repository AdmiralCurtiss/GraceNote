# GraceNote #

## Starting GraceNote ##
Run GraceNote.py using Python 2.7.x.
GraceNote looks for project configurations in the Project subfolder. If only one is found, it is automatically loaded, otherwise you can choose one.
For setting up a new project, please refer to the appropriate section of this readme.

## Install Instructions ##
If you already have Python 2.7.x and PyQt4 installed, you're good. Otherwise:
* Install Python from here: http://www.python.org/download/
  Be sure you use a 2.x.x version and the x86 installer -- not the x86-64 one!
* Install PyQt4 from here: http://www.riverbankcomputing.co.uk/software/pyqt/download
  Use the version that corresponds to the version of Python you installed. So if you picked a 2.7 x86 Python, you want PyQt-Py2.7-x86-gpl-*.exe.
* Optionally, you can install PyEnchant: http://packages.python.org/pyenchant//download.html
  This gives you spellchecking support.

## Usage Manual ##
Note: This manual was originally written for an earlier version, when this tool only supported Tales of Graces. Some information might be out-of-date and no longer accurate.

### Introduction ###
Grace Note is a full featured collaborative editor originally coded for the Tales of Graces translation project. Using this program, you can modify text from the game and view various statistics and information about the project.

On program start up, Grace Note will download any new files from the server that have been modified by others, as long as an internet connection is available.

During editing, Grace Note will auto-save locally, however, you must remember to save to upload your work to the server. If no internet connection is available, your changes will saved until you reconnect.


### The Main Window ###
The main Grace Note window contains a toolbar, a list on the left, a list on the right, and three text editing boxes. The title of the main window will show your current mode and role.


#### The File List ####
The left list is the file list. This shows a list of all the files, sorted as indicated by the radio buttons above. You may change the sorting. Simply click on a file to view a list of it’s contents in the rightmost list.


#### The Entry List ####
The right list is the entry list. This list shows the contents of the selected file. Each entry represents one message box or menu string in game. The check boxes to the left of the entry list signify that the entry is a debug-use entry. Viewing debug entries is disabled by default, but you can change this behaviour by clicking the yellow yield sign in the toolbar, directly above the entry list. To change the debug status of an entry, click the checkbox.


#### The Editing Windows ####
The three editing windows show the above, currently selected, and below entries, respectively. When an entry is selected, these boxes will contain the entry text, which can be edited. Variables are shown between angle brackets (<>), and newlines have been ornamented with a carriage return symbol. The brackets ARE required for all variables, but the carriage return symbol is optional, and need not be typed. Variables will also appear in colour. Editing windows support copy, paste, cut, select all, undo, and redo, via keyboard shortcuts and the right click menu ONLY. The edit menu is non-functional at this time, excepting full-text copy.

In the lower right corner are four symbols. These symbols denote the completion status of the entry. Green signifies the stage is complete, and blue signifies incomplete. These will be automatically modified dependent on the role you have set. You may also change them manually by clicking on them. The four stages are Translation, Translation Review, Context Review, and Editing, from left to right.

If a comment is available, the text ‘Comment Available’ will be listed beside the entry number above the text box.

If Pyenchant is installed, red lines beneath typed words will denote misspelled words. You may correct these yourself, or right-click them to pop up a list of suggestions.

At any time, you may select a Japanese word and right click it. The contextual menu will contain a list of suggested words, as well as their English equivalents and definitions. The dictionary used is an abridged dictionary, for conciseness. The dictionary also includes a very succinct kanji lookup.


### The Toolbar ###
The toolbar contains many essential features and information. The toolbar’s style and icon size can be changed in the View menu.


#### English, Japanese, Comments ####
The first three icons in the toolbar are ‘English’, ‘Japanese’, and ‘Comments’. Clicking English will change the displayed text to the translated English text, if any is available. This is the default. Clicking Japanese will change the displayed text in the editing boxes to the original Japanese, and clicking Comments will change the box to see any available comments. English and comments are editable, but the original Japanese is not.


#### Two-up ####
The two-up function in the toolbar doubles the amount of text boxes, allowing you to view two different view modes (of English, Japanese and Comments) side-by-side. The second set of text boxes appears to the right, and is not editable. By default, the boxes are set to be viewed in Japanese, but this can be changed by clicking the lower right icon.


#### Reports ####
Reports will detail today’s and yesterday’s uploads, as well as overall statistics. Due to Mass Replace, overall statistics are often skewed.


#### Mass Replace ####
Mass Replace is a powerful tool for searching and replacing text across files. You can search for text as part of an entry (exact match), or an entire entry on it’s own (entry match). Upon searching, a list will be generated that details the entry’s current English, if available, or Japanese if not, the file that contains it, and the entry number it occupies. You may selectively replace searches by modifying the check boxes provided. No text will be replaced until you click replace in the bottom left. This action can not be undone!

Some notes about Mass Replace. Is it possible and recommended to use the search feature on it’s own for a more precise search. You may not Mass replace whitespace or non-visible characters. Replace will not take effect without a search being done prior to the replacement. Deleting the text in search before replacing will modify the text to be replaced, so, it is possible to search for entries with ‘foo’ and then replace all instances of ‘bar’ within that set with some other text of choice (such as ‘I pity the’).


#### Completion ####
Details the completion of each category and file in terms of stage. These percentages are reflected on the website. The total percentage can be viewed in the Window Title.


#### Duplicate Search ####
This window can search inside categories for duplicate text. It can also search only for inconsistent duplicate text where the translated text does not match it’s duplicates, which can be used to find untranslated duplicates or mistranslated duplicates. Very powerful when used in combination with Mass Replace.


#### Live Search ####
The Live search will selectively filter the file list by the entered text. It will locate the text in English or Japanese. Due to the potentially large size of files, for a more specific search, please use the search filter included with Mass Replace. Live Search will only yield general results. Live Search requires a minimum of three characters.


#### Debug Toggle ####
Debug toggle changes the viewing of debug entries on or off. This is off by default.


### The Menu Bar ###
The menu bar contains all functions present in the toolbar, as well as several others.


#### File Menu ####

##### Save #####
Saves all changes done this session to the server. This may take some time, but there should be a progress bar.


#### Edit Menu ####
Most functions in the Edit Menu, for reasons beyond mortal comprehension, do not work. You may access these functions through their standard keyboard shortcuts, but selecting the menu item does not work.


##### Full-Text Copy #####
Full Text Copy only functions when a file or entry is selected. It will paste the entire contents of the file to the clipboard.


#### View Menu ####


##### Changelog #####
Shows the Changelog for the currently selected file.


##### Global Changelog #####
Shows the Changelog for all files at once.


##### Two-up #####
This option is also available in the toolbar. The two-up function doubles the amount of text boxes, allowing you to view two different view modes (of English, Japanese and Comments) side-by-side. The second set of text boxes appears to the right, and is not editable. By default, the boxes are set to be viewed in Japanese, but this can be changed by clicking the lower right icon.


##### English, Japanese, Comments #####
Theses options are also available in the toolbar. Clicking English will change the displayed text to the translated English text, if any is available. This is the default. Clicking Japanese will change the displayed text in the editing boxes to the original Japanese, and clicking Comments will change the box to see any available comments. English and comments are editable, but the original Japanese is not.


##### Toolbar Style and Icon Size #####
Sets the style and icon size for the toolbar.


#### Role Menu ####
The Role which is currently set determines to which completion meter you add. The role is displayed in the title of the Main Window. Setting the role correctly is important to ensuring proper progress bars.


#### Mode Menu ####
The Mode is used in conjunction with Roles in order to determine which files can be labelled complete.


##### Semi-Auto #####
In semi-auto mode, any entries you edit will be marked as ‘complete’ for your current role, and the completion percentage updated accordingly. You can manually set an entry to complete by using the icons in the lower right a text box when an entry is selected. This is the default mode.


##### Auto #####
In automatic mode, any entries which are viewed on screen will be set to ‘complete’ for your current role, and the completion percentage updated accordingly. You can manually set an entry to complete by using the icons in the lower right a text box when an entry is selected. This is useful for editing where entries may need to be read, but not necessarily edited, and manual clicking becomes tedious. This mode will not currently be kept between sessions, and must reset each time.


##### Manual #####
No changes to the status of entries will happen in this mode unless the status icons in each entry are manually clicked.


#### Options Menu ####

##### Reload Config #####
This reloads the currently opened *.xml configuration file.

##### Japanese Voices/English Voices #####
This changes which language's audio files are played, if available. The displayed language is the one that is currently active.

##### (Not) Updating Lower Status #####
This changes the behavior when an entry is edited that is set to a higher status than what is currently set in the Role settings. On Not Updating, the entry's status remains the higher one. On Updating, the entry's status changes to match the selected one.

##### Change Editing Window Amount #####
This changes the amount of entries displayed at once. A restart of GraceNote is required to apply this change.

##### (Not) Writing on Entry change #####
This changes the behavoir when edits made to entires are written to the local Databases. By default (Not Writing), edits are only written when changing databases or pressing pretty much any menu option. If you change this to Writing, changes are written every time you switch which entry is currently displayed. This is safer, but comes with a performance penalty.





## Setting up a Project ##

A GraceNote project requires:

* An FTP server (technically optional, but you won't be able to collaborate with other people without one)
* SQLite database files containing the game's text
* And a configuration file

Optionally, it can also have:

* Audio samples, for voice acting
* Images, for character poses
* Font images, to display text as it would show up in-game

### Creating the Databases ###

First off, create a SQLite file named `ChangeLog` with the following table:

	CREATE TABLE Log(id INT PRIMARY KEY, file TEXT, name TEXT, timestamp INT);

This is used to store which user made changes to what files when, or in other words which files were changed since the last check and should be updated from the server.

Then, create a SQLite file named `GracesJapanese` with the following tables:

	CREATE TABLE Japanese(id INT PRIMARY KEY, string TEXT, debug INT);
	CREATE TABLE descriptions(filename TEXT PRIMARY KEY, shortdesc TEXT, desc TEXT);

This stores the original, unmodified text from the game, and provides a way to change the displayed name of a database within GraceNote without changing the actual database filename.

With these, you can get to the actual text ripping. If you're comfortable with C#, I recommend using my [HyoutaTools](https://github.com/AdmiralCurtiss/HyoutaTools/tree/master/GraceNote)' [GraceNoteDatabaseEntry](https://github.com/AdmiralCurtiss/HyoutaTools/blob/master/GraceNote/GraceNoteDatabaseEntry.cs) class, filling an array of those with the extracted game text, and using the static InsertSQL function to insert them into database files based on [this database template](https://github.com/AdmiralCurtiss/HyoutaTools/blob/master/Files/gndb_template). For example:

	RandomGameFile GameFile = new RandomGameFile( System.IO.File.ReadAllBytes( "gamefile.arc" ) );
	System.IO.File.WriteAllBytes( "gamefile.db", Properties.Resources.gndb_template );
	List<GraceNoteDatabaseEntry> Entries = new List<GraceNoteDatabaseEntry>( GameFile.Strings.Count );
	foreach ( var x in GameFile.Strings ) {
		Entries.Add( new GraceNoteDatabaseEntry( x.Text ) );
	}
	GraceNoteDatabaseEntry.InsertSQL( Entries.ToArray(), "Data Source=gamefile.db", "Data Source=GracesJapanese" );

If you cannot use the provided template database, create one using the following SQL commands:

	CREATE TABLE History(id INT, english TEXT, comment TEXT, status TINYINT, UpdatedBy TEXT, UpdatedTimestamp INT);
	CREATE TABLE Text(id INT PRIMARY KEY, StringID INT, english TEXT, comment TEXT, updated TINYINT, status TINYINT, PointerRef integer, IdentifyString TEXT, IdentifyPointerRef INT, UpdatedBy TEXT, UpdatedTimestamp INT);
	CREATE INDEX History_ID_Index ON History(id);

Some additional info, such as the location of a pointer to the string in the original file, may be needed to reinsert the translated text later. If so, provide them to the GraceNoteDatabaseEntry constructor as PointerRef, IdentifyString or IdentifyPointerRef -- the names are kind of arbitrary, but you can use them as you like. Do note that IdentifyString is displayed within GraceNote next to the entry itself, so it can be used to provide additional info to the translator if possible, such as the name of the person speaking the line.

If the game uses special characters for things like variables or formatting, you should replace them with something more user friendly in this process, then revert that when it comes to reinserting the translated text. For example, if a game uses a 0x06 byte for printing the name of an in-game renamable hero character, replace that with something nicer like '<Hero>'. Pointy brackets are recommended.

As a rule, one game file database should be created for each actual game file. If the game you're working with has lots of entries (several thousand or more) in one file, it might make sense to split it into several game file databases.

If you would rather create those databases using your own code, keep these things in mind:
* Feel free to ignore the History table, it will be used by GraceNote itself. Insert your strings into the Text table.
* Each original language (usually Japanese) entry also needs to be inserted into the GracesJapanese database. For GraceNote's Duplicate Text feature, each original language string should only be inserted once, even if it appears multiple times in the game files.
* The 'id' column of the game file must start at 1 and not skip any number as it goes up.
* The 'StringId' column must reference the 'id' column of the GracesJapanese database's corresponding original language entry.
* The 'comment' column should be, unless some special information to the translator is neccesary, an empty string. It will be visible and editable in GraceNote.
* The 'status' column should be 0.
* You may want to set the UpdatedBy to the name of your ripping tool and the UpdatedTimestamp to the current timestamp (unix time), but it's not necessary.

### Creating the Config File ###

Compared to the databases, this is very easy. All you need here is some settings and a list of all your databases. Take a look at the [template config file](https://github.com/AdmiralCurtiss/GraceNote/blob/master/Projects/config_template.xml) and base yours off that.

The ID should be a unique string naming the project, usually you can take the game name. It will be used to store user info such as the settings and state of the program when you close it, so it can be restored later. Local paths are relative to the location of the config file. There is no limit on the number of categories, but each game file database should only be listed once. Things like Terms, Fonts, Images or the Dictionary are optional.

