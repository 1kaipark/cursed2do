import curses as crs  # avoid naming conflict bc im cheeky
import argparse
import pickle
import os
import shutil 
import time 

from copy import deepcopy 

class Curse(object):
    def __init__(self, title: str, notes: str, priority: int) -> None:
        """this will be one task"""
        self.title = title
        self.notes = notes
        self.priority = priority
        self.placed: bool = True

    def set_placed(self, state: bool) -> None:
        self.placed = state

    def __repr__(self) -> str:
        return f"LEVEL {self.priority} CURSE: YOU MUST DO THE FOLLOWING: \n {self.title}"


class Cursed2Do(object):
    def __init__(self, stdscr, curses: list[Curse | None]) -> None:
        self.stdscr = stdscr
        self.curses = sorted(curses, key=lambda c: c.priority)

        self._curses_og = pickle.dumps(deepcopy(self.curses)) # keep the binary representation of self.curses in memory

        self.user_is_cursed: bool = len(self.curses) != 0
        self.recently_lifted: list[Curse] = []
        self.selected = 0  # index of currently selected (use arrow keys to move)
        self.run()

    def new_curse(self, curse: Curse) -> None:
        self.curses.append(curse)
        self.user_is_cursed = len(self.curses) != 0

    def lift_curse(self) -> None:
        if len(self.curses) > 0:
            lifted: Curse = self.curses.pop(self.selected)
            self.recently_lifted.append(lifted)
            self.selected = max(0, self.selected - 1)
            self.user_is_cursed = len(self.curses) != 0

    def display_curses(self) -> None:
        self.h, self.w = self.stdscr.getmaxyx()
        title = "YOU HAVE BEEN CURSED TO..." if self.user_is_cursed else "ALL CURSES HAVE BEEN LIFTED :3"
        self.stdscr.addstr(0, self.w // 2 - len(title) // 2, title, crs.A_BOLD)

        # Display each curse task with a pointer to indicate selection
        for idx, curse in enumerate(self.curses):
            if idx == self.selected:
                self.stdscr.addstr(2 + idx, 2, f"{curse.priority} > {curse.title}", crs.A_REVERSE)  # Highlight selected
            else:
                self.stdscr.addstr(2 + idx, 2, f"{curse.priority} > {curse.title}")
    
    def display_new_curse_menu(self) -> Curse:
        crs.curs_set(1) # display cursor 
        crs.echo()

        menu_width = self.w - 4

        new_curse_menu = crs.newwin(9, menu_width, 2, 2)
        new_curse_menu.border()
        new_curse_menu.addstr(1, 2, "PLACE A NEW CURSE...", crs.A_BOLD)
        new_curse_menu.addstr(2, 2, "TITLE...")
        new_curse_menu.refresh()

        curse_title = new_curse_menu.getstr(3, 4, menu_width - 12).decode("utf-8")

        new_curse_menu.addstr(4, 2, "NOTES...")
        new_curse_menu.refresh()
        curse_notes = new_curse_menu.getstr(5, 4, menu_width - 12).decode("utf-8")

        new_curse_menu.addstr(6, 2, "PRIORITY...")
        curse_prio = new_curse_menu.getstr(7, 4, menu_width - 12).decode("utf-8")
        
        try:
            curse_prio = int(curse_prio.strip())

        except ValueError:
            curse_prio = 0

        crs.noecho()
        crs.curs_set(0)
        return Curse(curse_title, curse_notes, curse_prio)
    
    def display_note(self) -> None:
        self.prompt(self.curses[self.selected].notes)

    def undo_lift(self) -> None:
        self.curses.append(self.recently_lifted[-1])

    def alert(self, text: str, duration: int = 1) -> None:
        msg = crs.newwin(5, 20, 2, 2)
        msg.border()

        msg.addstr(2, 2, text)
        msg.refresh()
        time.sleep(duration)

        msg.clear()
        msg.refresh()

    def prompt(self, text: str) -> bool:
        prompt_width = max(len(text) + 10, 30)
        msg = crs.newwin(5, prompt_width, 2, 2)
        msg.border()

        msg.addstr(2, 2, text)

        msg.refresh()
        while 1:
            key = msg.getch()
            if key == ord('y'):
                return True
            else:
                return False
    
    def legend(self) -> None:
        legend_width: int = self.w - 4
        legend_y: int = self.h - 5

        legend_win = crs.newwin(4, legend_width, legend_y, 2)
        legend_win.border()

        legend_win.addstr(1, 2, "[q] QUIT")
        legend_win.addstr(2, 2, "[c] PLACE CURSE")
        legend_win.addstr(1, legend_width // 4, "[l] LIFT CURSE")
        legend_win.addstr(2, legend_width // 4, "[↑/↓] CHANGE SELECTION")
        legend_win.addstr(1, 2*legend_width // 4, "[→] READ NOTE")
        legend_win.addstr(2, 2*legend_width // 4, "[u] UNDO LIFT")
        legend_win.addstr(1, 3*legend_width // 4, "[w] SAVE TO DISK")
        legend_win.refresh()


    def run(self) -> None:
        crs.curs_set(0)  # hide the cursor
        self.stdscr.clear()

        while 1:
            # main loop
            self.curses = sorted(self.curses, key=lambda c: c.priority)
            self.stdscr.clear()
            self.display_curses()
            self.stdscr.refresh()

            self.legend()

            key = self.stdscr.getch()

            # handle keys
            if key == crs.KEY_UP and self.selected > 0:
                self.selected -= 1
            elif key == crs.KEY_DOWN and self.selected < len(self.curses) - 1:
                self.selected += 1
            elif key == 10:  # Enter key
                self.display_curse_notes()

            elif key == ord('q'):
                if self._curses_og == pickle.dumps(self.curses): # compare serialized versions
                    break
                else:
                    if self.prompt("YOU HAVE UNSAVED CHANGES... FORCE QUIT? [Y/n]"):
                        break


            elif key == ord('l'):
                self.lift_curse()

            elif key == ord('c'):
                curse: Curse = self.display_new_curse_menu()
                self.new_curse(curse)

            elif key == ord('-'):
                self.curses[self.selected].priority -= 1

            elif key == ord('+'):
                self.curses[self.selected].priority += 1

            elif key == crs.KEY_RIGHT:
                self.display_note()

            elif key == ord('u'):
                self.undo_lift()

            elif key == ord('w'):
                with open('my.curses', 'wb') as h:
                    pickle.dump(self.curses, h)
                self.alert('saved to file...')
                self._curses_og = pickle.dumps(deepcopy(self.curses))

            


def main(stdscr) -> None:
    curses: list[Curse | None] = []
    if os.path.exists('my.curses'):
        with open('my.curses', 'rb') as h:
            curses = pickle.load(h)
        shutil.copy('my.curses', 'bak.curses')

    c2d = Cursed2Do(stdscr, curses)

if __name__ == "__main__":
    crs.wrapper(main)
    # stdscr = crs.initscr()
    # main(stdscr)
    
