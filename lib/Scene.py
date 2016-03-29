#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
from avango.script import field_has_changed

class SceneScript(avango.script.Script):
    #input field
    sf_button8 = avango.SFBool() ##

    #output field
    sf_room_number = avango.SFInt()

    ## constructor
    def __init__(self):
        self.super(SceneScript).__init__()


        self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_sensor.Station.value = "device-keyboard"

        ## init field connections        
        self.sf_button8.connect_from(self.keyboard_sensor.Button21) # v for mono or stereo  ##      


        ### init variables
        self.CLASS = None


    def my_constructor(self, CLASS, ROOM_NUMBER):

        ### external reference
        self.CLASS = CLASS
        sf_room_number = ROOM_NUMBER



    @field_has_changed(sf_button8) ##
    def sf_button8_changed(self):
        if self.sf_button8.value == True: # key pressed

            if self.CLASS is not None:
                        if self.CLASS.room_number != 3:
                            self.CLASS.room_number = self.CLASS.room_number + 1
                            if self.CLASS.room_number == 2:
                                self.CLASS.office_room.Tags.value = ["invisible"]
                                #self.CLASS.kinect_node.Tags.value = ["invisible"]
                                self.CLASS.labyrinth_room.Tags.value = []

                            else:
                                self.CLASS.labyrinth_room.Tags.value = ["invisible"]
                                self.CLASS.classroom_room.Tags.value = []
                        else:
                            self.CLASS.room_number = 1
                            self.CLASS.office_room.Tags.value = []
                            #self.CLASS.kinect_node.Tags.value = []
                            self.CLASS.classroom_room.Tags.value = ["invisible"]
                        
                        sf_room_number = self.CLASS.room_number

