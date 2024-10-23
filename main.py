"""IADS ENTITY SCANNER"""

import contextlib
import itertools

# import logging
import re
import sys
import threading

# import timeit
import tkinter.font as tkfont
from pathlib import Path
from tkinter import TclError, filedialog, messagebox
from tkinter import scrolledtext as st
from typing import Optional

import ttkbootstrap as ttk
from PIL import Image, ImageTk
from ttkbootstrap.constants import BOTH, BOTTOM, DISABLED, END, LEFT, TOP, WORD, E, W, X

CUSTOM_TBUTTON = "Custom.TButton"
ext_entity_dict = {}
files_to_skip = ("chap", "production", "catalog", "entity", "dataset", "toc")
FOLDER_PATH = Path()


def scan_folder_in_background() -> None:
    """
    Starts a new thread to scan the IADS directory in the background.

    This function creates and starts a new thread that runs the `open_iads_dir` function,
    allowing the folder scanning process to occur without blocking the main program flow.

    Returns:
        None
    """
    thread = threading.Thread(target=open_iads_dir)
    thread.start()


def open_iads_dir() -> None:
    """
    Opens a directory selection dialog for the user to choose a folder,
    deletes the content of the textbox, and scans the selected folder
    for IADS files. If a folder is selected, it updates the global
    FOLDER_PATH variable and calls the scan_iads_folder function to
    process the folder. Finally, it enables the update button.
    Returns:
        None
    """
    textbox.delete("1.0", END)
    global FOLDER_PATH
    FOLDER_PATH = Path(filedialog.askdirectory())

    if FOLDER_PATH.exists():
        scan_iads_folder(FOLDER_PATH)
        # # Measure the time taken for 10 executions of scan_iads_folder
        # execution_time: float = timeit.timeit(
        #     "scan_iads_folder(FOLDER_PATH)", globals=globals(), number=10
        # )
        # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        # logging.info("Execution time: %s seconds", execution_time)
    update_btn.configure(state="normal")


def scan_iads_folder(folder_path: Path) -> None:
    """
    Scans the specified IADS folder for entity and work package files.
    This function updates the global `ext_entity_dict` with the results of scanning
    the entity files in the provided folder path. It then scans the work package files
    using the updated `ext_entity_dict`.
    Args:
        FOLDER_PATH (Path): The path to the folder containing the IADS files to be scanned.
    Returns:
        None
    """
    global ext_entity_dict  # pylint: disable=W0603
    ext_entity_dict = scan_entity_files(folder_path)
    scan_work_package_files(folder_path, ext_entity_dict)


def scan_entity_files(folder_path: Path) -> dict:
    """
    Scans a given folder for entity files and extracts external entities from them.
    Args:
        FOLDER_PATH (Path): The path to the folder containing entity files.
    Returns:
        dict: A dictionary where the keys are the base names of the entity files (without
              extensions) and the values are lists of external entities extracted from those files.
    Notes:
        - The function looks for files with a ".ent" extension.
        - It ignores files that do not contain "boilerplate" or "entities" in their path.
        - The function reads each entity file, processes its content to extract external entities,
          and stores the results in a dictionary.
    """
    ext_entity_dict = {}
    folder_path = Path(folder_path)

    # Iterate over all .ent files in the directory and subdirectories
    for path in folder_path.rglob("*.ent"):
        path_str = str(path).lower()
        # Check if the path contains "boilerplate" or "entities"
        if "boilerplate" in path_str or "entities" in path_str:
            # Open and read the entity file
            with path.open("r", encoding="utf-8") as entity_file:
                entity_list = entity_file.read().splitlines()
                entity_list = get_external_entities_from_ent_file(entity_list)
                ext_entity_dict[path.stem] = entity_list

    return ext_entity_dict


