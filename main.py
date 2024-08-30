"""WORK PACKAGE CONVERTER"""

from tkinter import filedialog, messagebox
import tkinter.font as tkfont
from tkinter.scrolledtext import ScrolledText
import os
import re
from typing import Optional
import ttkbootstrap as ttk
from ttkbootstrap.constants import (
    BOTH,
    BOTTOM,
    END,
    FALSE,
    LEFT,
    RIGHT,
    TOP,
    TRUE,
    WORD,
    X,
    YES,
)

bad_terms = ["chap", "production", "catalog", "entity", "start", "end"]


def open_wip_dir() -> None:
    """Opens an IADS files folder and scans through each WP file."""
    textbox.delete("1.0", END)
    global entities
    global filenames
    entity = ""
    entities = []

    if filenames := filedialog.askopenfilenames():
        doctype_end = "]>"
        filtered_filenames = filter_filenames(filenames)
        for path in filtered_filenames:
            filename = os.path.basename(path)
            doctype_start = f'<!DOCTYPE {get_opening_tag(path)} PUBLIC "-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" "../dtd/40051D_7_0.dtd" ['

            with open(path, "r", encoding="utf-8") as original:
                textbox.insert(END, f"{filename}\n")
                textbox.insert(END, f"{doctype_start}\n")
                for line in original:
                    if (
                        "<graphic " in line
                        or "<icon-set " in line
                        or "<symbol " in line
                        or "<authent " in line
                        or "<back " in line
                    ):
                        boardno = re.findall(r'".+"', line)
                        try:
                            entity = f'\t<!ENTITY {boardno[0][1:-1]} SYSTEM "../graphics-SVG/{boardno[0][1:-1]}.svg" NDATA svg>'
                            print(boardno[0][1:-1])
                            # TODO: Possibly switch entities w/ get_current_entities function in if statement below
                            # if entity not in entities:
                            if entity not in get_current_entities(path):
                                entities.append(f"{entity}\n")
                                print(entity)
                        except IndexError as err:
                            print(err)
                entities = sorted(dict.fromkeys(entities))

                for line in get_current_entities(path):
                    print(line)
                    textbox.insert(END, line)

                textbox.insert(END, f"{doctype_end}\n\n")
            original.close()
        entities = []
    update_btn.configure(state="normal")


def filter_filenames(filenames):
    """Filter filenames based on bad terms."""
    return [
        path
        for path in filenames
        if not any(term in os.path.basename(path).lower() for term in bad_terms)
    ]


def update_files() -> None:
    """Prepends DOCTYPE declaration to each file and adds graphics entities to each WP file."""
    entity = ""
    entities = []
    xml_tag = '<?xml version="1.0" encoding="UTF-8"?>'

    for path in filenames:
        filename = os.path.basename(path)

        if (
            "chap" not in filename.lower()
            and "catalog" not in filename.lower()
            and "production" not in filename.lower()
            and "entity" not in filename.lower()
            and "start" not in filename.lower()
            and "end" not in filename.lower()
            and "svg" not in filename.lower()
            and "tiff" not in filename.lower()
        ):
            doctype_start = f'<!DOCTYPE {get_opening_tag(path)} PUBLIC "-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" "../dtd/40051D_7_0.dtd" ['
            with open(path, "r", encoding="utf-8") as fin:
                data = fin.read().splitlines(True)
            with open(path, "w+", encoding="utf-8") as fout:
                for line in data:
                    if (
                        "<graphic " in line
                        or "<icon-set " in line
                        or "<symbol " in line
                        or "<authent " in line
                        or "<back " in line
                    ):
                        boardno = re.findall(r'".+"', line)
                        try:
                            entity = f'\t<!ENTITY {boardno[0][1:-1]} SYSTEM "../graphics-SVG/{boardno[0][1:-1]}.svg" NDATA svg>'
                            if entity not in entities:
                                print(boardno[0][1:-1])
                                entities.append(entity)
                        except IndexError as err:
                            print(err)
                fout.write(f"{xml_tag}\n{doctype_start}\n")
                entities = sorted(dict.fromkeys(entities))
                for line in entities:
                    fout.write(f"{line}\n")
                fout.write("]>\n")
                fout.writelines(data[1:])
            fout.close()
        elif (
            "chap" in filename.lower()
            or "catalog" in filename.lower()
            or "production" in filename.lower()
            or "entity" in filename.lower()
            or "start" in filename.lower()
            or "end" in filename.lower()
            or "svg" in filename.lower()
            or "tiff" in filename.lower()
        ):
            os.remove(path)
        entities = []
    messagebox.showinfo("SUCCESS", "Files converted successfully")


def get_opening_tag(path) -> Optional[str]:
    """Function that grabs the text of the opening tag in a work package."""
    with open(path, "r", encoding="utf-8") as original:
        lines = original.read().splitlines(True)
        opening_tag = None  # Initialize opening_tag to None

        try:
            for line in lines:
                if line.startswith("<!DOCTYPE"):
                    opening_tag = re.findall(r"([a-zA-Z.]+)", line)
                    break

            if opening_tag is None:
                raise UnboundLocalError("No opening tag found")

        except UnboundLocalError as err:
            print(err)
            messagebox.showerror("ERROR", f"Check {os.path.basename(path)} for errors.")
            return None  # Return None to indicate an error condition

    if opening_tag and len(opening_tag) > 1:
        print(
            f"|================================== {opening_tag[1].upper()} ==================================|"
        )
        return opening_tag[1]
    else:
        messagebox.showerror("ERROR", "No valid opening tag found.")
        return None


def get_current_entities(path) -> list:
    """Function that grabs the text of the opening tag in a work package."""
    with open(path, "r", encoding="utf-8") as original:
        lines = original.read().splitlines(True)
        entities = []
        for line in lines:
            # BUG: Fix printing non-entities because of "%" in line
            # ent_decs_newline = re.findall(r"^%.*;$", line)
            # if "<!ENTITY" in line or "%" in line:
            # if "<!ENTITY" in line or ent_decs_newline in line:
            if "<!ENTITY" in line:
                entities.append(line)
    original.close()
    return entities


root = ttk.Window("IADS GRAPHIC SCANNER", "darkly")
root.resizable(TRUE, FALSE)
root.geometry("950x750")

frame_top = ttk.Frame(root)
frame_top.pack(side=TOP, fill=X)

frame_btm = ttk.Frame(root)
frame_btm.pack(side=BOTTOM, fill=BOTH, expand=TRUE)

wip_btn = ttk.Button(
    frame_top, text="FILES FOLDER", command=open_wip_dir, bootstyle="success"
)
wip_btn.pack(side=LEFT, fill=BOTH, expand=TRUE, padx=10, pady=(10, 0))

update_btn = ttk.Button(
    frame_top,
    text="UPDATE FILES",
    command=update_files,
    bootstyle="success",
    state="disabled",
)
update_btn.pack(side=RIGHT, fill=BOTH, expand=TRUE, padx=10, pady=(10, 0))

style = ttk.Style()
textbox = ScrolledText(
    master=frame_btm,
    font="Menlo",
    highlightcolor=style.colors.success,
    highlightbackground=style.colors.border,
    highlightthickness=1,
    wrap=WORD,
)
textbox.pack(side=LEFT, fill=BOTH, expand=YES, padx=10, pady=10)

font = tkfont.Font(font=textbox["font"])
tab = font.measure("    ")
textbox.configure(tabs=tab)

root.mainloop()