class Scene:

    ## constructor
    def __init__( self
                , PARENT_NODE = None
                ):


        ### resources ###

        ## init scene light
        self.scene_light = avango.gua.nodes.LightNode(Name = "scene_light", Type = avango.gua.LightType.POINT)
        self.scene_light.Color.value = avango.gua.Color(0.9, 0.9, 0.9)
        self.scene_light.Brightness.value = 15.0
        self.scene_light.Falloff.value = 1.0 # exponent
        #self.scene_light.Softness.value = 2.0
        self.scene_light.EnableShadows.value = False
        self.scene_light.ShadowMapSize.value = 512
        #self.scene_light.ShadowOffset.value = 0.002
        #self.scene_light.ShadowMaxDistance.value = 5        
        self.scene_light.Transform.value = avango.gua.make_trans_mat(0.0, 0.5, 0.0) * \
                                           avango.gua.make_rot_mat(-90.0, 1, 0, 0) * \
                                           avango.gua.make_scale_mat(2.0)
        PARENT_NODE.Children.value.append(self.scene_light)


        #SUN
        self.sun_light = avango.gua.nodes.LightNode(Name = "sun_light", Type = avango.gua.LightType.SUN)
        self.sun_light.Color.value = avango.gua.Color(0.9, 0.9, 0.9)
        self.sun_light.Brightness.value = 55.0
        self.sun_light.Falloff.value = 1.0 # exponent
        self.sun_light.EnableShadows.value = False
        self.sun_light.ShadowMapSize.value = 512       
        self.sun_light.Transform.value = avango.gua.make_trans_mat(0.0, 2.1, 0.0) * \
                                         avango.gua.make_rot_mat(-90.0, 1, 0, 0)
        PARENT_NODE.Children.value.append(self.sun_light)


        ## init scene geometries
        _trimesh_loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external tri-meshes

        ## init office
        self.office_geometry = _trimesh_loader.create_geometry_from_file("office_geometry", "../objects/office/best-office.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.office_geometry.Transform.value = avango.gua.make_trans_mat(0.0, -0.55, -0.0) * \
                                               avango.gua.make_scale_mat(0.4, 0.4, 0.4)

        '''
        for _child in self.office_geometry.Children.value:
            _child.Material.value.set_uniform("Emissivity", 1.0)
            #_child.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
            #_child.Material.value.set_uniform("Roughness", 0.5)
            #_child.Material.value.set_uniform("Metalness", 0.5)
        '''
        
        ## init table
        self.table_geometry = _trimesh_loader.create_geometry_from_file("table_geometry", "../objects/office/round_table.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.table_geometry.Transform.value = avango.gua.make_trans_mat(0.0, -0.55, 0.0) * \
                                              avango.gua.make_scale_mat(6.0, 7.0, 7.0)
        #self.table_geometry.Material.value.set_uniform("ColorMap", "../objects/office/Texture-2.jpg")
        #self.table_geometry.Material.value.set_uniform("NormalMap", "../objects/office/round_table_normal.jpg")

        ## init dish 1
        self.transform_dish = avango.gua.nodes.TransformNode()
        self.dish_geometry = _trimesh_loader.create_geometry_from_file("dish_geometry", "../objects/dish/dish.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.dish_geometry.Transform.value = avango.gua.make_trans_mat(0.45, 0.14, 0.6) * \
                                              avango.gua.make_scale_mat(0.1, 0.1, 0.1) * \
                                              avango.gua.make_scale_mat(3.0, 3.0, 3.0)
        self.dish_geometry.Material.value.set_uniform("ColorMap", "../objects/dish/red_wood.jpg")
        self.transform_dish.Children.value = [self.dish_geometry]

        ## cubes
        self.transform_all_cubes = avango.gua.nodes.TransformNode()

        ## O_atom
        self.transform_O_atom = avango.gua.nodes.TransformNode()
        self.O_atom_geometry = _trimesh_loader.create_geometry_from_file("O_atom_geometry", "../objects/classroom/h2o_molecule.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.O_atom_geometry.Transform.value = avango.gua.make_trans_mat(0.45, 0.13, -0.95) * \
                                              avango.gua.make_scale_mat(0.1, 0.1, 0.1) * \
                                              avango.gua.make_scale_mat(0.5, 0.5, 0.5)
        self.O_atom_geometry.Material.value.set_uniform("ColorMap", "../textures/cube.png")
        self.O_atom_geometry.Tags.value = ["moveable"]
        self.transform_O_atom.Children.value = [self.O_atom_geometry]

        ## H_atom
        self.transform_H1_atom = avango.gua.nodes.TransformNode()
        self.H1_atom_geometry = _trimesh_loader.create_geometry_from_file("H1_atom_geometry", "../objects/classroom/h2o_molecule.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.H1_atom_geometry.Transform.value = avango.gua.make_trans_mat(0.15, 0.13, -0.85) * \
                                              avango.gua.make_scale_mat(0.1, 0.1, 0.1) * \
                                              avango.gua.make_scale_mat(0.3, 0.3, 0.3)
        self.H1_atom_geometry.Material.value.set_uniform("ColorMap", "../textures/cube.png")
        self.H1_atom_geometry.Tags.value = ["moveable"]
        self.transform_H1_atom.Children.value = [self.H1_atom_geometry]

        ## H_atom
        self.transform_H2_atom = avango.gua.nodes.TransformNode()
        self.H2_atom_geometry = _trimesh_loader.create_geometry_from_file("H2_atom_geometry", "../objects/classroom/h2o_molecule.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.H2_atom_geometry.Transform.value = avango.gua.make_trans_mat(0.35, 0.13, -0.80) * \
                                              avango.gua.make_scale_mat(0.1, 0.1, 0.1) * \
                                              avango.gua.make_scale_mat(0.3, 0.3, 0.3)
        self.H2_atom_geometry.Material.value.set_uniform("ColorMap", "../textures/cube.png")
        self.H2_atom_geometry.Tags.value = ["moveable"]
        self.transform_H2_atom.Children.value = [self.H2_atom_geometry]

        for i in range(5):

            self.transform_cube1 = avango.gua.nodes.TransformNode()
            self.cube1_geometry = _trimesh_loader.create_geometry_from_file("cube1_geometry", "../objects/cube/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
            self.cube1_geometry.Transform.value = avango.gua.make_scale_mat(0.6, 0.6, 0.6)
            #                             avango.gua.make_scale_mat(0.05, 0.05, 0.05)
            self.cube1_geometry.Material.value.set_uniform("ColorMap", "../textures/cube.png")
            self.transform_cube1.Children.value = [self.cube1_geometry]
            self.cube1_geometry.Tags.value = ["moveable"]
            self.transform_all_cubes.Children.value.append(self.transform_cube1)



        ## init kinect video avatar
        '''
        _video_loader = avango.gua.nodes.Video3DLoader() # get video-3D loader
        #self.kinect_node = _video_loader.load("kinect_node", "/opt/kinect-resources/shot_lcd_KV2_X_5.ks")
        #self.kinect_node = _video_loader.load("kinect_node", "/opt/kinect-resources/rgbd-framework/recordings/stepptanz/stepptanz_from_charon.ks")
        self.kinect_node = _video_loader.load("kinect_node", "/opt/kinect-resources/calib_3dvc/surface_23_24_25_26.ks")
        self.kinect_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0) * \
                                           avango.gua.make_rot_mat(180.0,0,1,0) * \
                                           avango.gua.make_scale_mat(0.12)
        PARENT_NODE.Children.value.append(self.kinect_node)
        '''

        ## init labyrinth
        self.labyrinth_geometry = _trimesh_loader.create_geometry_from_file("labyrinth_geometry", "../objects/labyrinth/labyrinth-textured2.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS| avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.labyrinth_geometry.Transform.value = avango.gua.make_scale_mat(6.0, 3.0, 6.0) * \
                                                  avango.gua.make_trans_mat(0.0, -0.6, 0.0)
        
        ## init tables
        self.tables_geometry = _trimesh_loader.create_geometry_from_file("tables_geometry", "../objects/classroom/tables_distance.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS| avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.tables_geometry.Transform.value = avango.gua.make_trans_mat(0.0, -0.55, -0.0) * \
                                               avango.gua.make_scale_mat(0.3, 0.3, 0.3)


        ## init rooms
        self.office_room = avango.gua.nodes.TransformNode()
        self.office_room.Children.value = [self.office_geometry, self.table_geometry, self.transform_dish, self.transform_all_cubes]
        PARENT_NODE.Children.value.append(self.office_room)

        self.classroom_room = avango.gua.nodes.TransformNode()
        self.classroom_room.Children.value = [self.office_geometry, self.tables_geometry, self.transform_O_atom, self.transform_dish, self.transform_H1_atom, self.transform_H2_atom]
        PARENT_NODE.Children.value.append(self.classroom_room)
        self.classroom_room.Tags.value = ["invisible"]

        self.labyrinth_room = avango.gua.nodes.TransformNode()
        self.labyrinth_room.Children.value = [self.labyrinth_geometry]
        PARENT_NODE.Children.value.append(self.labyrinth_room)
        self.labyrinth_room.Tags.value = ["invisible"]

        self.room_number = 1
        self.script = SceneScript()
        self.script.my_constructor(CLASS = self, ROOM_NUMBER = self.room_number)