def scan_work_package_files(folder_path: Path, ext_entity_dict: dict) -> None:
    """
    Scans work package files in the specified folder path for XML files, extracts external entities
    and graphics, and displays them in a textbox widget.
    Args:
        FOLDER_PATH (Path): The path to the folder containing work package files.
        ext_entity_dict (dict): A dictionary to store the extracted external entities.
    Returns:
        None
    """
    # Create a progress bar widget
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)

    # Get a list of all XML files that need to be processed
    xml_files = [
        path
        for path in folder_path.rglob("files/*.xml")
        if not any(term in path.name.lower() for term in files_to_skip)
        and "!submission" not in str(path).lower()
    ]
    max_value = len(xml_files)

    if max_value == 0:
        # If no files are found, display an informational message and remove the progress bar
        messagebox.showinfo("Info", "No XML files found to scan.")
        progress_bar.destroy()
        return

    # Set the maximum value for the progress bar
    progress_bar["maximum"] = max_value
    progress_bar["value"] = 0  # Reset the progress bar value

    # Iterate through all XML files and process them
    for i, path in enumerate(xml_files, start=1):
        # Open and read the work package file using a context manager
        path_str = str(path).lower()
        if (
            not any(term in path.name.lower() for term in files_to_skip)
            and "!submission" not in path_str
        ):
            with path.open("r", encoding="utf-8") as work_package:
                new_external_entities = []
                new_graphics = []

                # Print path of the work package file in the textbox
                textbox.tag_configure("path", font=("Arial", 12, "bold"))
                textbox.insert(END, f"{path.name}\n", "path")
                print_doctype_declaration(path)

                # Break the file into lines and scan for entities
                lines = work_package.read().splitlines()
                scan_lines_for_entities(lines, ext_entity_dict, new_external_entities, new_graphics)

                # Combine and sort all unique entities (graphics and external entities)
                total_entities = list(itertools.chain(new_graphics, new_external_entities))
                sorted_entities = sorted(set(total_entities))

                # Insert each entity into the textbox
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

        # Update the progress bar
        progress_bar["value"] = i
        root.update_idletasks()  # Ensure the GUI is updated during the loop

    # Once processing is complete, destroy the progress bar
    progress_bar.destroy()

    # Show a success message
    messagebox.showinfo("SUCCESS", "Files scanned successfully")


