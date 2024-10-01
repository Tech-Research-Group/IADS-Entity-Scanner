"""IADS ENTITY SCANNER"""
import itertools
import os
from PIL import Image, ImageTk
import re
import timeit
from tkinter import messagebox, filedialog
import tkinter.font as tkfont
from tkinter import scrolledtext as st
import ttkbootstrap as ttk
from ttkbootstrap.constants import (
    BOTH,
    BOTTOM,
    DISABLED,
    E,
    END,
    LEFT,
    TOP,
    W,
    WORD,
    X
)
from typing import Optional

global GRAPHIC_TAG, ICON_SET_TAG, SYMBOL_TAG, AUTHENT_TAG, BACK_TAG
GRAPHIC_TAG = "<graphic "
ICON_SET_TAG = "<icon-set "
SYMBOL_TAG = "<symbol "
AUTHENT_TAG = "<authent "
BACK_TAG = "<back "
CUSTOM_TBUTTON = "Custom.TButton"
files_to_skip = ("chap", "production", "catalog", "entity", "dataset", "toc")


def open_iads_dir() -> None:
    """
    Opens an IADS project folder and scans through each WP file.
    Parameters:
        None
    Returns:
        None
    """
    textbox.delete("1.0", END)
    global folder_path
    folder_path = filedialog.askdirectory()

    if folder_path:
        scan_iads_folder(folder_path)
        # # Measure the time taken for 10 executions of scan_iads_folder
        # execution_time = timeit.timeit(
        #     "scan_iads_folder(folder_path)",
        #     globals=globals(),
        #     number=5
        # )
        # print(f"Execution time: {execution_time} seconds")
    update_btn.configure(state="normal")


def scan_iads_folder(folder_path: str) -> None:
    global ext_entity_dict
    ext_entity_dict = scan_entity_files(folder_path)
    scan_work_package_files(folder_path, ext_entity_dict)


def scan_entity_files(folder_path: str) -> dict:
    ext_entity_dict = {}
    for dir, subdirs, files in os.walk(folder_path):
        for file in files:
            path = os.path.join(dir, file).lower()
            if "boilerplate" in path or "entities" in path and file.endswith('.ent'):

                with open(path, "r", encoding="utf-8") as entity_file:
                    entity_list = get_external_entities_from_ent_file(
                        entity_file
                    )
                    entity_file.close()
                    ext_entity_dict[file.split('.')[0]] = entity_list
    return ext_entity_dict


def scan_work_package_files(folder_path: str, ext_entity_dict: dict) -> None:
    for subdir, dirs, files in os.walk(folder_path):
        for file in files:
            if (
                file.endswith('.xml') and
                not any(term in file.lower() for term in files_to_skip)
            ):
                path = os.path.join(subdir, file)

                with open(path, "r", encoding="utf-8") as work_package:
                    new_external_entities = []
                    new_graphics = []

                    # Print path of the work package file
                    textbox.tag_configure("path", font=("Arial", 12, "bold"))
                    textbox.insert(END, f"{os.path.basename(path)}\n", "path")
                    print_doctype_declaration(path)

                    scan_lines_for_entities(
                        work_package, ext_entity_dict,
                        new_external_entities, new_graphics
                    )

                    total_entities = list(
                        itertools.chain(new_graphics, new_external_entities)
                    )
                    sorted_entities = sorted(set(total_entities))

                    for entity in sorted_entities:
                        textbox.insert(END, f"{entity}\n")
                        # Color-code the entity declarations
                        # if "<!ENTITY %" in entity:
                        #     open_tag = entity.split("ENTITY")[0]
                        #     entity_name = entity.split(
                        #         "ENTITY % ")[1].strip(" ")
                        #     textbox.tag_configure(
                        #         "aqua", foreground="aqua", font="Monaco")
                        #     textbox.insert(END, f"{open_tag}", "aqua")
                        #     textbox.tag_configure(
                        #         "lavender", foreground="lavender", font="Monaco")
                        #     textbox.insert(END, "ENTITY", "lavender")
                        #     textbox.tag_configure(
                        #         "aqua", foreground="aqua", font="Monaco")
                        #     textbox.insert(END, " % ", "aqua")
                        #     textbox.tag_configure(
                        #         "red", foreground="red", font="Monaco")
                        #     textbox.insert(END, f"{entity_name}", "red")
                        # elif "NOTATION" in entity:
                        #     textbox.tag_configure(
                        #         "aqua", foreground="aqua", font="Monaco")
                        #     textbox.insert(END, f"{entity}\n", "aqua")
                        # elif "%" not in entity and "NOTATION" not in entity:
                        #     textbox.insert(END, f"{entity}\n")

                    textbox.tag_configure(
                        "aqua", foreground="aqua", font="Monaco")
                    textbox.insert(END, "]>\n\n", "aqua")
                work_package.close()


