import random, time, math, datetime, os
from Constants import *

water_duration = 3600 # * 24
stage_factors = (1, 3, 10, 20, 30)

class Plant(object):
    # This is your plant!
    def __init__(self, owner, generation=1):
        # Constructor
        self.points = 0 # one point per second
        self.life_stages = tuple(st * water_duration for st in stage_factors)
        self.stage = 0
        self.mutation = 0
        self.species = random.randint(0,len(species_list)-1)
        self.color = random.randint(0,len(color_list)-1)
        self.rarity = self.rarity_check()
        self.ticks = 0
        self.age_formatted = "0"
        self.generation = generation
        self.generation_bonus = 1 + (0.2 * (generation - 1))
        self.dead = False
        self.owner = owner
        self.start_time = int(time.time())
        self.last_time = int(time.time())
        self.last_update = int(time.time())
        # must water plant first day
        #self.last_water = int(time.time())-(24*3600)-1
        self.last_water = int(time.time())
        self.watered_24h = True
        self.visitors = []

    def update(self):
        
        # find out stage:
        self.water_check()
        if self.dead_check(): # updates self.time_delta_watered
            return

        self.stage = find_stage(self)
        
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
        CONST_RARITY_MAX = 256.0
        rare_seed = random.randint(1,CONST_RARITY_MAX)
        common_range =    round((2.0/3)*CONST_RARITY_MAX)
        uncommon_range =  round((2.0/3)*(CONST_RARITY_MAX-common_range))
        rare_range =      round((2.0/3)*(CONST_RARITY_MAX-common_range-uncommon_range))
        legendary_range = round((2.0/3)*(CONST_RARITY_MAX-common_range-uncommon_range-rare_range))

        common_max = common_range
        uncommon_max = common_max + uncommon_range
        rare_max = uncommon_max + rare_range
        legendary_max = rare_max + legendary_range
        godly_max = CONST_RARITY_MAX

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

    def dead_check(self):
        # if it has been >5 days since watering, sorry plant is dead :(
        self.time_delta_watered = int(time.time()) - self.last_water
        if self.time_delta_watered > (5 * water_duration):
            self.dead = True
        return self.dead

    def water_check(self):
        self.time_delta_watered = int(time.time()) - self.last_water
        if self.time_delta_watered <= (water_duration):
            if not self.watered_24h:
                self.watered_24h = True
            return True
        else:
            self.watered_24h = False
            return False

    def mutate_check(self):
        # Create plant mutation
        # Increase this # to make mutation rarer (chance 1 out of x each second)
        CONST_MUTATION_RARITY = 20000
        mutation_seed = random.randint(1,CONST_MUTATION_RARITY)
        if mutation_seed == CONST_MUTATION_RARITY:
            # mutation gained!
            mutation = random.randint(0,len(self.mutation_list)-1)
            if self.mutation == 0:
                self.mutation = mutation
                return True
        else:
            return False

    def growth(self):
        # Increase plant growth stage
        if self.stage < (len(stage_list)-1):
            self.stage += 1

    def water(self):
        # Increase plant growth stage
        if not self.dead:
            self.last_water = int(time.time())
            self.watered_24h = True

    def start_over(self):
        # After plant reaches final stage, given option to restart
        # increment generation only if previous stage is final stage and plant
        # is alive
        if not self.dead:
            next_generation = self.generation + 1
        else:
            # Should this reset to 1? Seems unfair.. for now generations will
            # persist through death.
            next_generation = self.generation
        self.kill_plant()
        
        self.__init__(self.owner, next_generation)

    def kill_plant(self):
        self.dead = True

def find_stage(plant: Plant):
    now = int(time.time())
    
    res1 = min(now - plant.last_water, water_duration)
    res2 = min(plant.last_update - plant.last_water, water_duration)
    
    plant.points += max(0, res1 - res2) # max() not necessary but just in case
    
    print("generation bonus: ", plant.generation_bonus, ". increase: ", res1 - res2, "max: ", water_duration)
    plant.last_update = now
    
    stages = tuple(ti / plant.generation_bonus for ti in plant.life_stages) # bonus is applied to stage thresholds
    count = 0
    closest = None
    delta = plant.points
    
    for n in stages:
        if (n <= delta and (closest is None or (delta - n) < (delta - closest))):
            closest = n
            count += 1
            
    print("plant is in stage", count, "because it passed", closest, "seconds of life")
    return count
    
def get_plant_water(plant: Plant):
    water_delta = time.time() - plant.last_water
    water_left_pct = max(0, 1 - (water_delta/water_duration)) # 24h
    water_left = int(math.ceil(water_left_pct * 10))
    return f"{water_left * '🟦'}{'⬛' * (10 - water_left)} {str(int(water_left_pct * 100))}% "

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

def get_plant_art(plant: Plant):
    
    if plant.dead == True:
        filename = 'rip.txt'
    elif datetime.date.today().month == 10 and datetime.date.today().day == 31:
        filename = 'jackolantern.txt'
    elif plant.stage == 0:
        filename = 'seed.txt'
    elif plant.stage == 1:
        filename = 'seedling.txt'
    elif plant.stage == 2:
        filename = plant_art_list[plant.species]+'1.txt'
    elif plant.stage == 3 or plant.stage == 5:
        filename = plant_art_list[plant.species]+'2.txt'
    elif plant.stage == 4:
        filename = plant_art_list[plant.species]+'3.txt'

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
{plant.parse_plant()}

{get_plant_water(plant)}

Points: {plant.points}
Bonus: x{plant.generation_bonus - 1}
'''