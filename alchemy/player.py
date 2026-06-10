class Player:

    def __init__(self, 
                 skill=15, 
                 fortify=0, 
                 alchemist_perk_level=0, 
                 is_physician=False, 
                 is_benefactor=False, 
                 is_poisoner=False, 
                 is_seeker=False,
                 has_purity=False):

        self.alchemy_skill = skill
        self.fortify_alchemy = fortify
        self.has_purity = has_purity

        self.alchemist_perk = alchemist_perk_level * 20
        self.physician_perk = 25 if is_physician else 0
        self.benefactor_perk = 25 if is_benefactor else 0
        self.poisoner_perk = 25 if is_poisoner else 0
        self.seeker_of_shadows = 10 if is_seeker else 0

    def __repr__(self):
        return (f"Player(skill={self.alchemy_skill}, fortify={self.fortify_alchemy}, "
                f"alchemist={self.alchemist_perk}%, physician={self.physician_perk > 0}, "
                f"benefactor={self.benefactor_perk > 0}, poisoner={self.poisoner_perk > 0})")

