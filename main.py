from ast import literal_eval as leval
import json
from os import path
import time
import re

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def check_marks(group, category: str, default: int = 3):
    """
        Looks up the value of [group] in the category [category], 
        and asks for user input if not found
    """
    print(category)
    if str(group) in seen[category]:
        return seen[category].get(str(group))
    else:
        input_ = input(str(group) + "\n")
        if not input_:
            return default

        # If input is a valid python type, treat it as the dict value
        # Otherwise, assume user has typed in alternative input string to be used as new group
        # (i.e. to correct typoes) hence the recursion
        try:
            new_mark = leval(input_)
            seen[category][str(group)] = new_mark
        except ValueError:
            return check_marks(input_, category, default)
        else:
            return new_mark

# This is the original problem with blanks replaced by regex capture groups 
# TODO: fix "Match Failure"s caused by students changing other parts of the code
pattern = r"""\n*?(.*)\n*
def democracy_sausage\(menu, packsize, orders\):
\n*?(.*)\n*
    for cur_order in orders:
        order_ingredients = menu\[cur_order\]
\n*?(.*)\n*
            ingredients\[cur_ingredient\] \+= cur_number

    packs = {}

    for cur_ingredient in ingredients:
        cur_number = ingredients\[cur_ingredient\]
        cur_size = packsize\[cur_ingredient\]
        cur_packs = cur_number \/\/ cur_size
\n*?(.*)\n*
            cur_packs \+= 1
        packs\[cur_ingredient\] = cur_packs
\n*?(.*)\n*$"""

last_time = 0
def run(event, filename="input.txt"):
    """Runs the marking function"""
    modname = path.split(event.src_path)[1]
    if modname != filename:
        return

    # TODO: There is a bug where saving a file saves twice 
    # This is a temp fix (that doesn't quite work)
    global last_time
    if time.time() - last_time < 0.5:
        return

    print("\n----------------")
    with open(filename) as f:
        # Replace tab with 4 spaces
        src = f.read().replace('\t', '    ')
        # Remove comments
        src = re.sub(r" *(#.*)?$", "", src, flags=re.MULTILINE)

    match = re.match(pattern, src)
    if not match: 
        print("Match Failure!")
        return

    # Regex is [negative lookbehind for non-whitespace] followed by [a number of spaces]
    # Used to remove excessive spaces that students add
    # TODO: add spaces? 
    groups = tuple(re.sub(r"(?<=\S) +", r" ", match.group(i)) for i in range(6))
    m_import, m_init = check_marks(groups[1:3], 'importing', default=(3, 3))
    m_loop = check_marks(groups[3], 'loop')
    m_conditional = check_marks(groups[4], 'conditional')
    m_sort_return = check_marks(groups[5], 'sort_return')

    # The marks are actually deductions so we do 3 - mark
    print(3 - m_import, end=" ")
    print(3 - m_init, end=" ")
    print(3 - m_loop, end=" ")
    print(3 - m_conditional, end=" ")
    print(3 - m_sort_return)
    last_time = time.time()


if __name__ == "__main__":
    # Records all responses the script has seen in a dictionary/json format
    # TODO: use fuzz? to account for typoes
    if path.exists('seen.json'):
        with open('seen.json', 'r') as f:
            seen = json.loads(f.read())
    else:
        seen = {
            'importing': {},
            'loop': {},
            'conditional': {},
            'sort_return': {}
        }

    # We use watchdog to detect file changes in the current directory
    # Simply saving the file (input.txt) will rerun this marking script
    event_handler = FileSystemEventHandler()
    event_handler.on_modified = run
    observer = Observer()
    observer.schedule(event_handler, '.')
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        # Save seen.json for next time
        with open('seen.json', 'w') as f:
            f.write(json.dumps(seen))

    observer.join()
