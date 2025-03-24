# #!/opt/local/bin/python

# import curses
# import numpy as np
# import time

# # mykey = -1

# # def main(stdscr):
# #     try:
# #         stdscr.clear()
# #         global mykey
# #         mykey = stdscr.getch()


# #     except:
# #         pass

# cmd_list = [
#     "command 1",
#     "command 2",
#     "command 3",
#     "command 4",
#     "command 5",
#     "command 6",
#     "command 7",
#     "command 8",
#     "command 9",
#     "command 10",
#     "command 11",
#     "command 12",
#     "command 13",
#     "command 14",
#     "command 15",
#     "command 16",
#     "command 17",
#     "command 18",
#     "command 19",
#     "command 20",
#     "command 21",
#     "command 22",
#     "command 23",
#     "command 24",
#     "command 25",
#     "command 26",
#     "command 27",
#     "command 28",
#     "command 29",
#     "command 30",
# ]


# # Want pad to move up by one line every time
# # Want viewport to move up until its maximum height and then remain fixed
# def main(stdscr = None):
#     try:
#         # Size of region where commands can be written
#         PAD_W = curses.COLS
#         # PAD_W = 100
#         PAD_H = 1000
        
#         # Size of viewport
#         VIEWPORT_MAX_HEIGHT = 10
#         pad = curses.newpad(PAD_H, PAD_W )
#         for i in range(0, len(cmd_list)):

#             # Add string to line i of pad -> 
#             pad.addstr(i, 0, cmd_list[i])
#             pad_coord_y = np.max([0, i - VIEWPORT_MAX_HEIGHT])
#             pad_coord_x = 0

#             viewport_offset_x = 2
#             viewport_offset_y = 2

#             viewport_height = np.min([i, VIEWPORT_MAX_HEIGHT])

#             stdscr_tl_coord_y = viewport_offset_y + VIEWPORT_MAX_HEIGHT - viewport_height
#             stdscr_tl_coord_x = viewport_offset_x

#             stdscr_br_coord_y = viewport_offset_y + VIEWPORT_MAX_HEIGHT
#             stdscr_br_coord_x = np.min([PAD_W, curses.COLS]) - viewport_offset_x
#             # stdscr_br_coord_x = np.min([PAD_W, 100000]) - viewport_offset_x
            
#             # 1 & 2: top left in pad
#             # 3 & 4: top left in our viewport
#             # 5 & 6: lower right corner of viewport
#             pad.refresh( pad_coord_y, pad_coord_x, stdscr_tl_coord_y, stdscr_tl_coord_x, stdscr_br_coord_y, stdscr_br_coord_x)
#             # print( pad_coord_y, pad_coord_x, stdscr_tl_coord_y, stdscr_tl_coord_x, stdscr_br_coord_y, stdscr_br_coord_x)
#             time.sleep(0.2)
#         time.sleep(1)
#     except KeyboardInterrupt:
#         pass

# curses.wrapper(main)
# # print(mykey)
# # print(curses.KEY_BACKSPACE)
# # main()

class Parent():
    varar = 1

    def pprint(self):
        print(f"Parent: {self.var}")

class Child(Parent):
    def pprint(self):
        print(f"Child: {self.var}")

    def child_method(self):
        print("Child method")

c = Child()
c.child_method()