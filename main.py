"""IADS ENTITY SCANNER"""

import contextlib
import itertools
import os
import re

# import timeit
import tkinter.font as tkfont
from tkinter import TclError, filedialog, messagebox
from tkinter import scrolledtext as st
from typing import Optional

import ttkbootstrap as ttk  # type: ignore
from PIL import Image, ImageTk
from ttkbootstrap.constants import DISABLED  # type: ignore
from ttkbootstrap.constants import BOTH, BOTTOM, END, LEFT, TOP, WORD, E, W, X

CUSTOM_TBUTTON = "Custom.TButton"
ext_entity_dict: dict[str, list[str]] = {}
files_to_skip = ("chap", "production", "catalog", "entity", "dataset", "toc")
FOLDER_PATH = ""
# flake8: disable=E501
ICON_BITMAP = r"C:\\Users\\nicho\\OneDrive - techresearchgroup.com\\Documents\\GitHub\\IADS-Graphics-Scanner\\logo_TRG.ico"  # pylint: disable=C0301
IMAGE_PATH = r"C:\\Users\\nicho\\OneDrive - techresearchgroup.com\\Documents\\GitHub\\IADS-Graphics-Scanner\\logo_TRG_text.png"  # pylint: disable=C0301


def open_iads_dir() -> None:
    """
    Opens a directory selection dialog for the user to choose a folder.
    Clears the content of the textbox and sets the global FOLDER_PATH variable
    to the selected directory path. If a directory is selected, it scans the
    IADS folder and updates the button state to normal.
    Returns:
        None
    """
    textbox.delete("1.0", END)
    global FOLDER_PATH  # pylint: disable=W0603
    FOLDER_PATH = filedialog.askdirectory()

    if FOLDER_PATH:
        scan_iads_folder(FOLDER_PATH)
        # # Measure the time taken for 10 executions of scan_iads_folder
        # execution_time = timeit.timeit(
        #     "scan_iads_folder(FOLDER_PATH)",
        #     globals=globals(),
        #     number=5
        # )
        # print(f"Execution time: {execution_time} seconds")
    update_btn.configure(state="normal")


def scan_iads_folder(FOLDER_PATH: str) -> None:
    """
    Scans the specified IADS folder for entity and work package files.
    This function updates the global `ext_entity_dict` with the results of scanning
    the entity files in the given folder. It then scans the work package files
    using the updated `ext_entity_dict`.
    Args:
        FOLDER_PATH (str): The path to the folder containing the IADS files to be scanned.
    Returns:
        None
    """
    global ext_entity_dict  # pylint: disable=W0603
    ext_entity_dict = scan_entity_files(FOLDER_PATH)
    scan_work_package_files(FOLDER_PATH, ext_entity_dict)


def scan_entity_files(FOLDER_PATH: str) -> dict:
    """
    Scans a given folder for entity files and extracts external entities from them.
    Args:
        FOLDER_PATH (str): The path to the folder containing entity files.
    Returns:
        dict: A dictionary where the keys are the base names of the entity files (without
              extensions) and the values are lists of external entities extracted from those files.
    Notes:
        - The function searches for files with the ".ent" extension.
        - It ignores files that do not contain "boilerplate" or "entities" in their paths.
        - The function reads each entity file, processes its content to extract external entities,
          and stores the results in a dictionary.
    """
    ext_entity_dict = {}
    for _dir, _subdir, files in os.walk(FOLDER_PATH):
        for file in files:
            path = os.path.join(_dir, file).lower()
            if "boilerplate" in path or "entities" in path and file.endswith(".ent"):

                with open(path, "r", encoding="utf-8") as entity_file:
                    entity_list = entity_file.read().splitlines()
                    entity_list = get_external_entities_from_ent_file(entity_list)
                    entity_file.close()
                    ext_entity_dict[file.split(".")[0]] = entity_list
    return ext_entity_dict


