#!/usr/bin/env python
from ants import *
import logging
import random
import string
import copy

class Ant:

    def __init__(self):
        self.location = {}
        self.job = ''
        self.job_ttl = 0
        self.target_location = {}

class MyBot:

    def __init__(self):
        pass

    def do_setup(self, ants):
        self.ants = ants
        self.ants_born = {}
        self.waypoints = []
        self.ants_in_waypoints = {}
        for row in range(0, ants.rows, 10):
            for col in range(0, ants.cols, 10):
                self.waypoints.append((row, col))
        self.log(self.waypoints)

    # utils

    def log(self, log_str):
        logging.error(log_str)

    def randstring(self):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(5))

    # strategies

    def update_position(self, born_ant, new_loc):
        loc = self.ants_born[born_ant].location
        self.ants_born[born_ant].location = new_loc
        self.log(str(loc) + ' -> ' + str(new_loc))

    # just move one to n,s,e,w
    def do_move_direction(self, born_ant, direction):
        loc = self.ants_born[born_ant].location
        new_loc = self.ants.destination(loc, direction)
        if (self.ants.unoccupied(new_loc) and new_loc not in self.orders):
            self.ants.issue_order((loc, direction))
            self.orders[new_loc] = loc
            self.update_position(born_ant, new_loc)
            return True
        else:
            return False

    # move to destination, autodirection
    def do_move_location(self, born_ant, dest):
        loc = self.ants_born[born_ant].location
        directions = self.ants.direction(loc, dest) #calculates direction to destination
        for direction in directions:
            if self.do_move_direction(born_ant, direction):
                return True
        return False

    # give newborns a name, remove dead ants
    def incubator(self):
        for ant_loc in self.ants.my_ants():
            # loop tru ants, check ant.future_location - when not found in loop, its new
            ant_found = False
            for born_ant in self.ants_born:
                if self.ants_born[born_ant].location == ant_loc:
                    ant_found = True
                    break

            if not ant_found:
                a = Ant()
                a.location = ant_loc
                randstring = self.randstring()
                self.ants_born[randstring] = a
                self.log('new ant detected: ' + str(a.location))

        # detect dead ants
        new_ants_born = copy.deepcopy(self.ants_born)
        for born_ant in self.ants_born:
            if self.ants_born[born_ant].location not in self.ants.my_ants():
                self.log('dead ant detected: ' + str(self.ants_born[born_ant].location))
                del new_ants_born[born_ant]
                self.ants_born = new_ants_born

    def get_hunted_food(self):
        for foodant in self.ants_born:
            target_location = self.ants_born[foodant].target_location
            self.hunted_food.append(target_location)
        return self.hunted_food

    def get_nearest_food(self, born_ant):
        ant_dist = []
        for food_loc in self.ants.food():
            for thisant in self.ants_born:
                ant_loc = self.ants_born[thisant].location
                dist = self.ants.distance(ant_loc, food_loc)
                ant_dist.append((dist, thisant, food_loc))
        ant_dist.sort()
        ret = None
        for dist, thisant, food_loc in ant_dist:
            if born_ant == thisant and food_loc not in self.get_hunted_food() and ret == None:
                ret = (dist, food_loc)
                break
        return ret

    def get_nearest_waypoints(self, loc):
        wp_dist = []
        for wp_loc in self.waypoints:
            dist = self.ants.distance(loc, wp_loc)
            wp_dist.append((dist, wp_loc))
        wp_dist.sort()
        ret = []
        for dist, wp_loc in wp_dist:
            ret.append((dist, wp_loc))
        return ret

    def get_guards_for_waypoint(self, wp_loc):
        wp_count = 0
        for born_ant in self.ants_born:
            if self.ants_born[born_ant].job == 'wp_guard' and self.ants_born[born_ant].target_location == wp_loc:
                wp_count += 1
        return wp_count

    def assign_job(self, born_ant):
        nearest_food = self.get_nearest_food(born_ant)
        if nearest_food != None:
            (dist, food_loc) = nearest_food
            self.ants_born[born_ant].job = 'goto'
            self.ants_born[born_ant].job_ttl = dist
            self.ants_born[born_ant].target_location = food_loc
        else:
            nearest_waypoints = self.get_nearest_waypoints(self.ants_born[born_ant].location)
            if nearest_waypoints != None:
                for (dist, wp_loc) in nearest_waypoints:
                    # count guards for waypoint
                    wp_count = self.get_guards_for_waypoint(wp_loc)
                    self.log('waypoint: ' + str(wp_loc) + ', wp_count: ' + str(wp_count))
                    if wp_count <= 2:
                        self.ants_born[born_ant].job = 'wp_guard'
                        self.ants_born[born_ant].job_ttl = dist
                        self.ants_born[born_ant].target_location = wp_loc
                        break

    def execute(self, born_ant):

        # execute jobs
        job = self.ants_born[born_ant].job
        if job == 'goto':
            target_location = self.ants_born[born_ant].target_location
            self.do_move_location(born_ant, target_location)

        if job == 'wp_guard':
            target_location = self.ants_born[born_ant].target_location
            self.do_move_location(born_ant, target_location)

        self.ants_born[born_ant].job_ttl -= 1

    # do turn

    def do_turn(self, ants):
        self.log('round start')

        # init round vars
        self.orders = {} #key: destination tuple. value: location of the ant tuple
        self.hunted_food = [] #todo: evtl sinnlos; globaler machen

        # check count & bear ants
        current_ants_count = len(ants.my_ants())
        ants_born_count = len(self.ants_born)
        if current_ants_count != ants_born_count:
            self.incubator()

        # assign & execute jobs
        for born_ant in self.ants_born:
            if self.ants_born[born_ant].job_ttl <= 0:
                self.assign_job(born_ant)

            self.log('\n')
            self.log('ant name: ' + str(born_ant))
            self.log('location: ' + str(self.ants_born[born_ant].location))
            self.log('job: ' + str(self.ants_born[born_ant].job))
            self.log('job_ttl: ' + str(self.ants_born[born_ant].job_ttl))
            self.log('target_location: ' + str(self.ants_born[born_ant].target_location))
            self.log('\n')

            self.execute(born_ant)

        self.log('round end.\n')

if __name__ == '__main__':
    # psyco will speed up python a little, but is not needed
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(MyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
