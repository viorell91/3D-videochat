#!/usr/bin/python

### import guacamole libraries ###
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
import avango.daemon

### import framework libraries ###
from lib.Intersection import *

### import python libraries ###
# ...

import copy


class ManipulationManagerScript(avango.script.Script):

    ## input fields
    sf_key_1 = avango.SFBool()
    sf_key_front = avango.SFBool()
    sf_key_center = avango.SFBool()
    sf_key_back = avango.SFBool()


    ## constructor
    def __init__(self):
        self.super(ManipulationManagerScript).__init__()

        ### external references ###
        self.CLASS = None # is set later

        ### resources ###


    
    def my_constructor(self, CLASS):
        self.CLASS = CLASS
        self.sf_key_1.connect_from(self.CLASS.keyboard_sensor.Button12) # key 1
        self.sf_key_front.connect_from(self.CLASS.pointer_device_sensor.Button0)
        #print(self.CLASS.pointer_device_sensor.Button0)


    ### callbacks ###
    @field_has_changed(sf_key_1)
    def sf_key_1_changed(self):
        if self.sf_key_1.value == True and self.CLASS is not None: # key is pressed
            self.CLASS.set_manipulation_technique(0) # switch to Virtual-Ray manipulation technique

    @field_has_changed(sf_key_front)
    def sf_key_front_changed(self):
        if self.sf_key_front.value == True and self.CLASS is not None: # key is pressed
            print("pressed")
        else:
            print("not pressed")

        

class ManipulationManager:

    ## constructor
    def __init__( self
                , SCENEGRAPH = None
                , PARENT_NODE = None
                , POINTER_TRACKING_STATION = ""
                , TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat()
                , POINTER_DEVICE_STATION = ""
                , HEAD_NODE = None
                ):


        ### external references ###
        self.HEAD_NODE = HEAD_NODE
        

        ### variables ###
        self.active_manipulation_technique = None


        ### resources ###
    
        ## init intersection
        self.intersection_ray = Intersection(SCENEGRAPH = SCENEGRAPH, WHITE_LIST = ["moveable"])
        self.intersection_falling = Intersection(SCENEGRAPH = SCENEGRAPH, BLACK_LIST = ["invisible"])

        ## init sensors
        self.pointer_tracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.pointer_tracking_sensor.Station.value = POINTER_TRACKING_STATION
        self.pointer_tracking_sensor.TransmitterOffset.value = TRACKING_TRANSMITTER_OFFSET
            
        self.pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.pointer_device_sensor.Station.value = POINTER_DEVICE_STATION
        print("Button", self.pointer_device_sensor.Button0)

        self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_sensor.Station.value = "device-keyboard"

        ## init manipulation techniques
        self.virtualRay = VirtualRay()
        self.virtualRay.my_constructor(MANIPULATION_MANAGER = self, PARENT_NODE = PARENT_NODE)

        
        ## init script    
        self.script = ManipulationManagerScript()
        self.script.my_constructor(self)


        ### set initial states ###
        self.set_manipulation_technique(0) # switch to virtual-ray manipulation technique


    ### functions ###
    def set_manipulation_technique(self, INT):
        # evtl. disable prior technique
        if self.active_manipulation_technique is not None:
            self.active_manipulation_technique.enable(False)
    
        # enable new technique
        if INT == 0: # virtual-ray
            print("switch to virtual-ray technique")
            self.active_manipulation_technique = self.virtualRay

        self.active_manipulation_technique.enable(True)



class ManipulationTechnique(avango.script.Script):

    ## input fields
    sf_drag_button = avango.SFBool()
    sf_drag_button_not_falling = avango.SFBool()

    ## constructor
    def __init__(self):
        self.super(ManipulationTechnique).__init__()
               

    def my_constructor( self
                      , MANIPULATION_MANAGER = None
                      , PARENT_NODE = None
                      ):

        ### external references ###
        self.MANIPULATION_MANAGER = MANIPULATION_MANAGER
        self.PARENT_NODE = PARENT_NODE

    
        ### variables ###
        self.enable_flag = False
        
        self.first_pick_result = None

        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()


        ### resources ###

        ## init nodes
        self.pointer_node = avango.gua.nodes.TransformNode(Name = "pointer_node")
        self.pointer_node.Transform.connect_from(MANIPULATION_MANAGER.pointer_tracking_sensor.Matrix)
        if PARENT_NODE is not None:
            PARENT_NODE.Children.value.append(self.pointer_node)
        
        self.tool_node = avango.gua.nodes.TransformNode(Name = "tool_node")
        self.tool_node.Tags.value = ["invisible"]
        self.pointer_node.Children.value.append(self.tool_node)


        ## init field connections
        self.sf_drag_button.connect_from(MANIPULATION_MANAGER.pointer_device_sensor.Button0)
        self.sf_drag_button_not_falling.connect_from(MANIPULATION_MANAGER.pointer_device_sensor.Button1)
        self.falling = True

        ## set global evaluation policy
        self.always_evaluate(True)



    ### functions ###
    def enable(self, FLAG):
        self.enable_flag = FLAG
        
        if self.enable_flag == True:
            self.tool_node.Tags.value = [] # set tool visible
        else:
            self.stop_dragging() # evtl. stop active dragging process
            
            self.tool_node.Tags.value = ["invisible"] # set tool invisible


    ### callbacks ###
    def evaluate(self):
        raise NotImplementedError("To be implemented by a subclass.")


    @field_has_changed(sf_drag_button)
    def sf_drag_button_changed(self):
        if self.enable_flag == True and self.sf_drag_button.value == True and self.first_pick_result is not None: # button pressed and intersection targetst found --> start dragging
            self.falling = True
            _node = self.first_pick_result.Object.value # get geometry node
            #print(_node, _node.Name.value)

            self.start_dragging(_node)

        elif self.sf_drag_button.value == False and self.dragged_node is not None: # button released and active dragging operation --> stop dragging
            self.stop_dragging()

    @field_has_changed(sf_drag_button_not_falling)
    def sf_drag_button_not_falling_changed(self):
        if self.enable_flag == True and self.sf_drag_button_not_falling.value == True and self.first_pick_result is not None: # button pressed and intersection targetst found --> start dragging
            self.falling = False
            self.MANIPULATION_MANAGER.virtualRay.remove_falling_objects(self.dragged_node)
            _node = self.first_pick_result.Object.value # get geometry node
            #print(_node, _node.Name.value)

            self.start_dragging(_node)

        elif self.sf_drag_button_not_falling.value == False and self.dragged_node is not None: # button released and active dragging operation --> stop dragging
            self.stop_dragging()
            
        

    ### functions ###
    def start_dragging(self, NODE):          
        #self.dragged_node = NODE
        self.dragged_node = NODE.Parent.value # take the group node of the geomtry node
        self.dragging_offset_mat = avango.gua.make_inverse_mat(self.tool_node.WorldTransform.value) * self.dragged_node.Transform.value # object transformation in pointer coordinate system

  
    def stop_dragging(self):
        print("stop dragging")
        self.MANIPULATION_MANAGER.virtualRay.add_falling_object(self.dragged_node)
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()


    def dragging(self):
        if self.dragged_node is not None: # object to drag
            self.dragged_node.Transform.value = self.tool_node.WorldTransform.value * self.dragging_offset_mat
            print("Current picked", self.dragged_node.Name)
            