def scan_work_package_files(FOLDER_PATH: str, ext_entity_dict: dict) -> None:
    """
    Scans work package files in the specified folder path for XML files, extracts external entities
    and graphics, and displays them in a textbox widget.
    Args:
        FOLDER_PATH (str): The path to the folder containing work package files.
        ext_entity_dict (dict): A dictionary to store extracted external entities.
    Returns:
        None
    """
    for _dir, _subdir, files in os.walk(FOLDER_PATH):
        for file in files:
            if file.endswith(".xml") and not any(term in file.lower() for term in files_to_skip):
                path = os.path.join(_dir, file)
                with open(path, "r", encoding="utf-8") as work_package:
                    new_external_entities: list[str] = []
                    new_graphics: list[str] = []

                    # Print path of the work package file
                    textbox.tag_configure("path", font=("Arial", 12, "bold"))
                    textbox.insert(END, f"{os.path.basename(path)}\n", "path")
                    print_doctype_declaration(path)

                    # Break the file into lines and scan for entities
                    lines = work_package.read().splitlines()
                    scan_lines_for_entities(
                        lines, ext_entity_dict, new_external_entities, new_graphics
                    )

                    total_entities = list(itertools.chain(new_graphics, new_external_entities))
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

                    textbox.tag_configure("aqua", foreground="aqua", font="Monaco")
                    textbox.insert(END, "]>\n\n", "aqua")
                work_package.close()


def scan_lines_for_entities(
    lines: list[str], ext_entity_dict: dict, new_external_entities: list, new_graphics: list
) -> None:
    """
    Scans a list of lines for graphic tags and external entities, updating the provided lists and
    dictionary.
    Args:
        lines (list[str]): A list of strings representing lines to be scanned.
        ext_entity_dict (dict): A dictionary to store external entities found in the lines.
        new_external_entities (list): A list to store new external entities found in the lines.
        new_graphics (list): A list to store new graphic tags found in the lines.
    Returns:
        None
    """
    for line in lines:
        process_graphic_tags(line, new_graphics)
        process_external_entities(line, ext_entity_dict, new_external_entities)


def process_graphic_tags(line: str, new_graphics: list) -> None:
    """
    Processes a line of text to identify and extract graphic tags, then appends
    corresponding ENTITY and NOTATION declarations to the new_graphics list.
    Args:
        line (str): A line of text potentially containing graphic tags.
        new_graphics (list): A list to which ENTITY and NOTATION declarations
                             will be appended if graphic tags are found.
    Returns:
        None
    """
    if (
        "<graphic " in line
        or "<icon-set " in line
        or "<symbol " in line
        or "<authent " in line
        or "<back " in line
    ):
        boardno = re.findall(r'boardno=[",\'][a-zA-Z0-9_-]+[",\']', line)
        boardno = boardno[0][9:-1]
        if boardno:
            graphic = f"\t<!ENTITY {boardno} SYSTEM " f'"../graphics-SVG/{boardno}.svg" NDATA SVG>'
            if graphic not in new_graphics:
                new_graphics.append(graphic)

        # Add SVG notation if the work package includes graphics
        new_graphics.append('\t<!NOTATION SVG PUBLIC "-//W3C//DTD SVG 1.1//EN">')


def process_external_entities(
    line: str, ext_entity_dict: dict, new_external_entities: list
) -> None:
    """
    Processes a line of text to find and handle external entity references.
    This function searches for external entity references in the provided line of text.
    If any references are found, it retrieves their declarations from the provided
    dictionary and appends them to the list of new external entities.
    Args:
        line (str): The line of text to be processed.
        ext_entity_dict (dict): A dictionary containing external entity declarations.
        new_external_entities (list): A list to which new external entity declarations
                                      will be appended.
    Returns:
        None
    """
    if "&" in line:
        # Find external entity references (e.g., &entity;)
        matches = re.findall(r"&([a-zA-Z0-9._-]+);", line)

        if matches:
            # Since re.findall returns a list of matched entities, we iterate over them
            for new_external_entity in matches:
                entity_declaration = get_entity_declaration(new_external_entity, ext_entity_dict)
                if entity_declaration:
                    new_external_entities.append(entity_declaration)