def scan_lines_for_entities(
    work_package: str,
    ext_entity_dict: dict,
    new_external_entities: list,
    new_graphics: list
) -> None:
    """
    Scans lines in a work package for specific tags and external entity
    references, and generates corresponding graphic and external entity
    declarations.
    Args:
        work_package (str): The content of the work package to be scanned.
        ext_entity_dict (dict): A dictionary mapping entity types to their
        corresponding identifiers.
        new_external_entities (list): A list to store new external entity
        declarations.
        new_graphics (list): A list to store new graphic declarations.
    Returns:
        None
    """
    for line in work_package:
        process_graphic_tags(line, new_graphics)
        process_external_entities(line, ext_entity_dict, new_external_entities)


def process_graphic_tags(
        line: str, new_graphics: list
) -> None:
    """
    Processes a line of text to identify and handle graphic tags.
    This function checks if the provided line contains any of the predefined
    graphic tags (GRAPHIC_TAG, ICON_SET_TAG, SYMBOL_TAG, AUTHENT_TAG, BACK_TAG).
    If a graphic tag is found, it extracts the 'boardno' value from the line,
    constructs an ENTITY declaration for the graphic, and appends it to the
    new_graphics list. Additionally, if any graphic tags are found, it appends
    an SVG NOTATION declaration to the new_graphics list.
    Args:
        line (str): The line of text to be processed.
        new_graphics (list): A list to which new graphic ENTITY and NOTATION
                                declarations will be appended.
    Returns:
        None
    """
    if (
        GRAPHIC_TAG in line
        or ICON_SET_TAG in line
        or SYMBOL_TAG in line
        or AUTHENT_TAG in line
        or BACK_TAG in line
    ):
        boardno = re.findall(
            r'boardno=[",\'][a-zA-Z0-9_-]+[",\']', line)
        boardno = boardno[0][9:-1]
        if boardno:
            graphic = (
                f'\t<!ENTITY {boardno} SYSTEM '
                f'"../graphics-SVG/{boardno}.svg" NDATA SVG>'
            )
            if graphic not in new_graphics:
                new_graphics.append(graphic)

    # Add SVG notation if the work package includes graphics
    new_graphics.append(
        '\t<!NOTATION SVG PUBLIC "-//W3C//DTD SVG 1.1//EN">'
    )


def process_external_entities(
    line: str,
    ext_entity_dict: dict,
    new_external_entities: list
) -> None:
    """
    Processes lines containing external entity references and adds
    corresponding external entity declarations to the
    new_external_entities list.
    Args:
        line (str): The line to be processed.
        ext_entity_dict (dict): A dictionary mapping entity types to their
        corresponding identifiers.
        new_external_entities (list): A list to store new external entity
        declarations.
    Returns:
        None
    """
    if "&" in line:
        # Find external entity references (e.g., &entity;)
        matches = re.findall(r"&([a-zA-Z0-9._-]+);", line)

        if matches:
            # Since re.findall returns a list of matched entities, we
            # iterate over them
            for new_external_entity in matches:
                entity_declaration = get_entity_declaration(
                    new_external_entity,
                    ext_entity_dict
                )
                if entity_declaration:
                    new_external_entities.append(entity_declaration)