def scan_lines_for_entities(
    lines: list[str],
    ext_entity_dict: dict,
    new_external_entities: list,
    new_graphics: list,
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
            graphic = f"\t<!ENTITY {boardno} SYSTEM " f'"../graphics-SVG/{boardno}.svg" NDATA svg>'
            if graphic not in new_graphics:
                new_graphics.append(graphic)

        # Add SVG notation if the work package includes graphics
        new_graphics.append('\t<!NOTATION svg PUBLIC "-//W3C//DTD SVG 1.1//EN">')


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
    Generates an entity declaration string based on the provided external entity name and dictionary.
    Args:
        new_external_entity (str): The name of the new external entity to be declared.
        ext_entity_dict (dict): A dictionary containing existing external entities.
    Returns:
        Optional[str]: The entity declaration string if the entity is found in the dictionary, otherwise None.
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
            "-//TRG//ENTITIES MIL-STD-40051 Cautions REV A 1.0 20241018//EN",
        ),
        "equipment_conditions": (
            "equipment_conditions",
            "../entities/equipment_conditions",
            "-//TRG//ENTITIES MIL-STD-40051 Equipment Conditions REV A 1.0 20241018//EN",
        ),
        "followon_maintenance": (
            "followon_maintenance",
            "../entities/followon_maintenance",
            "-//TRG//ENTITIES MIL-STD-40051 Follow-on Maintenance REV A 1.0 20241018//EN",
        ),
        "isb": (
            "isb",
            "../entities/isb",
            "-//TRG//ENTITIES MIL-STD-40051 Initial Setup Box REV A 1.0 20241018//EN",
        ),
        "materials": (
            "materials",
            "../entities/materials",
            "-//TRG//ENTITIES MIL-STD-40051 Material Parts REV A 1.0 20241018//EN",
        ),
        "material_replacement_parts": (
            "material_replacement_parts",
            "../entities/material_replacement_parts",
            "-//TRG//ENTITIES MIL-STD-40051 Material Replacement Parts REV A 1.0 20241018//EN",
        ),
        "notes": (
            "notes",
            "../entities/notes",
            "-//TRG//ENTITIES MIL-STD-40051 Notes REV A 1.0 20241018//EN",
        ),
        "personnel": (
            "personnel",
            "../entities/personnel",
            "-//TRG//ENTITIES MIL-STD-40051 Personnel REV A 1.0 20241018//EN",
        ),
        "procedural_steps": (
            "procedural_steps",
            "../entities/procedural_steps",
            "-//TRG//ENTITIES MIL-STD-40051 Procedural Steps REV A 1.0 20241018//EN",
        ),
        "references": (
            "references",
            "../entities/references",
            "-//TRG//ENTITIES MIL-STD-40051 References REV A 1.0 20241018//EN",
        ),
        "special_tools": (
            "special_tools",
            "../entities/special_tools",
            "-//TRG//ENTITIES MIL-STD-40051 Special Tools REV A 1.0 20241018//EN",
        ),
        "test_equipment": (
            "test_equipment",
            "../entities/test_equipment",
            "-//TRG//ENTITIES MIL-STD-40051 Test Equipment REV A 1.0 20241018//EN",
        ),
        "tools": (
            "tools",
            "../entities/tools",
            "-//TRG//ENTITIES MIL-STD-40051 Tools REV A 1.0 20241018//EN",
        ),
        "warnings": (
            "warnings",
            "../entities/warnings",
            "-//TRG//ENTITIES MIL-STD-40051 Warnings REV A 1.0 20241018//EN",
        ),
    }

    for key, value in entity_mapping.items():
        try:
            if new_external_entity in ext_entity_dict[key]:
                entity_name, filename, public_id = value
                return (
                    f'\t<!ENTITY % {entity_name} PUBLIC "{public_id}" '
                    f'"{filename}.ent"> %{entity_name};'
                )
        except KeyError:
            # If the entity file is not found in the dictionary, skip to the next entity file
            continue

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


def print_doctype_declaration(path: Path) -> None:
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
        textbox.insert(END, " " + doctype_tag_end + "\n", "aqua")