def get_entity_declaration(new_external_entity: str, ext_entity_dict: dict) -> Optional[str]:
    """
    Generates an entity declaration string for a given external entity.
    Args:
        new_external_entity (str): The name of the new external entity to be declared.
        ext_entity_dict (dict): A dictionary containing existing external entities.
    Returns:
        Optional[str]: The entity declaration string if the entity is found in the mapping,
                       otherwise None.
    """
    entity_mapping = {
        "dimboil": (
            "dim_boilerplate",
            "../dtd/boilerplate/dimboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 DIM Boilerplate REV D 7.0 20220130//EN",
        ),
        "editboil": (
            "editable_boilerplate",
            "../dtd/boilerplate/editboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 EDIT Boilerplate REV D 7.0 20220130//EN",
        ),
        "gimboil": (
            "gim_boilerplate",
            "../dtd/boilerplate/gimboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 GIM Boilerplate REV D 7.0 20220130//EN",
        ),
        "mimboil": (
            "mim_boilerplate",
            "../dtd/boilerplate/mimboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 MIM Boilerplate REV D 7.0 20220130//EN",
        ),
        "pimboil": (
            "pim_boilerplate",
            "../dtd/boilerplate/pimboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 PIM Boilerplate REV D 7.0 20220130//EN",
        ),
        "prodboil": (
            "prod_boilerplate",
            "../dtd/boilerplate/prodboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 PROD Boilerplate REV D 7.0 20220130//EN",
        ),
        "simboil": (
            "sim_boilerplate",
            "../dtd/boilerplate/simboil",
            "-//USA-DOD//ENTITIES MIL-STD-40051 SIM Boilerplate REV D 7.0 20220130//EN",
        ),
        "cautions": (
            "cautions",
            "../entities/cautions",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Cautions REV D 7.0 20220130//EN",
        ),
        "ec": (
            "ec",
            "../entities/ec",
            "-//USA-DOD//ENTITIES MIL-STD-40051 EC REV D 7.0 20220130//EN",
        ),
        "fom": (
            "fom",
            "../entities/fom",
            "-//USA-DOD//ENTITIES MIL-STD-40051 FOM REV D 7.0 20220130//EN",
        ),
        "materials": (
            "materials",
            "../entities/materials",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Materials REV D 7.0 20220130//EN",
        ),
        "mrp": (
            "mrp",
            "../entities/mrp",
            "-//USA-DOD//ENTITIES MIL-STD-40051 MRP REV D 7.0 20220130//EN",
        ),
        "notes": (
            "notes",
            "../entities/notes",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Notes REV D 7.0 20220130//EN",
        ),
        "personnel": (
            "personnel",
            "../entities/personnel",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Personnel REV D 7.0 20220130//EN",
        ),
        "procedural_steps": (
            "procedural_steps",
            "../entities/procedural_steps",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Procedural Steps REV D 7.0 20220130//EN",
        ),
        "tools": (
            "tools",
            "../entities/tools",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Tools REV D 7.0 20220130//EN",
        ),
        "warnings": (
            "warnings",
            "../entities/warnings",
            "-//USA-DOD//ENTITIES MIL-STD-40051 Warnings REV D 7.0 20220130//EN",
        ),
    }

    for key, value in entity_mapping.items():
        if new_external_entity in ext_entity_dict[key]:
            entity_name, filename, public_id = value
            return (
                f'\t<!ENTITY % {entity_name} PUBLIC "{public_id}" '
                f'"{filename}.ent"> %{entity_name};'
            )
    return None