class VirtualRay(ManipulationTechnique):

    ## constructor
    def __init__(self):
        self.super(VirtualRay).__init__()


    def my_constructor( self
                      , MANIPULATION_MANAGER = None                      
                      , PARENT_NODE = None
                      ):

        ManipulationTechnique.my_constructor(self, MANIPULATION_MANAGER = MANIPULATION_MANAGER, PARENT_NODE = PARENT_NODE)


        ### further parameters ###  
        self.ray_length = 2.0 # in meter
        self.ray_thickness = 0.005 # in meter

        self.intersection_point_size = 0.01 # in meter

        self.falling_attenuation = 0.01
        self.falling_objects = []

        ### further resources ###
        _loader = avango.gua.nodes.TriMeshLoader()

        self.ray_geometry = _loader.create_geometry_from_file("ray_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) * \
                                            avango.gua.make_rot_mat(-90.0,1,0,0) * \
                                            avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
        self.ray_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.tool_node.Children.value.append(self.ray_geometry)

        self.intersection_geometry = _loader.create_geometry_from_file("intersection_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.intersection_geometry.Tags.value = ["invisible"] # set geometry invisible
        self.intersection_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.tool_node.Children.value.append(self.intersection_geometry)

         

    def add_falling_object(self, NODE):
        self.falling_objects.append(NODE)
        print(self.falling_objects)

    def remove_falling_objects(self, NODE):
        self.falling_objects = []
        print(self.falling_objects)


    ### callbacks ###
    
    ## implement base class function
    def evaluate(self):

        if self.enable_flag == True:    
            ## calc intersection
            _mf_pick_result = self.MANIPULATION_MANAGER.intersection_ray.calc_pick_result(PICK_MAT = self.tool_node.WorldTransform.value, PICK_LENGTH = self.ray_length, PICK_DIRECTION = avango.gua.Vec3(0.0,0.0,-1.0))
            #print("Picked objects: ", len(_mf_pick_result.value))

            if len(_mf_pick_result.value) > 0: # intersection found
                self.first_pick_result = _mf_pick_result.value[0] # get first pick result
            
            else: # no intersection found
                self.first_pick_result = None
  
 
            if self.first_pick_result is not None:
                _point = self.first_pick_result.WorldPosition.value
                _distance = (self.tool_node.WorldTransform.value.get_translate() - _point).length()
                
                ## update ray length visualization
                self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, _distance * -0.5) * \
                                                    avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
                                                    avango.gua.make_scale_mat(self.ray_thickness, _distance, self.ray_thickness)
  

                ## update intersection point visualization
                self.intersection_geometry.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-_distance) * \
                                                             avango.gua.make_scale_mat(self.intersection_point_size)
                                                                  
                self.intersection_geometry.Tags.value = [] # set visible

            else: 
                ## set to default ray length visualization
                self.ray_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, self.ray_length * -0.5) * \
                                                    avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
                                                    avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)

                ## update intersection point visualization
                self.intersection_geometry.Tags.value = ["invisible"] # set invisible


            # evtl. drag object
            ManipulationTechnique.dragging(self)
            

            if self.falling:
                _new_list = copy.copy(self.falling_objects)

                #print(self, len(self.falling_objects))
                for _object in self.falling_objects:
                    _mf_pick_result = self.MANIPULATION_MANAGER.intersection_falling.calc_pick_result(PICK_MAT = _object.WorldTransform.value, PICK_LENGTH = 0.0034, PICK_DIRECTION = avango.gua.Vec3(0.0, -1.0 ,0.0))

                    if len(_mf_pick_result.value) > 0: # intersection found
                        _new_list.remove(_object)
                    else:
                        _object.Transform.value = avango.gua.make_trans_mat(0.0, -self.falling_attenuation, 0.0) * _object.Transform.value

                self.falling_objects = _new_list
                #print(self.falling_objects)