def get_opening_tag(path: Path) -> Optional[str]:
    """
    Extracts the opening tag from an HTML or XML file.
    Args:
        path (Path): The file path to the HTML or XML file.
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

    if opening_tag and len(opening_tag) >= 2:
        return opening_tag[1]
    else:
        # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        # logging.info("No valid opening tag found in %s.", path)
        return None


def update_files_in_background() -> None:
    """
    Starts a new thread to update files in the background.

    This function creates and starts a new thread that runs the `update_files`
    function with the specified `FOLDER_PATH` and `ext_entity_dict` arguments.
    It allows the file update process to run asynchronously without blocking
    the main program execution.

    Returns:
        None
    """
    thread = threading.Thread(target=update_files(FOLDER_PATH, ext_entity_dict))
    thread.start()


def update_files(folder_path: Path, ext_entity_dict: dict) -> None:
    """
    Updates XML files in the specified folder and its subdirectories.
    This function iterates through all XML files in the given folder path and its subdirectories.
    For each XML file, it processes the file unless it matches any term in the files_to_skip list.
    After processing all files, it displays a success message.
    Args:
        folder_path (Path): The path to the folder containing XML files to be updated.
        ext_entity_dict (dict): A dictionary containing external entity definitions to be used in the update process.
    Returns:
        None
    """
    doctype_end = "]>"
    xml_tag = '<?xml version="1.0" encoding="UTF-8"?>'

    # Create a progress bar
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=20)

    # Get a list of all XML files to be processed
    xml_files = [
        path
        for path in folder_path.rglob("files/*.xml")
        if not any(term in path.name.lower() for term in files_to_skip)
        and "!submission" not in str(path).lower()
    ]
    max_value = len(xml_files)

    # Set the maximum value for the progress bar
    progress_bar["maximum"] = max_value
    progress_bar["value"] = 0  # Reset the progress bar value

    # Iterate through all XML files and process them
    for i, path in enumerate(xml_files, start=1):
        process_file(path, xml_tag, doctype_end, ext_entity_dict)
        # # Measure the time taken for 10 executions of scan_iads_folder
        # execution_time: float = timeit.timeit(
        #     "process_file(path, xml_tag, doctype_end, ext_entity_dict)",
        #     globals=globals(),
        #     number=10,
        # )
        # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        # logging.info("Execution time: %s seconds", execution_time)
        progress_bar["value"] = i  # Update progress bar value
        root.update_idletasks()  # Update the GUI

    # Job is done; now hide the progress bar
    progress_bar.pack_forget()

    # Display a success message
    messagebox.showinfo("SUCCESS", "Files converted successfully")


def should_skip_file(path: Path) -> bool:
    """
    Determines if a file should be skipped based on its name.
    Args:
        path (Path): The path of the file to check.

    Returns:
        bool: True if the file should be skipped, False otherwise.
    """
    return any(term in path.name.lower() for term in files_to_skip)


def process_file(path: Path, xml_tag: str, doctype_end: str, ext_entity_dict: dict) -> None:
    """
    Processes an XML file by extracting entities and updating its content.
    Args:
        path (Path): The path to the XML file to be processed.
        xml_tag (str): The XML tag to be used in the updated content.
        doctype_end (str): The ending part of the DOCTYPE declaration.
        ext_entity_dict (dict): A dictionary containing external entities to be extracted.
    Returns:
        None
    """
    new_graphics, new_external_entities = extract_entities(path, ext_entity_dict)
    doctype_start = (
        f"<!DOCTYPE {get_opening_tag(path)} PUBLIC "
        f'"-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" '
        f'"../dtd/40051D_7_0.dtd" ['
    )

    # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    # logging.info("Opening %s.", path)

    # Read the work package file
    with path.open("r", encoding="utf-8") as fin:
        work_package = fin.read().splitlines(True)

    # Write the updated content to the file
    write_updated_file(
        path, work_package, xml_tag, doctype_start, doctype_end, new_graphics, new_external_entities
    )


def extract_entities(path: Path, ext_entity_dict: dict) -> tuple[list[str], list[str]]:
    """
    Extracts graphic-related entities and external entity references from a file.
    Args:
        path (Path): The path to the file to be processed.
        ext_entity_dict (dict): A dictionary containing external entity definitions.
    Returns:
        tuple[list[str], list[str]]: A tuple containing two lists:
            - new_graphics: A list of strings representing new graphic-related entities.
            - new_external_entities: A list of strings representing new external entity references.
    """
    new_graphics = []
    new_external_entities = []

    with path.open("r", encoding="utf-8") as fin:
        work_package = fin.read().splitlines(True)

    for line in work_package:
        # Extract graphics-related entities
        if is_graphic_line(line):
            boardno = re.findall(r'boardno=[",\'][a-zA-Z0-9_-]+[",\']', line)
            boardno = boardno[0][9:-1]
            if boardno:
                graphic = (
                    f"\t<!ENTITY {boardno} SYSTEM "
                    f'"../graphics-SVG/{boardno}.svg"'
                    f" NDATA svg>"
                )
                new_graphics.append(graphic)
            new_graphics.append('\t<!NOTATION svg PUBLIC "-//W3C//DTD SVG 1.1//EN">')

        # Extract external entity references
        if "&" in line:
            matches = re.findall(r"&([a-zA-Z0-9._-]+);", line)

            for new_external_entity in matches:
                entity_declaration = get_entity_declaration(new_external_entity, ext_entity_dict)
                if entity_declaration:
                    new_external_entities.append(entity_declaration)

    return new_graphics, new_external_entities


def is_graphic_line(line: str) -> bool:
    """
    Determines if a given line contains any graphic-related tags.
    Args:
        line (str): The line of text to be checked.
    Returns:
        bool: True if the line contains any graphic-related tags, False otherwise.
    Graphic-related tags include:
        - <graphic
        - <icon-set
        - <symbol
        - <authent
        - <back
    """
    graphic_tags = ["<graphic ", "<icon-set ", "<symbol ", "<authent ", "<back "]
    return any(tag in line for tag in graphic_tags)


def write_updated_file(
    path: Path,
    work_package: list[str],
    xml_tag: str,
    doctype_start: str,
    doctype_end: str,
    new_graphics: list[str],
    new_external_entities: list[str],
) -> None:
    """
    Writes an updated XML file with new graphics and external entities.
    This function writes a new XML file at the specified path, including the provided XML tag,
    DOCTYPE start, and DOCTYPE end. It inserts new graphics and external entities in sorted order
    and appends the remaining part of the original file, excluding the old DOCTYPE section.
    Args:
        path (Path): The path to the file to be written.
        work_package (list[str]): The original content of the file as a list of strings.
        xml_tag (str): The XML tag to be written at the beginning of the file.
        doctype_start (str): The starting tag of the DOCTYPE section.
        doctype_end (str): The ending tag of the DOCTYPE section.
        new_graphics (list[str]): A list of new graphics entities to be included.
        new_external_entities (list[str]): A list of new external entities to be included.
    Returns:
        None
    """
    with path.open("w", encoding="utf-8") as fout:
        fout.write(f"{xml_tag}\n{doctype_start}\n")
        total_entities = list(itertools.chain(new_graphics, new_external_entities))
        sorted_entities = sorted(set(total_entities))

        for entity in sorted_entities:
            fout.write(f"{entity}\n")

        fout.write(f"{doctype_end}\n")

        # Write the remaining part of the file (excluding the old DOCTYPE)
        found_doctype_end = False
        for line in work_package:
            if not found_doctype_end:
                if doctype_end in line:
                    found_doctype_end = True
                continue  # Skip lines until DOCTYPE end is found

            fout.write(line)


def resource_path(relative_path):
    """Get the absolute path to the resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    except AttributeError:
        base_path = (
            Path.cwd()
        )  # Path to the current working directory, equivalent to os.path.abspath(".")

    return base_path / relative_path  # Use the '/' operator to join paths in pathlib


