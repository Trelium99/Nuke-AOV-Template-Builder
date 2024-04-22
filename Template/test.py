"""You can run the code if you past this in the script view to see how it works.
Just import an exr sequence"""

class Setup:

    def __init__(self):
        self.primary_aovs = []
        self.secondary_aovs = []
        self.channel_list = nuke.layers()
        self.selected_aovs_list = []
        self.missed_aovs = []

    def create_layer_lists(self):
        for item in self.channel_list:
            if item.split("_")[0] == "RGBA":
                self.primary_aovs.append(item)
            elif item == 'coat' or item == 'sheen' or item == 'specular' or item == 'sss' or item == 'volume' or \
                    item.split("_")[0] == 'diffuse' or item.split("_")[0] == 'specular' or item.split("_")[
                0] == "sss" or item == 'emission':
                self.secondary_aovs.append(item)
            else:
                if item.split("_")[0] != "crypto" and item != 'rgba' and item != 'alpha' and item != 'rgb':
                    self.missed_aovs.append(item)
        return self.primary_aovs, self.secondary_aovs, self.missed_aovs

    def check_missed(self):
        aov_select = nuke.Panel('Did we miss any AOVS?')
        for item in self.missed_aovs:
            aov_select.addBooleanCheckBox(f"{item}", False)
        display_aov_select = aov_select.show()
        for aov in self.missed_aovs:
            if aov_select.value(aov):
                self.selected_aovs_list.append(aov)
                self.missed_aovs.remove(aov)

    def create_ui(self):
        second = False
        aov_select = nuke.Panel('Select Primary AOVs')
        for item in self.primary_aovs:
            aov_select.addBooleanCheckBox(f'{item}', False)
        display_aov_select = aov_select.show()

        for aov in self.primary_aovs:
            if aov_select.value(aov):
                self.selected_aovs_list.append(aov)
        if self.selected_aovs_list != []:
            self.check_missed()
        if display_aov_select == 0:
            return self.selected_aovs_list, display_aov_select
        else:
            aov_select = nuke.Panel('Select Secondary AOVs')
            for item in self.secondary_aovs:
                aov_select.addBooleanCheckBox(f'{item}', False)
            display_aov_select = aov_select.show()

            for aov in self.secondary_aovs:
                if aov_select.value(aov):
                    self.selected_aovs_list.append(aov)
                    second = True

            if self.selected_aovs_list != [] and second is True:
                self.check_missed()

            if display_aov_select == 0:
                return self.selected_aovs_list, display_aov_select

        return self.selected_aovs_list, display_aov_select


def group_make():
    group = nuke.nodes.Group(name="AOV_GRP", postage_stamp=True)
    group.knob("tile_color").setValue(0x6aff55ff)
    return group


def make_overblack(ref_node):
    overblack_group = nuke.nodes.Group(name="Overblack", xpos=ref_node['xpos'].value() - 1000,
                                       ypos=ref_node['ypos'].value())
    overblack_group.knob('tile_color').setValue(0xff)

    with overblack_group:
        ob_const = nuke.nodes.Constant()
        ob_input = nuke.nodes.Input()
        ob_out = nuke.nodes.Output()
        ob_merge = nuke.nodes.Merge()
        ob_merge.setInput(0, ob_input)
        ob_merge.setInput(1, ob_const)
        ob_out.setInput(0, ob_merge)

    overblack_group.setInput(0, ref_node)
    return overblack_group


def make_top_line(group_node):
    with group_node:
        input_node = nuke.nodes.Input(name="InputMain", xpos=0, ypos=0)

        input_dot = nuke.nodes.Dot(xpos=input_node['xpos'].value(), ypos=input_node['ypos'].value() + 400)
        input_dot.setInput(0, input_node)

        copy_alpha_dot = nuke.nodes.Dot(xpos=input_dot['xpos'].value() + 400, ypos=input_dot['ypos'].value())
        copy_alpha_dot.setInput(0, input_dot)

        overblack_node = make_overblack(input_dot)

        unpre_dot_start = nuke.nodes.Dot(xpos=overblack_node['xpos'].value() - 1600,
                                         ypos=overblack_node['ypos'].value())
        unpre_dot_start.setInput(0, overblack_node)

        shuf_dot_start = nuke.nodes.Dot(xpos=unpre_dot_start['xpos'].value() - 300,
                                        ypos=unpre_dot_start['ypos'].value())
        shuf_dot_start.setInput(0, unpre_dot_start)
        alpha_shuff = nuke.nodes.Shuffle2(name="AlphaShuffle", xpos=input_dot['xpos'].value(),
                                          ypos=input_dot['ypos'].value() + 100)
        alpha_shuff.setInput(0, input_dot)
        alpha_shuff.knob('in1').setValue('alpha')
        alpha_shuff.knob('out1').setValue('rgba')
    return alpha_shuff, unpre_dot_start, shuf_dot_start, copy_alpha_dot


