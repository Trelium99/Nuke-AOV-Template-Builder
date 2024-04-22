class Setup:

    def __init__(self):
        self.primary_aovs = []
        self.secondary_aovs = []
        self.channel_list = nuke.layers()
        self.selected_aovs_list = []
        self.missed_aovs = []

    def create_layer_lists(self): #here is where I mentioned having to do some manual handling to create lists based on JCs preference
        for item in self.channel_list: #i think here if we can agree on a naming convention this wont be an issue
            if item.split("_")[0] == "RGBA":
                self.primary_aovs.append(item)
            elif item == 'coat' or item == 'sheen' or item == 'specular' or item == 'sss' or item == 'volume' or \
                    item.split("_")[0] == 'diffuse' or item.split("_")[0] == 'specular' or item.split("_")[
                0] == "sss" or item == 'emission':
                self.secondary_aovs.append(item)
            else:
                if item.split("_")[0] != "crypto" and item != 'rgba' and item != 'alpha' and item != 'rgb':
                    self.missed_aovs.append(item)
        return self.primary_aovs, self.secondary_aovs, self.missed_aovs #so I do build some preliminary lists but also ask the artist to make sure its got everything.

    def check_missed(self, name):
        aov_select = nuke.Panel(f'Did we miss any {name} AOVS?')
        aov_select.setWidth(300)
        for item in self.missed_aovs:
            aov_select.addBooleanCheckBox(f"{item}", False)
        aov_select.show()
        for aov in self.missed_aovs:
            if aov_select.value(aov):
                self.selected_aovs_list.append(aov)
                self.missed_aovs.remove(aov)

    def create_ui(self): #makes the pop up UI for the artists
        second = False
        aov_select = nuke.Panel('Select Primary AOVs')
        for item in self.primary_aovs:
            aov_select.addBooleanCheckBox(f'{item}', False)
        display_aov_select = aov_select.show()

        for aov in self.primary_aovs:
            if aov_select.value(aov):
                self.selected_aovs_list.append(aov)
        if self.selected_aovs_list != []:
            self.check_missed(name="Primary")
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
                self.check_missed(name="Secondary")

            if display_aov_select == 0:
                return self.selected_aovs_list, display_aov_select

        return self.selected_aovs_list, display_aov_select