def get_external_entities_from_ent_file(entity_file: list[str]) -> list:
    """
    Extracts external entity names from a list of strings representing lines in an entity file.
    Args:
        entity_file (list[str]): A list of strings where each string is a line from an entity file.
    Returns:
        list: A list of unique external entity names found in the entity file.
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
    Prints the DOCTYPE declaration for a given file path in a formatted manner.
    This function retrieves the opening tag from the specified file path and prints
    the DOCTYPE declaration with specific color formatting for different parts of the
    declaration. The colors used are:
    - Aqua for the opening caret and the Public ID and DTD path.
    - Lavender for the "DOCTYPE" keyword.
    - Red for the opening tag.
    Args:
        path (str): The file path from which to retrieve the opening tag.
    """
    opening_tag = get_opening_tag(path)
    if opening_tag:
        doctype_tag_end = (
            'PUBLIC "-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" '
            '"../dtd/40051D_7_0.dtd" ['
        )
        # Print Opening Caret in aqua
        textbox.tag_configure("aqua", foreground="aqua", font="Monaco")
        textbox.insert(END, "<!", "aqua")
        # Print DOCTYPE in lavender
        textbox.tag_configure("lavender", foreground="lavender", font="Monaco")
        textbox.insert(END, "DOCTYPE ", "lavender")
        # Print opening tag in red
        textbox.tag_configure("red", foreground="red", font="Monaco")
        textbox.insert(END, f"{opening_tag}", "red")
        # Print Public ID and DTD path in aqua
        textbox.tag_configure("aqua", foreground="aqua", font="Monaco")
        textbox.insert(END, f" {doctype_tag_end}\n", "aqua")