def make_aov(list_item, input_dot, unpre_dot_start, shuf_dot_start, group, make_safety):
    with group:
        if make_safety:
            safety_variables = safety_net(input_dot, unpre_dot_start, shuf_dot_start, group)
            merge_plus = safety_variables[2]
            unpre = safety_variables[1]
            shuff_dot = safety_variables[0]
            return merge_plus, unpre, shuff_dot
        else:
            shuff_dot = nuke.nodes.Dot(xpos=shuf_dot_start['xpos'].value(), ypos=shuf_dot_start['ypos'].value() + 300)
            shuff_dot.setInput(0, shuf_dot_start)

            aov_shuff = nuke.nodes.Shuffle2(name=list_item, in1=list_item, xpos=shuff_dot['xpos'].value() + 100,
                                            ypos=shuff_dot['ypos'].value())
            aov_shuff.setInput(0, shuff_dot)

            unpre = nuke.nodes.unpremult_layered(xpos=aov_shuff['xpos'].value() + 200, ypos=aov_shuff['ypos'].value())
            unpre.setInput(0, aov_shuff)
            unpre.setInput(1, unpre_dot_start)

            pre_mult = nuke.nodes.Premult(xpos=unpre['xpos'].value() + 2500, ypos=unpre['ypos'].value())
            pre_mult.setInput(0, unpre)

            merge_plus = nuke.nodes.Merge(name=f"{list_item} merge", operation="plus",
                                          xpos=pre_mult['xpos'].value() + 100,
                                          ypos=pre_mult['ypos'].value())
            if list_item.split("_")[0] != 'RGBA':
                merge_from = nuke.nodes.Merge(name=f"{list_item} merge", operation="from",
                                              xpos=pre_mult['xpos'].value() + 100,
                                              ypos=merge_plus['ypos'].value() - 50)
                merge_from.setInput(1, pre_mult)
                merge_from.setInput(0, input_dot)
                merge_plus.setInput(1, pre_mult)
                merge_plus.setInput(0, merge_from)
            else:
                merge_plus.setInput(1, pre_mult)
                merge_plus.setInput(0, input_dot)

            make_backdrop(list_item, shuff_dot, group)
        return merge_plus, unpre, shuff_dot


def make_backdrop(list_item, shuf_dot_start, group):
    with group:
        backdrop = nuke.nodes.BackdropNode(label=list_item, note_font="DejaVu Sans", note_font_size=50, z_order=1,
                                           appearance="Border", xpos=shuf_dot_start['xpos'].value() - 50,
                                           ypos=shuf_dot_start['ypos'].value() - 100)

        backdrop.knob("bdwidth").setValue(3200)
        backdrop.knob("bdheight").setValue(268)
        if list_item.split("_")[0] == "RGBA":
            backdrop.knob("tile_color").setValue(0x59ccccff)
        elif make_safety:
            backdrop.knob("tile_color").setValue(0xff5f92ff)
        else:
            backdrop.knob("tile_color").setValue(0x7f66e5ff)


def end_aov_list(group, merge_plus, copy_alpha_dot):
    with group:
        copy_alpha = nuke.nodes.Copy(name='copyAlpha', xpos=merge_plus['xpos'].value(),
                                     ypos=merge_plus['ypos'].value() + 250)
        copy_alpha.knob('from0').setValue('rgba.alpha')
        copy_alpha.knob('to0').setValue('rgba.alpha')
        alpha_dot = nuke.nodes.Dot(xpos=copy_alpha['xpos'].value() + 400, ypos=copy_alpha['ypos'].value())
        alpha_dot.setInput(0, copy_alpha_dot)
        copy_alpha.setInput(0, merge_plus)
        copy_alpha.setInput(1, alpha_dot)
        output = nuke.nodes.Output(xpos=copy_alpha['xpos'].value(), ypos=copy_alpha['ypos'].value() + 250)
        output.setInput(0, copy_alpha)
        nuke.nodes.Input(name='Mask Input', xpos=copy_alpha['xpos'].value() - 200,
                         ypos=copy_alpha['ypos'].value() + 100)