def get_entity_declaration(
    new_external_entity: str,
    ext_entity_dict: dict
) -> Optional[str]:
    """
    Maps the entity to the corresponding public_id and filename and creates the
    external entity declaration.
    Args:
        new_external_entity (str): The new external entity to be mapped.
        ext_entity_dict (dict): A dictionary mapping entity types to their
        corresponding identifiers.
    Returns:
        Optional[str]: The external entity declaration, or None if the entity
        doesn't match any known entities.
    """
    entity_mapping = {
        "dimboil": ("dim_boilerplate", "../dtd/boilerplate/dimboil",
                    "-//USA-DOD//ENTITIES MIL-STD-40051 DIM Boilerplate REV D 7.0 20220130//EN"),
        "editboil": ("editable_boilerplate", "../dtd/boilerplate/editboil",
                     "-//USA-DOD//ENTITIES MIL-STD-40051 EDIT Boilerplate REV D 7.0 20220130//EN"),
        "gimboil": ("gim_boilerplate", "../dtd/boilerplate/gimboil",
                    "-//USA-DOD//ENTITIES MIL-STD-40051 GIM Boilerplate REV D 7.0 20220130//EN"),
        "mimboil": ("mim_boilerplate", "../dtd/boilerplate/mimboil",
                    "-//USA-DOD//ENTITIES MIL-STD-40051 MIM Boilerplate REV D 7.0 20220130//EN"),
        "pimboil": ("pim_boilerplate", "../dtd/boilerplate/pimboil",
                    "-//USA-DOD//ENTITIES MIL-STD-40051 PIM Boilerplate REV D 7.0 20220130//EN"),
        "prodboil": ("prod_boilerplate", "../dtd/boilerplate/prodboil",
                     "-//USA-DOD//ENTITIES MIL-STD-40051 PROD Boilerplate REV D 7.0 20220130//EN"),
        "simboil": ("sim_boilerplate", "../dtd/boilerplate/simboil",
                    "-//USA-DOD//ENTITIES MIL-STD-40051 SIM Boilerplate REV D 7.0 20220130//EN"),
        "cautions": ("cautions", "../entities/cautions",
                     "-//USA-DOD//ENTITIES MIL-STD-40051 Cautions REV D 7.0 20220130//EN"),
        "ec": ("ec", "../entities/ec",
               "-//USA-DOD//ENTITIES MIL-STD-40051 EC REV D 7.0 20220130//EN"),
        "fom": ("fom", "../entities/fom",
                "-//USA-DOD//ENTITIES MIL-STD-40051 FOM REV D 7.0 20220130//EN"),
        "materials": ("materials", "../entities/materials",
                      "-//USA-DOD//ENTITIES MIL-STD-40051 Materials REV D 7.0 20220130//EN"),
        "mrp": ("mrp", "../entities/mrp",
                "-//USA-DOD//ENTITIES MIL-STD-40051 MRP REV D 7.0 20220130//EN"),
        "notes": ("notes", "../entities/notes",
                  "-//USA-DOD//ENTITIES MIL-STD-40051 Notes REV D 7.0 20220130//EN"),
        "personnel": ("personnel", "../entities/personnel",
                      "-//USA-DOD//ENTITIES MIL-STD-40051 Personnel REV D 7.0 20220130//EN"),
        "procedural_steps": ("procedural_steps", "../entities/procedural_steps",
                             "-//USA-DOD//ENTITIES MIL-STD-40051 Procedural Steps REV D 7.0 20220130//EN"),
        "tools": ("tools", "../entities/tools",
                  "-//USA-DOD//ENTITIES MIL-STD-40051 Tools REV D 7.0 20220130//EN"),
        "warnings": ("warnings", "../entities/warnings",
                     "-//USA-DOD//ENTITIES MIL-STD-40051 Warnings REV D 7.0 20220130//EN")
    }

    for key, value in entity_mapping.items():
        if new_external_entity in ext_entity_dict[key]:
            entity_name, filename, public_id = value
            return (
                f'\t<!ENTITY % {entity_name} PUBLIC "{public_id}" '
                f'"{filename}.ent"> %{entity_name};'
            )
    return None


