import random, time, math, datetime, os
from Constants import *

water_duration = 3600 * 24
death_duration = 6 * water_duration
stage_factors = (1, 3, 10, 20, 30)
indicator_squares = 6
mutation_rarity = 20000 # Increase this # to make mutation rarer (chance 1 out of x each second)
max_plant_rarity = 256.0

class Plant(object):
    # This is your plant!
    def __init__(self, owner, generation=1):
        # Constructor
        self.points = 0 # one point per second
        self.life_stages = tuple(st * water_duration for st in stage_factors)
        self.stage = 0
        self.mutation = 0
        self.species = random.randint(0, len(species_list) - 1)
        self.color = random.randint(0, len(color_list) - 1)
        self.name = plant_names[random.randint(0, len(plant_names) - 1)]
        self.rarity = self.rarity_check()
        self.ticks = 0
        self.generation = generation
        self.generation_bonus = 1 + (0.2 * (generation - 1))
        self.dead = False
        self.owner = owner
        self.start_time = int(time.time())
        self.last_update = self.start_time
        self.last_water = self.start_time - water_duration

    def update(self):
        now = int(time.time())
        water_delta = now - self.last_water
        if water_delta > death_duration:
            self.dead = True
            return
    
        increase = min(water_delta, water_duration) - min(self.last_update - self.last_water, water_duration)

        if increase != 0:
            self.points += increase
            self.mutate_check(increase)

        stages = tuple(th / self.generation_bonus for th in self.life_stages) # bonus is applied to stage thresholds
        count = 0
        closest = None
        delta = self.points

        for n in stages:
            if (n <= delta and (closest is None or (delta - n) < (delta - closest))):
                closest = n
                count += 1

        self.stage = count
        self.last_update = now
        
    def parse_plant(self):
        # Converts plant data to human-readable format
        output = ""
        if self.stage >= 3:
            output += rarity_list[self.rarity] + " "
        if self.mutation != 0:
            output += mutation_list[self.mutation] + " "
        if self.stage >= 4:
            output += color_list[self.color] + " "
        output += stage_list[self.stage] + " "
        if self.stage >= 2:
            output += species_list[self.species] + " "
        return output.strip()

    def rarity_check(self):
        # Generate plant rarity
        rare_seed = random.randint(1,max_plant_rarity)
        common_range =    round((2.0 / 3) * max_plant_rarity)
        uncommon_range =  round((2.0 / 3) * (max_plant_rarity - common_range))
        rare_range =      round((2.0 / 3) * (max_plant_rarity - common_range - uncommon_range))
        legendary_range = round((2.0 / 3) * (max_plant_rarity - common_range - uncommon_range - rare_range))

        common_max = common_range
        uncommon_max = common_max + uncommon_range
        rare_max = uncommon_max + rare_range
        legendary_max = rare_max + legendary_range
        godly_max = max_plant_rarity

        if 0 <= rare_seed <= common_max:
            return 0
        elif common_max < rare_seed <= uncommon_max:
            return 1
        elif uncommon_max < rare_seed <= rare_max:
            return 2
        elif rare_max < rare_seed <= legendary_max:
            return 3
        elif legendary_max < rare_seed <= godly_max:
            return 4

    def mutate_check(self, increase):
        # Create plant mutation
        mutation_seed = random.randint(increase, mutation_rarity)
        if mutation_seed == mutation_rarity:
            # mutation gained!
            mutation = random.randint(0, len(self.mutation_list) - 1)
            if self.mutation == 0:
                self.mutation = mutation
                return True
        else:
            return False

    def water(self):
        if not self.dead:
            self.last_water = int(time.time())

    def start_over(self):
        next_generation = self.generation if self.dead else self.generation + 1
        self.__init__(self.owner, next_generation)

def get_plant_water(plant: Plant):
    water_delta = int(time.time()) - plant.last_water
    water_left_pct = max(0, 1 - (water_delta/water_duration))
    water_left = int(math.ceil(water_left_pct * indicator_squares))
    return f"{water_left * '🟦'}{'⬛' * (indicator_squares - water_left)} {str(round(water_left_pct * 100))}% "

def get_plant_description(plant: Plant):
    output_text = ""
    this_species = species_list[plant.species]
    this_color = color_list[plant.color]
    this_stage = plant.stage
    
    if plant.dead:
            this_stage = 99
    try:
        description_num = random.randint(0,len(stage_descriptions[this_stage]) - 1)
    except KeyError as e:
        print(e)
        description_num = 0
    # If not fully grown
    if this_stage <= 4:
        # Growth hint
        if this_stage >= 1:
            last_growth_at = plant.life_stages[this_stage - 1]
        else:
            last_growth_at = 0
        ticks_since_last = plant.ticks - last_growth_at
        ticks_between_stage = plant.life_stages[this_stage] - last_growth_at
        if ticks_since_last >= ticks_between_stage * 0.8:
            output_text += "You notice your plant looks different.\n"

    output_text += get_stage_description(this_stage, description_num, this_species, this_color) + "\n"

    # if seedling
    if this_stage == 1:
        species_options = [species_list[plant.species],
                species_list[(plant.species+3) % len(species_list)],
                species_list[(plant.species-3) % len(species_list)]]
        random.shuffle(species_options)
        plant_hint = "It could be a(n) " + species_options[0] + ", " + species_options[1] + ", or " + species_options[2]
        output_text += plant_hint + ".\n"

    # if young plant
    if this_stage == 2:
        if plant.rarity >= 2:
            rarity_hint = "You feel like your plant is special."
            output_text += rarity_hint + ".\n"

    # if mature plant
    if this_stage == 3:
        color_options = [color_list[plant.color],
                color_list[(plant.color+3) % len(color_list)],
                color_list[(plant.color-3) % len(color_list)]]
        random.shuffle(color_options)
        return "You can see the first hints of " + color_options[0] + ", " + color_options[1] + ", or " + color_options[2]

    return output_text

def get_art_filename(plant: Plant):
    if plant.dead == True: return 'rip.txt'
    if datetime.date.today().month == 10 and datetime.date.today().day == 31: return 'jackolantern.txt'
    if plant.stage == 0: return 'seed.txt'
    if plant.stage == 1: return 'seedling.txt'
    if plant.stage == 2: return plant_art_list[plant.species]+'1.txt'
    if plant.stage == 3 or plant.stage == 5: return plant_art_list[plant.species]+'2.txt'
    if plant.stage == 4: return plant_art_list[plant.species]+'3.txt'
    return "template.txt"

def get_plant_art(plant: Plant):
    filename = get_art_filename(plant)
    # Prints ASCII art from file at given coordinates
    this_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "art")
    this_filename = os.path.join(this_dir, filename)
    this_file = open(this_filename,"r")
    this_string = this_file.read()
    this_file.close()
    return this_string

def get_plant_info(plant: Plant):
    return f'''
{get_plant_description(plant)}
```{get_plant_art(plant)}```
{plant.name}, the {plant.parse_plant()}

{get_plant_water(plant)}

Points: {plant.points}
Bonus: x{plant.generation_bonus - 1}
Owner: {plant.owner}
'''