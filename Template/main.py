import create_nodes as node
from setup import Setup


ui = Setup()
layer_lists = ui.create_layer_lists()
pop_up_ui = ui.create_ui()

if pop_up_ui[1] == 1 and pop_up_ui[0] != []:
    make_safety = False
    count = 0
    aov_line_build = ()

    try:
        node = nuke.selectedNode()
        grpx = node['xpos'].value()
        grpy = node['ypos'].value()
    except ValueError:
        node = None
        grpx = -200
        grpy = 100

    grp = group_make(grpx, grpy, node)
    top_line = make_top_line(grp)
    channel_list = pop_up_ui[0]

    for i in range(len(channel_list)):
        # this determines if the primary aovs have been built and when to add the safety net. Which always comes inbetween the primary and secondary aovs
        if i == 0 and channel_list[i].split("_")[0] != "RGBA":
            count += 1
            make_safety = True
            aov_line_build = make_aov(channel_list[i], top_line[0], top_line[1], top_line[2], grp, make_safety)
            make_safety = False
            aov_line_build = make_aov(channel_list[i], aov_line_build[0], aov_line_build[1], aov_line_build[2], grp, make_safety)
        elif i == 0:
            aov_line_build = make_aov(channel_list[i], top_line[0], top_line[1], top_line[2], grp, make_safety)
        else:
            if i == len(channel_list)-1 and channel_list[i].split("_")[0] == "RGBA":
                aov_line_build = make_aov(channel_list[i], aov_line_build[0], aov_line_build[1], aov_line_build[2], grp, make_safety)
                make_safety = True
                aov_line_build = make_aov(channel_list[i], aov_line_build[0], aov_line_build[1], aov_line_build[2], grp, make_safety)
                make_safety = False
            else:
                if channel_list[i].split("_")[0] != "RGBA":
                    count += 1
                    if count == 1:
                        make_safety = True
                        aov_line_build = make_aov(channel_list[i], aov_line_build[0], aov_line_build[1], aov_line_build[2], grp, make_safety)
                        make_safety = False

                aov_line_build = make_aov(channel_list[i], aov_line_build[0], aov_line_build[1], aov_line_build[2], grp, make_safety)

    end_aov_list(grp, aov_line_build[0], top_line[3])
    nuke.message("Success! Group created.")
else:
    nuke.message("No AOV groups selected.")