def get_external_entities_from_ent_file(
        entity_file: str
) -> list:
    """
    Extracts all external entities from a given entity file.
    Parameters:
        entity_file (str): A string representing the entity file content.
        external_entities (list): A list to store all external
        entities found.
    Returns:
        list: A list of all external entities extracted from the entity
        file.
    """
    external_entities = []
    for line in entity_file:
        if "<!ENTITY" in line:
            external_entity = re.findall(r"<!ENTITY [a-zA-Z0-9._-]+", line)

            if external_entity and external_entity not in external_entities:
                external_entity = external_entity[0][9:]
                external_entities.append(external_entity)
    return external_entities


def print_doctype_declaration(path: str) -> None:
    """
    Prints the opening tag in the doctype declaration in green.
    Args:
        path (str): The file path.
    Returns:
        None
    """
    opening_tag = get_opening_tag(path)
    if opening_tag:
        doctype_tag_end = (
            'PUBLIC "-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN"'
            '"../dtd/40051D_7_0.dtd" ['
        )
        # Print Opening Caret in aqua
        textbox.tag_configure("aqua", foreground="aqua", font="Monaco")
        textbox.insert(END, "<!", "aqua")
        # Print DOCTYPE in lavender
        textbox.tag_configure(
            "lavender", foreground="lavender", font="Monaco")
        textbox.insert(END, "DOCTYPE ", "lavender")
        # Print opening tag in red
        textbox.tag_configure("red", foreground="red", font="Monaco")
        textbox.insert(END, f"{opening_tag}", "red")
        # Print Public ID and DTD path in aqua
        textbox.tag_configure("aqua", foreground="aqua", font="Monaco")
        textbox.insert(END, f" {doctype_tag_end}\n", "aqua")


def get_opening_tag(path: str) -> Optional[str]:
    """
    Function that grabs the text of the opening tag in a work package.
    Parameters:
        path (str): The path to the work package file.
    Returns:
        Optional[str]: The text of the opening tag, or None if an error occurs.
    """
    with open(path, "r", encoding="utf-8") as work_package:
        lines = work_package.read().splitlines(True)
        opening_tag = None  # Initialize opening_tag to None

        for line in lines:
            if line.startswith("<!DOCTYPE"):
                opening_tag = re.findall(r"([a-zA-Z.]+)", line)
                break

    if opening_tag and len(opening_tag) > 1:
        return opening_tag[1]
    else:
        print(f"No valid opening tag found in {path}.")
        return None


def update_files(ext_entity_dict: dict) -> None:
    global folder_path
    doctype_end = "]>"
    xml_tag = '<?xml version="1.0" encoding="UTF-8"?>'

    for subdir, dirs, files in os.walk(folder_path):
        for file in files:
            if (
                file.endswith('.xml') and
                not any(term in file.lower() for term in files_to_skip)
            ):
                path = os.path.join(subdir, file)
                new_graphics = []
                new_external_entities = []
                doctype_start = (
                    f'<!DOCTYPE {get_opening_tag(path)} PUBLIC '
                    f'"-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" '
                    f'"../dtd/40051D_7_0.dtd" ['
                )

                print(f'Opening {path}')
                # Read the work package file
                with open(path, "r", encoding="utf-8") as fin:
                    work_package = fin.read().splitlines(True)

                # Create a new file or overwrite the existing one
                with open(path, "w", encoding="utf-8") as fout:
                    for line in work_package:
                        # Find all the graphic-related lines
                        if (
                            GRAPHIC_TAG in line
                            or ICON_SET_TAG in line
                            or SYMBOL_TAG in line
                            or AUTHENT_TAG in line
                            or BACK_TAG in line
                        ):
                            boardno = re.findall(r'".+"', line)
                            if boardno:
                                graphic = (
                                    f'\t<!ENTITY {boardno[0][1:-1]} SYSTEM '
                                    f'"../graphics-SVG/{boardno[0][1:-1]}.svg"'
                                    f' NDATA SVG>'
                                )
                                new_graphics.append(graphic)
                            # Add SVG notation if the work package includes
                            # graphics
                            new_graphics.append(
                                '\t<!NOTATION SVG PUBLIC "-//W3C//DTD SVG 1.1//EN">'
                            )

                        # Find all the external entity references
                        if "&" in line:
                            matches = re.findall(r"&([a-zA-Z0-9._-]+);", line)
                            if matches:
                                for new_external_entity in matches:
                                    entity_declaration = (
                                        get_entity_declaration(
                                            new_external_entity,
                                            ext_entity_dict
                                        )
                                    )
                                    if entity_declaration:
                                        new_external_entities.append(
                                            entity_declaration
                                        )

                    # Write XML declaration and DOCTYPE with new entities
                    fout.write(f"{xml_tag}\n{doctype_start}\n")
                    total_entities = list(
                        itertools.chain(new_graphics, new_external_entities)
                    )
                    sorted_entities = sorted(set(total_entities))

                    for entity in sorted_entities:
                        fout.write(f"{entity}\n")

                    fout.write(f"{doctype_end}\n")

                    # Find where the DOCTYPE ends (i.e., ]>) and start writing
                    # the rest of the file from there
                    found_doctype_end = False
                    for line in work_package:
                        if not found_doctype_end:
                            if ']>' in line:
                                found_doctype_end = True
                            continue  # Skip lines until DOCTYPE end is found

                        # Write the remaining part of the file (excluding the
                        # old DOCTYPE)
                        fout.write(line)

    messagebox.showinfo("SUCCESS", "Files converted successfully")


