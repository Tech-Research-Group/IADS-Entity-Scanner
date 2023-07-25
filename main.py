"""WORK PACKAGE CONVERTER"""
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
from tkinter.scrolledtext import ScrolledText
import os
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, BOTTOM, END, FALSE, LEFT, RIGHT, TOP, TRUE, WORD, X, YES

bad_terms = ['chap', 'production', 'entity', 'start', 'end']

def open_wip_dir() -> None:
    """Opens TM WIP folder and creates a production.xml file an IADS project."""
    global entities
    global filenames
    entity = ''
    entities = []

    if filenames := filedialog.askopenfilenames():
        doctype_end = ']>'
        # convert_btn.configure(state='normal')
        for path in filenames:
            filename = os.path.basename(path)
            doctype_start = f'<!DOCTYPE {get_opening_tag(path)} PUBLIC "-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" "../IADS/dtd/40051D_7_0.dtd" ['
            # if "title page" in filename.lower() or "front cover" in filename.lower():
            #     with open(path, 'r', encoding='utf-8') as og:
                    
            if "chap" not in filename.lower() and "production" not in filename.lower() and "entity" not in filename.lower() and "start" not in filename.lower() and "end" not in filename.lower() and "svg" not in filename.lower() and "title page" not in filename.lower():
                with open(path, 'r', encoding='utf-8') as original:
                    textbox.insert(END, f'{filename}\n')
                    textbox.insert(END, f'{doctype_start}\n')
                    for line in original:
                        if '<graphic ' in line or '<icon-set ' in line or '<symbol ' in line or '<authent ' in line or '<back ' in line:
                            boardno = re.findall(r'".+"', line)
                            try:
                                entity = f'\t<!ENTITY {boardno[0][1:-1]} SYSTEM "graphics-SVG/{boardno[0][1:-1]}.svg" NDATA svg>'
                                print(boardno[0][1:-1])
                                if entity not in entities:
                                    entities.append(f'{entity}\n')
                                    print(entity)
                            except IndexError as err:
                                print(err)
                    entities = sorted(dict.fromkeys(entities))
                    for line in entities:
                        textbox.insert(END, line)
                    textbox.insert(END, f'{doctype_end}\n\n')
                original.close()
            entities = []
    convert_btn.configure(state='normal')
    

def convert_files() -> None:
    """Prepends DOCTYPE tag to each file and adds entities to production.xml file."""
    entity = ''
    entities = []
    xml_tag = '<?xml version="1.0" encoding="UTF-8"?>'

    for path in filenames:
        filename = os.path.basename(path)
        doctype_start = f'<!DOCTYPE {get_opening_tag(path)} PUBLIC "-//USA-DOD//DTD -1/2D TM Assembly REV D 7.0 20220130//EN" "../IADS/dtd/40051D_7_0.dtd" ['
        # if "title page" in filename.lower() or "front cover" in filename.lower():
        #     with open(path, 'r', encoding='utf-8') as _fin:
        #         data = _fin.read().splitlines(True)
        #     _fin.close()
        #     with open(path, 'w+', encoding='utf-8') as _fout:
        #          for line in data:
        #             if line.startswith('<production '):
        #                 _fout.write('')
        #             elif line.startswith('<paper.manual '):
        #                 _fout.write('')
        #             elif line.startswith('<paper.frnt '):
        #                 _fout.write('')
        #             if '<graphic ' in line:
        #                 boardno = re.findall(r'".+"', line)
        #                 entity = f'\t<!ENTITY {boardno[0][1:-1]} SYSTEM "graphics-SVG/{boardno[0][1:-1]}.svg" NDATA svg>'
        #     _fout.write(f'{xml_tag}\n{doctype_start}\n')
        #     _fout.write(entity)
        #     _fout.writelines(data[1:])
        #     _fout.close()
        if "chap" not in filename.lower() and "production" not in filename.lower() and "entity" not in filename.lower() and "start" not in filename.lower() and "end" not in filename.lower() and "svg" not in filename.lower():
            with open(path, 'r', encoding='utf-8') as fin:
                data = fin.read().splitlines(True)
            with open(path, 'w+', encoding='utf-8') as fout:
                for line in data:
                    if '<graphic ' in line or '<icon-set ' in line or '<symbol ' in line or '<authent ' in line or '<back ' in line:
                        boardno = re.findall(r'".+"', line)
                        try:
                            entity = f'\t<!ENTITY {boardno[0][1:-1]} SYSTEM "graphics-SVG/{boardno[0][1:-1]}.svg" NDATA svg>'
                            if entity not in entities:
                                print(boardno[0][1:-1])
                                entities.append(entity)
                        except IndexError as err:
                            print(err)
                fout.write(f'{xml_tag}\n{doctype_start}\n')
                entities = sorted(dict.fromkeys(entities))
                for line in entities:
                    fout.write(f'{line}\n')
                fout.write(']>\n')
                fout.writelines(data[1:])
            fout.close()
        elif "chap" in filename.lower() or "entity" in filename.lower() or "start" in filename.lower() or "end" in filename.lower() or "svg" in filename.lower():
            os.remove(path)
        entities = []
    messagebox.showinfo('SUCCESS', 'Files converted successfully')


def get_opening_tag(path) -> str:
    """Function that grabs the text of the opening tag in a work package."""
    with open(path, 'r', encoding='utf-8') as original:
        line = original.read().splitlines(True)
        first_line = line[0]
        print(first_line)
        try:
            second_line = line[1]
        except IndexError as err:
            print(err)
            # return ''
            second_line = ''
        line = second_line if '<?xml' in first_line else first_line
        opening_tag = re.findall(r'([a-zA-Z.]+)', line)
    original.close()
    print(opening_tag)
    return opening_tag[0]


root = ttk.Window('IADS GRAPHICS SCANNER', 'darkly')
root.resizable(TRUE, FALSE)
root.geometry('1250x1500')

frame_top = ttk.Frame(root)
frame_top.pack(side=TOP, fill=X)

frame_btm = ttk.Frame(root)
frame_btm.pack(side=BOTTOM, fill=BOTH, expand=TRUE)

wip_btn = ttk.Button(frame_top, text='WIP FOLDER', command=open_wip_dir,
                     bootstyle='success')
wip_btn.pack(side=LEFT, fill=BOTH, expand=TRUE, padx=10, pady=(10, 0))

convert_btn = ttk.Button(frame_top, text='UPDATE FILES', command=convert_files,
                      bootstyle='success', state='disabled')
convert_btn.pack(side=RIGHT, fill=BOTH, expand=TRUE, padx=10, pady=(10, 0))

style = ttk.Style()
textbox = ScrolledText(
    master=frame_btm,
    font='Menlo',
    highlightcolor=style.colors.success,
    highlightbackground=style.colors.border,
    highlightthickness=1,
    wrap=WORD
)
textbox.pack(side=LEFT, fill=BOTH, expand=YES, padx=10, pady=10)

font = tkfont.Font(font=textbox['font'])
tab=font.measure('    ')
textbox.configure(tabs=tab)

root.mainloop()