def safety_net(merge_plus, unpre, shuff_dot, group):
    with group:
        safety_shuff_dot = nuke.nodes.Dot(xpos=shuff_dot['xpos'].value(), ypos=shuff_dot['ypos'].value() + 300)
        safety_shuff_dot.setInput(0, shuff_dot)

        shuff_list = nuke.allNodes(filter="Shuffle2")
        for node in shuff_list:
            if node.knob("name").value() == "AlphaShuffle":
                shuff_list.remove(node)
        safety_merge = nuke.nodes.Merge2(name='safety_merge', operation='plus',
                                         xpos=safety_shuff_dot['xpos'].value() + 50,
                                         ypos=safety_shuff_dot['ypos'].value())
        for i in range(len(shuff_list)):
            if i < 2:
                safety_merge.setInput(i, shuff_list[i])
            elif i >= 2:
                safety_merge.setInput(i + 1, shuff_list[i])

        safety_merge.knob("hide_input").setValue(True)

        diff_merge = nuke.nodes.Merge(operation='difference', xpos=safety_merge['xpos'].value() + 100,
                                      ypos=safety_merge['ypos'].value())
        diff_merge.setInput(1, shuff_dot)
        diff_merge.setInput(0, safety_merge)

        safety_unpre = nuke.nodes.unpremult_layered(xpos=diff_merge['xpos'].value() + 150,
                                                    ypos=diff_merge['ypos'].value())
        safety_unpre.setInput(0, diff_merge)
        safety_unpre.setInput(1, unpre)

        pre_mult = nuke.nodes.Premult(xpos=safety_unpre['xpos'].value() + 2500, ypos=safety_unpre['ypos'].value())
        pre_mult.setInput(0, safety_unpre)

        safety_merge_plus = nuke.nodes.Merge(name="safety merge", operation="plus", xpos=pre_mult['xpos'].value() + 100,
                                             ypos=pre_mult['ypos'].value())
        safety_merge_plus.setInput(1, pre_mult)
        safety_merge_plus.setInput(0, merge_plus)
        make_backdrop("safety_net", safety_shuff_dot, group)
    return safety_shuff_dot, safety_unpre, safety_merge_plus


ui = Setup()
layer_lists = ui.create_layer_lists()
button_tests = ui.create_ui()

if button_tests[1] == 1 and button_tests[0] != []:
    make_safety = False
    count = 0
    aov = ()
    grp = group_make()
    top_line = make_top_line(grp)
    channel_list = button_tests[0]
    print(channel_list)
    for i in range(len(channel_list)):
        if i == 0 and channel_list[i].split("_")[0] != "RGBA":
            count += 1
            make_safety = True
            aov = make_aov(channel_list[i], top_line[0], top_line[1], top_line[2], grp, make_safety)
            make_safety = False
            aov = make_aov(channel_list[i], aov[0], aov[1], aov[2], grp, make_safety)
        elif i == 0:
            aov = make_aov(channel_list[i], top_line[0], top_line[1], top_line[2], grp, make_safety)
        else:
            if i == len(channel_list)-1 and channel_list[i].split("_")[0] == "RGBA":
                aov = make_aov(channel_list[i], aov[0], aov[1], aov[2], grp, make_safety)
                make_safety = True
                aov = make_aov(channel_list[i], aov[0], aov[1], aov[2], grp, make_safety)
                make_safety = False
            else:
                if channel_list[i].split("_")[0] != "RGBA":
                    count += 1
                    if count == 1:
                        make_safety = True
                        aov = make_aov(channel_list[i], aov[0], aov[1], aov[2], grp, make_safety)
                        make_safety = False
                aov = make_aov(channel_list[i], aov[0], aov[1], aov[2], grp, make_safety)
    end_aov_list(grp, aov[0], top_line[3])
else:
    nuke.message("No AOV groups selected.")