# Initialize main window with ttkbootstrap style
root = ttk.Window("IADS ENTITY SCANNER", "darkly")
root.resizable(True, True)
root.geometry("1400x800")

ICON_BITMAP = "logo_TRG.ico"
# Set the window icon
with contextlib.suppress(TclError):
    root.iconbitmap(ICON_BITMAP)

IMAGE_PATH = "logo_TRG_text.png"
image_path = resource_path(IMAGE_PATH)
image = Image.open(IMAGE_PATH).convert("RGBA")

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
    frame_top,
    text="Open IADS Folder",
    command=scan_folder_in_background,
    style=CUSTOM_TBUTTON,
)
iads_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=W)

# "UPDATE WP ENTITIES" button with custom color
update_btn = ttk.Button(
    frame_top,
    text="Update WP Entities",
    command=update_files_in_background,
    state=DISABLED,
    style=CUSTOM_TBUTTON,
)
update_btn.grid(row=0, column=1, padx=5, pady=5, sticky=W)

# Add empty space between buttons and the image
frame_top.columnconfigure(2, weight=1)

# Label to display the image on the far right
img_label = ttk.Label(frame_top, image=img)  # type: ignore
# Keep a reference to avoid garbage collection
img_label.image = img  # type: ignore
img_label.grid(row=0, column=3, padx=0, pady=5, sticky=E)

# ScrolledText widget for log output or entity text display
textbox = st.ScrolledText(
    master=frame_btm,
    font=("Monaco", 12),
    wrap=WORD,
    highlightthickness=1,
)
textbox.pack(side=LEFT, fill=BOTH, expand=True)

# Configure the font and tabs for the ScrolledText widget
font = tkfont.Font(font=textbox["font"])
tab = font.measure("    ")  # Measure the size of 4 spaces
textbox.configure(tabs=tab)

# Start the main event loop
root.mainloop()
