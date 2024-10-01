# IADS Entity Scanner

### Introduction
To use this application open your current IADS project folder by clicking "Open IADS Folder" and selecting the root folder for your IADS project. This 
will bring up a preview of the DOCTYPE tag along with all entities for each graphic and external entity used within each work package. If the preview 
of each work package DOCTYPE and its entities looks correct, click "Update WP Entities" to add the DOCTYPE tags to the beginning of each work package. 
You should receive a success alert if everything works correctly.

*Make sure none of your work packages start with a blank line. That will cause issues when the scanner tries to update that work package. Also, make
sure each graphic, symbol, icon-set, back and authent tag starts at the beginning of their own line to ensure the scanner reads and updates each graphic
properly.*

![IADS Graphics Scanner](https://github.com/Tech-Research-Group/IADS-Entity-Scanner/blob/main/scanner-screenshot.png "IADS Entity Scanner")

If you find any bugs or have some ideas to improve the program please reach out to [Nick Ricci](https://github.com/trg-nickr) so he can address each of 
them properly. Thanks!
