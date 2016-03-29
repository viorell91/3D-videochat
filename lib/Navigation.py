#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
from lib.Intersection import Intersection

import time

### import python libraries
# ...

class NavigationScript(avango.script.Script):
    #input field
    sf_button = avango.SFBool() ##

    #output field
    sf_room_number = avango.SFInt()

    ## constructor
    def __init__(self):
        self.super(NavigationScript).__init__()

        self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_sensor.Station.value = "device-keyboard"

        ## init field connections        
        self.sf_button.connect_from(self.keyboard_sensor.Button21) # R

        ### init variables
        self.CLASS = None


    def my_constructor(self, CLASS, ROOM_NUMBER):
        ### external reference
        self.CLASS = CLASS
        self.host_name = self.CLASS.host_name
        
        if self.host_name == "athena":
            self.z = 1.7
            self.rotation = 180.0
            self.deviation = 0.0 
        elif self.host_name == "eris":
            self.z = 0.6
            self.rotation = 0.0
            self.deviation = 0.8
        elif self.host_name == "arachne":
            self.z = 0.6
            self.rotation = 0.0
            self.deviation = -0.8
    

        self.round_table = avango.gua.make_rot_mat(self.rotation, 0, 1, 0) * avango.gua.make_trans_mat(0.0, 0.1, 1.2)
        self.classroom = avango.gua.make_rot_mat(self.rotation, 0, 1, 0) * avango.gua.make_trans_mat(self.deviation, 0.1, self.z)
        self.labyrinth = avango.gua.make_trans_mat(-70.2, 0.1, -35.2) * avango.gua.make_rot_mat(-90.0, 0, 1, 0)



    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.sf_button.value == True: # key pressed

            if self.CLASS is not None:
                self.CLASS.room_number = self.CLASS.room_number + 1

                if self.CLASS.room_number == 4: # round table
                    self.CLASS.room_number = 1

                    if self.host_name == "eris":
                        self.CLASS.sf_nav_mat.value = self.round_table
                    else:
                        self.CLASS.sf_nav_mat.value = avango.gua.make_rot_mat(90.0, 0, 1, 0) * self.round_table

                elif self.CLASS.room_number == 2: # labyrinth
                    self.CLASS.sf_nav_mat.value = self.labyrinth
                    self.CLASS.speed_factor = 0.3
                    self.CLASS.attenuation_factor = 2
                    self.CLASS.dist = 1.5
                        
                else: # classroom
                    #print("rotation", self.rotation.get_rotate(), "host", self.host_name)
                    self.CLASS.sf_nav_mat.value = self.classroom
                    self.CLASS.speed_factor = 0.1
                    self.CLASS.attenuation_factor = 1
                    self.CLASS.dist = 1
                    

                sf_room_number = self.CLASS.room_number
                print("room number", self.CLASS.room_number, self.host_name)
                print("position\n", self.CLASS.sf_nav_mat.value)
                


class SteeringNavigation(avango.script.Script):

    ### fields ###

    ## input fields
    mf_dof = avango.MFFloat()
    mf_dof.value = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] # init 7 channels

    ## output fields
    sf_nav_mat = avango.gua.SFMatrix4()
    sf_nav_mat.value = avango.gua.make_identity_mat()

    
    ### constructor
    def __init__(self):
        self.super(SteeringNavigation).__init__()

        ### parameters ###
        self.rot_center_offset = avango.gua.Vec3(0.0,0.0,0.0)

        self.attenuation_factor = 1.0


    def my_constructor(self, MF_DOF, ATTENUATION_FACTOR = 1.0, SCENEGRAPH = None, SCENE_ROOT = None, HOST_NAME = None):

        self.mf_dof.connect_from(MF_DOF)
        
        self.attenuation_factor = ATTENUATION_FACTOR

        self.host_name = HOST_NAME

        self.intersection = Intersection(SCENEGRAPH, BLACK_LIST = ["unpickable", "invisible"])

        self.room_number = 1
        self.speed_factor = 0.1
        self.dist = 1
        self.script = NavigationScript()
        self.script.my_constructor(CLASS = self, ROOM_NUMBER = self.room_number)


    @field_has_changed(mf_dof)
    def mf_dof_changed(self):
        ## handle translation input
        _x = self.mf_dof.value[0]
        _y = self.mf_dof.value[1]
        _z = self.mf_dof.value[2]

        _trans_vec    = avango.gua.Vec3(_x, _y, _z) * self.attenuation_factor
        _trans_input  = _trans_vec.length()
         
        if _trans_input > 0.0:

            ## transfer-function for translation
            _exponent   = 2
            _multiple   = int(_trans_input)
            _rest       = _trans_input - _multiple
            _factor     = _multiple + pow(_rest, _exponent)

          

            self.intersection.set_pick_mat(self.sf_nav_mat.value)
            self.intersection.set_pick_direction(_trans_vec)
            self.intersection.set_pick_length(20.0)
            
            _mf_pick_result = self.intersection.compute_intersection()

            _trans_vec.normalize()
            _trans_vec = _trans_vec * _factor * self.speed_factor
            
            for _pick_result in _mf_pick_result.value:
                _node = _pick_result.Object.value
                _distance = _pick_result.Distance.value * 20.0
                _world_intersection_pos = _pick_result.WorldPosition.value
                
                _distance2 = (_world_intersection_pos - self.sf_nav_mat.value.get_translate()).length()

                if _distance < self.dist: # add radius of 0.5 m
                    _trans_vec = avango.gua.Vec3(0.0, 0.0, 0.0)


        ## handle rotation input
        _rx = 0.0
        _ry = self.mf_dof.value[4]
        _rz = 0.0

        _rot_vec    = avango.gua.Vec3(_rx, _ry, _rz) * self.attenuation_factor
        _rot_input  = _rot_vec.length()


        if (_trans_input or _rot_input) and self.host_name is not "athena" > 0.0:
            ## accumulate input
            self.sf_nav_mat.value = self.sf_nav_mat.value * \
                                    avango.gua.make_trans_mat(_trans_vec) * \
                                    avango.gua.make_trans_mat(self.rot_center_offset) * \
                                    avango.gua.make_rot_mat(_rot_vec.y,0,1,0) * \
                                    avango.gua.make_rot_mat(_rot_vec.x,1,0,0) * \
                                    avango.gua.make_rot_mat(_rot_vec.z,0,0,1) * \
                                    avango.gua.make_trans_mat(self.rot_center_offset * -1)

            #print("MATRIX", self.sf_nav_mat.value)

        #print("Pos", self.sf_nav_mat.value.get_translate(), _trans_vec)


    ### functions ###
    def set_start_transformation(self, MATRIX):
        self.sf_nav_mat.value = MATRIX

  
    def set_rotation_center_offset(self, OFFSET_VEC): 
        self.rot_center_offset = OFFSET_VEC
