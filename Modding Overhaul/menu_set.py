from visualization import history_editor, map_viewer, map_editor
from info_grabber import eu4_info

def choose_menu():
    menu_num = 2
    while True:
        info=eu4_info()
        if menu_num==1:
            menu_num=map_editor(menu_num,info)
        elif menu_num==2:
            menu_num=history_editor(menu_num,info)
        elif menu_num==3:
            menu_num=map_viewer(menu_num,info)
        elif  menu_num>3:
            break