# Initialize main window with ttkbootstrap style
root = ttk.Window("IADS ENTITY SCANNER", "darkly")
root.resizable(True, True)
root.geometry("1400x800")

# Set the window icon
root.iconbitmap('logo_TRG.ico')

# Load the PNG image and extract a dominant color (or manually specify)
image_path = "logo_TRG_text.png"
image = Image.open(image_path).convert('RGBA')

# Resize the image
new_width = 350  # Adjust this to make it longer
original_width, original_height = image.size
aspect_ratio = original_height / original_width
new_height = int(new_width * aspect_ratio)
image_resized = image.resize((new_width, new_height), Image.LANCZOS)
img = ImageTk.PhotoImage(image_resized)

# Create a custom style for the buttons with the dominant color
dominant_color = '#2067AD'
subordinate_color = '#FFFFFF'
trg_style = ttk.Style()
trg_style.configure(CUSTOM_TBUTTON, font=("Helvetica", 14, "bold"), padding=10,
                    relief="flat", foreground=subordinate_color,
                    background=dominant_color)

# Top frame for buttons and image
frame_top = ttk.Frame(root)
frame_top.pack(side=TOP, fill=X, padx=10, pady=(10, 0))

# Bottom frame for ScrolledText
frame_btm = ttk.Frame(root)
frame_btm.pack(side=BOTTOM, fill=BOTH, expand=True, padx=10, pady=10)

# "IMPORT IADS FOLDER" button with custom color
iads_btn = ttk.Button(frame_top, text="Open IADS Folder",
                      command=open_iads_dir, style=CUSTOM_TBUTTON)
iads_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=W)

# "UPDATE WP ENTITIES" button with custom color
update_btn = ttk.Button(frame_top, text="Update WP Entities",
                        command=lambda: update_files(ext_entity_dict),
                        state=DISABLED, style=CUSTOM_TBUTTON)
update_btn.grid(row=0, column=1, padx=5, pady=5, sticky=W)

# Add empty space between buttons and the image
frame_top.columnconfigure(2, weight=1)

# Label to display the image on the far right
img_label = ttk.Label(frame_top, image=img)
img_label.image = img  # Keep a reference to avoid garbage collection
img_label.grid(row=0, column=3, padx=0, pady=5, sticky=E)

# ScrolledText widget for log output or entity text display
textbox = st.ScrolledText(
    master=frame_btm,
    font=("Monaco", 12),
    wrap=WORD,
    highlightcolor=root.style.colors.success,
    highlightbackground=root.style.colors.border,
    highlightthickness=1
)
textbox.pack(side=LEFT, fill=BOTH, expand=True)

# Configure the font and tabs for the ScrolledText widget
font = tkfont.Font(font=textbox["font"])
tab = font.measure("    ")  # Measure the size of 4 spaces
textbox.configure(tabs=tab)

# Start the main event loop
root.mainloop()
