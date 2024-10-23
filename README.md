# IADS Entity Scanner

### Introduction

To use this application, open your current IADS project folder by clicking "Open IADS Folder" and select the root folder for your IADS project. This will bring up a preview of each work package's DOCTYPE tag along with all graphic and external entities (boilerplate and custom) used within each work package. If the preview of each work package DOCTYPE and its entities looks correct, click "Update WP Entities" to add the DOCTYPE tags to the beginning of each work package. You should receive a success alert if everything works correctly.

For the program to read your custom entity files, please use the following file names:

- cautions.ent
- equipment_conditions.ent
- followon_maintenance.ent
- materials.ent
- material_replacement_parts.ent
- notes.ent
- personnel.ent
- procedural_steps.ent
- references.ent
- special_tools.ent
- test_equipment.ent
- tools.ent
- warnings.ent

_If you prefer to store all of your initial setup box entities in one entity file instead of the individual ones seen above, you can use the following entity file name instead:_

- isb.ent

![IADS Entity Scanner](https://github.com/Tech-Research-Group/IADS-Entity-Scanner/blob/main/scanner-screenshot.png "IADS Entity Scanner")

If you find any bugs or have some ideas to improve the program, please reach out to [Nick Ricci](https://github.com/trg-nickr) so he can address each of them properly. Thanks!