def get_opening_tag(path: str) -> Optional[str]:
    """
    Extracts the opening tag from an HTML or XML file.
    Args:
        path (str): The file path to the HTML or XML file.
    Returns:
        Optional[str]: The opening tag if found, otherwise None.
    This function reads the content of the specified file and searches for the
    <!DOCTYPE> declaration. If found, it extracts and returns the tag name.
    If no valid opening tag is found, it prints a message and returns None.
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


def update_files(FOLDER_PATH: str, ext_entity_dict: dict) -> None:
    """
    Updates XML files in the specified folder by adding new graphic and external entity
    declarations.
    This function traverses through the given folder, processes each XML file, and updates it by:
    - Adding new graphic-related entities based on specific tags found in the file.
    - Adding new external entity references found in the file.
    - Writing the updated XML declaration and DOCTYPE with the new entities.
    Args:
        FOLDER_PATH (str): The path to the folder containing the XML files to be updated.
        ext_entity_dict (dict): A dictionary containing external entity declarations.
    Returns:
        None
    """
    doctype_end = "]>"
    xml_tag = '<?xml version="1.0" encoding="UTF-8"?>'

    for _dir, _subdir, files in os.walk(FOLDER_PATH):
        for file in files:
            if file.endswith(".xml") and not any(term in file.lower() for term in files_to_skip):
                path = os.path.join(_dir, file)
                new_graphics = []
                new_external_entities = []
                doctype_start = (
                    f"<!DOCTYPE {get_opening_tag(path)} PUBLIC "
                    f'"-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" '
                    f'"../dtd/40051D_7_0.dtd" ['
                )
                print(f"Opening {path}")

                # Read the work package file
                with open(path, "r", encoding="utf-8") as fin:
                    work_package = fin.read().splitlines(True)

                # Create a new file or overwrite the existing one
                with open(path, "w", encoding="utf-8") as fout:
                    for line in work_package:
                        # Find all the graphic-related lines
                        if (
                            "<graphic " in line
                            or "<icon-set " in line
                            or "<symbol " in line
                            or "<authent " in line
                            or "<back " in line
                        ):
                            boardno = re.findall(r'".+"', line)
                            if boardno:
                                graphic = (
                                    f"\t<!ENTITY {boardno[0][1:-1]} SYSTEM "
                                    f'"../graphics-SVG/{boardno[0][1:-1]}.svg"'
                                    f" NDATA SVG>"
                                )
                                new_graphics.append(graphic)
                            # Add SVG notation if the work package includes graphics
                            new_graphics.append(
                                '\t<!NOTATION SVG PUBLIC "-//W3C//DTD SVG 1.1//EN">'
                            )

                        # Find all the external entity references
                        if "&" in line:
                            matches = re.findall(r"&([a-zA-Z0-9._-]+);", line)
                            if matches:
                                for new_external_entity in matches:
                                    entity_declaration = get_entity_declaration(
                                        new_external_entity, ext_entity_dict
                                    )
                                    if entity_declaration:
                                        new_external_entities.append(entity_declaration)

                    # Write XML declaration and DOCTYPE with new entities
                    fout.write(f"{xml_tag}\n{doctype_start}\n")
                    total_entities = list(itertools.chain(new_graphics, new_external_entities))
                    sorted_entities = sorted(set(total_entities))

                    for entity in sorted_entities:
                        fout.write(f"{entity}\n")

                    fout.write(f"{str(doctype_end)}\n")

                    # Find where the DOCTYPE ends (i.e., ]>) and start writing the rest of the file
                    # from there
                    found_doctype_end = False
                    for line in work_package:
                        if not found_doctype_end:
                            if doctype_end in line:
                                found_doctype_end = True
                            continue  # Skip lines until DOCTYPE end is found

                        # Write the remaining part of the file (excluding the old DOCTYPE)
                        fout.write(line)

    messagebox.showinfo("SUCCESS", "Files converted successfully")


# Initialize main window with ttkbootstrap style
root = ttk.Window("IADS ENTITY SCANNER", "darkly")
root.resizable(True, True)
root.geometry("1400x800")

# Set the window icon
with contextlib.suppress(TclError):
    root.iconbitmap(ICON_BITMAP)

# Load the PNG image and extract a dominant color (or manually specify)
with contextlib.suppress(TclError):
    image = Image.open(IMAGE_PATH).convert("RGBA")

# try:
#     IMAGE_PATH = "logo_TRG_text.png"
#     image = Image.open(IMAGE_PATH).convert("RGBA")
# except FileNotFoundError as e:
#     print(f"Warning: Failed to load image: {e}")

# Resize the image
NEW_WIDTH = 350  # Adjust this to make it longer
original_width, original_height = image.size
aspect_ratio = original_height / original_width
new_height = int(NEW_WIDTH * aspect_ratio)
image_resized = image.resize((NEW_WIDTH, new_height), Image.Resampling.LANCZOS)
img = ImageTk.PhotoImage(image_resized)

# Create a custom style for the buttons with the dominant color
DOMINANT_COLOR = "#2067AD"
SUBORDINATE_COLOR = "#FFFFFF"
trg_style = ttk.Style()
trg_style.configure(
    CUSTOM_TBUTTON,
    font=("Helvetica", 14, "bold"),
    padding=10,
    relief="flat",
    foreground=SUBORDINATE_COLOR,
    background=DOMINANT_COLOR,
)

# Top frame for buttons and image
frame_top = ttk.Frame(root)
frame_top.pack(side=TOP, fill=X, padx=10, pady=(10, 0))

# Bottom frame for ScrolledText
frame_btm = ttk.Frame(root)
frame_btm.pack(side=BOTTOM, fill=BOTH, expand=True, padx=10, pady=10)

# "IMPORT IADS FOLDER" button with custom color
iads_btn = ttk.Button(
    frame_top, text="Open IADS Folder", command=open_iads_dir, style=CUSTOM_TBUTTON
)
iads_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=W)

# "UPDATE WP ENTITIES" button with custom color
update_btn = ttk.Button(
    frame_top,
    text="Update WP Entities",
    command=lambda: update_files(FOLDER_PATH, ext_entity_dict),
    state=DISABLED,
    style=CUSTOM_TBUTTON,
)
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
    highlightcolor=ttk.Style().lookup("TButton", "foreground", default="green"),
    highlightbackground=ttk.Style().lookup("TButton", "bordercolor", default="black"),
    highlightthickness=1,
)
textbox.pack(side=LEFT, fill=BOTH, expand=True)

# Configure the font and tabs for the ScrolledText widget
font = tkfont.Font(font=textbox["font"])
tab = font.measure("    ")  # Measure the size of 4 spaces
textbox.configure(tabs=tab)

# Start the main event loop
root.mainloop()
