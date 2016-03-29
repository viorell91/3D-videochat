#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.daemon
import avango.script
from avango.script import field_has_changed

### import application libraries
from lib.GuaVE import GuaVE
from lib.FPSGui import FPSGui


class SimpleViewingSetupScript(avango.script.Script):

    ## constructor
    def __init__(self):

        self.super(SimpleViewingSetupScript).__init__()
        self.always_evaluate(True)

        ### init variables
        self.CLASS = None


    def my_constructor(self, CLASS):
        ### external reference
        self.CLASS = CLASS

    def evaluate(self):
        if self.CLASS is not None:
            _y = self.CLASS.head_node.Transform.value.get_translate()[1]

            if _y > self.CLASS.mono_height_threshold:
                self.CLASS.set_eye_distance(0.065)
            else:
                self.CLASS.set_eye_distance(0.0) # connection to head tracking but first: static head position:
                self.CLASS.head_node.Transform.value = self.CLASS.head_pos
    

class SimpleViewingSetup:

    ### constructor
    def __init__( self
                , SCENEGRAPH = None
                , RESOLUTION = avango.gua.Vec2ui(1920, 1080) # in pixels
                , STEREO_MODE = "mono"
                , SCREEN_DIMENSIONS = avango.gua.Vec2(1.0, 1.0) # in meter
                , SCREEN_MAT = avango.gua.make_identity_mat()
                , HEADTRACKING_FLAG = False
                , TRACKING_STATION = ""
                , TRANSMITTER_OFFSET_MAT = avango.gua.make_identity_mat()
                , NAVIGATION_START_MAT = avango.gua.make_identity_mat()
                , HOSTNAME = ""
                , CLIENT_FLAG = False
                , BLACK_LIST = []
                ):
                                

        ### external references ###
        self.SCENEGRAPH = SCENEGRAPH
                                  
        ### parameters ###
        self.hostname = HOSTNAME

        self.mono_height_threshold = 0.4
        self.head_pos = avango.gua.make_trans_mat(0.0, 0.573, 1.0)
        if self.hostname == "athena":
            #teaching
            self.mono_height_threshold = 0.25
            self.head_pos = avango.gua.make_trans_mat(0.0, 0.6, 0.0)
            # sitting
            #self.mono_height_threshold = 0.15
            #self.head_pos = avango.gua.make_trans_mat(0.0, 0.6, 0.0)
        
        
        ### resources ###
        
        self.shell = GuaVE()

        ## init window
        self.window = avango.gua.nodes.GlfwWindow(Title = "window")
        #self.window.EnableFullscreen.value = True
        self.window.Size.value = RESOLUTION
        self.window.LeftResolution.value = RESOLUTION
        
        avango.gua.register_window(self.window.Title.value, self.window) 


        ## init viewer
        self.viewer = avango.gua.nodes.Viewer()
        self.viewer.SceneGraphs.value = [SCENEGRAPH]
        self.viewer.Windows.value = [self.window]
        #self.viewer.DesiredFPS.value = 60.0 # in Hz


        ## init passes & render pipeline description
        self.resolve_pass = avango.gua.nodes.ResolvePassDescription()
        self.resolve_pass.EnableSSAO.value = False
        self.resolve_pass.SSAOIntensity.value = 3.0
        self.resolve_pass.SSAOFalloff.value = 10.0
        self.resolve_pass.SSAORadius.value = 2.0
        #self.resolve_pass.EnableScreenSpaceShadow.value = True
        self.resolve_pass.EnvironmentLightingColor.value = avango.gua.Color(0.2, 0.2, 0.2)
        self.resolve_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
        self.resolve_pass.Exposure.value = 1.0

        #self.resolve_pass.BackgroundMode.value = avango.gua.BackgroundMode.COLOR
        #self.resolve_pass.BackgroundColor.value = avango.gua.Color(0.45, 0.5, 0.6)
        self.resolve_pass.BackgroundMode.value = avango.gua.BackgroundMode.SKYMAP_TEXTURE
        #self.resolve_pass.BackgroundTexture.value = "/opt/guacamole/resources/skymaps/DH216SN.png"
        #self.resolve_pass.BackgroundTexture.value = "/opt/guacamole/resources/skymaps/warehouse.jpg"
        #self.resolve_pass.BackgroundTexture.value = "/opt/guacamole/resources/skymaps/bath.jpg"
        self.resolve_pass.BackgroundTexture.value = "/opt/kinect-resources/calib_3dvc/skype_3D/textures/skymap.png"        
        

        self.pipeline_description = avango.gua.nodes.PipelineDescription(Passes = [])
        self.pipeline_description.EnableABuffer.value = False
        self.pipeline_description.Passes.value.append(avango.gua.nodes.TriMeshPassDescription())
        self.pipeline_description.Passes.value.append(avango.gua.nodes.Video3DPassDescription())
        #self.pipeline_description.Passes.value.append(avango.gua.nodes.TexturedQuadPassDescription())
        self.pipeline_description.Passes.value.append(avango.gua.nodes.LightVisibilityPassDescription())
        #self.pipeline_description.Passes.value.append(avango.gua.nodes.BBoxPassDescription())
        self.pipeline_description.Passes.value.append(self.resolve_pass)
        self.pipeline_description.Passes.value.append(avango.gua.nodes.TexturedScreenSpaceQuadPassDescription())               
        self.pipeline_description.Passes.value.append(avango.gua.nodes.SSAAPassDescription())


        self.navigation_node = avango.gua.nodes.TransformNode(Name = "{0}_navigation_node".format(self.hostname))
        SCENEGRAPH.Root.value.Children.value.append(self.navigation_node)
        self.navigation_node.Transform.value = NAVIGATION_START_MAT

        '''
        ## init navigation geometry
        _trimesh_loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external tri-meshes            

        self.navigation_geometry = _trimesh_loader.create_geometry_from_file("{0}_navigation_geometry".format(self.hostname), "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.navigation_geometry.Transform.value = avango.gua.make_scale_mat(1.0)
        self.navigation_node.Children.value.append(self.navigation_geometry)
        '''
        
        ## init head node
        self.head_node = avango.gua.nodes.TransformNode(Name = "head_node")
        self.head_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.6)
        self.navigation_node.Children.value.append(self.head_node)

        if HEADTRACKING_FLAG == True:
            self.headtracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
            self.headtracking_sensor.Station.value = TRACKING_STATION
            self.headtracking_sensor.TransmitterOffset.value = TRANSMITTER_OFFSET_MAT
            self.headtracking_sensor.ReceiverOffset.value = avango.gua.make_identity_mat()

            self.head_node.Transform.connect_from(self.headtracking_sensor.Matrix)
            #print(self.headtracking_sensor.Matrix)


        ## init screen node
        self.screen_node = avango.gua.nodes.ScreenNode(Name = "screen_node")
        self.screen_node.Width.value = SCREEN_DIMENSIONS.x
        self.screen_node.Height.value = SCREEN_DIMENSIONS.y
        self.screen_node.Transform.value = SCREEN_MAT
        self.navigation_node.Children.value.append(self.screen_node)
        

        ## init camera node
        self.camera_node = avango.gua.nodes.CameraNode(Name = "camera_node")
        self.camera_node.SceneGraph.value = SCENEGRAPH.Name.value
        self.camera_node.LeftScreenPath.value = self.screen_node.Path.value
        self.camera_node.RightScreenPath.value = self.screen_node.Path.value
        self.camera_node.NearClip.value = 0.1 # in meter
        self.camera_node.FarClip.value = 100.0 # in meter
        self.camera_node.Resolution.value = RESOLUTION
        self.camera_node.OutputWindowName.value = self.window.Title.value
        self.camera_node.PipelineDescription.value = self.pipeline_description
        self.camera_node.BlackList.value = BLACK_LIST
        
        self.head_node.Children.value = [self.camera_node]

        #print("stereo mode", STEREO_MODE)
        if STEREO_MODE == "anaglyph":
            self.camera_node.EnableStereo.value = True

            self.window.StereoMode.value = avango.gua.StereoMode.ANAGLYPH_RED_CYAN
            self.window.RightResolution.value = RESOLUTION

            self.set_eye_distance(0.064)

        elif STEREO_MODE == "checkerboard":
            self.camera_node.EnableStereo.value = True

            self.window.StereoMode.value = avango.gua.StereoMode.CHECKERBOARD
            self.window.RightResolution.value = RESOLUTION

            self.set_eye_distance(0.064)

        elif STEREO_MODE == "SIDE_BY_SIDE":
            self.camera_node.EnableStereo.value = True
            
            self.window.StereoMode.value = avango.gua.StereoMode.SIDE_BY_SIDE

            self.window.Size.value = avango.gua.Vec2ui(1920*2, 1200)

            #print("offsetMat", TRANSMITTER_OFFSET_MAT)

            #self.head_node.Transform.value.get_translate()[1] = self.head_node.Transform.value.get_translate()[1] + 20

            self.window.LeftResolution.value = avango.gua.Vec2ui(1780, 1185)
            self.window.LeftPosition.value = avango.gua.Vec2ui(140, 0)
            self.window.RightResolution.value = avango.gua.Vec2ui(1780, 1185)
            self.window.RightPosition.value = avango.gua.Vec2ui(1920, 0)

            self.set_eye_distance(0.064)

        ## intit FPS gui sub-class
        self.fpsGUI = FPSGui( PARENT_NODE = self.screen_node
                            , WINDOW = self.window
                            , VIEWER = self.viewer
                            )

        self.script = SimpleViewingSetupScript()
        self.script.my_constructor(CLASS = self)


        ### trigger callbacks ###

        ## @var frame_trigger
        # Triggers framewise evaluation of respective callback method
        self.frame_trigger = avango.script.nodes.Update(Callback = self.frame_callback, Active = False)

        if CLIENT_FLAG == True:
            self.frame_trigger.Active.value = True # enable frame trigger to search for distributed scenegraph
        


    ### callback functions ###
    def frame_callback(self):
        _nettrans = self.SCENEGRAPH.Root.value.Children.value[0]

        for _node in _nettrans.Children.value:               
            if _node.Name.value.count(self.hostname) > 0:
                self.navigation_node.Transform.connect_from(_node.Transform)

                self.frame_trigger.Active.value = False # disable frame callback
                
                break


        '''
        for _node in _nettrans.Children.value:               
            if _node.Name.value.count(self.hostname) > 0:
                self.SCENEGRAPH.Root.value.Children.value.remove(self.navigation_node)
                _node.Children.value.append(self.navigation_node)

                ## update node paths
                self.camera_node.LeftScreenPath.value = self.screen_node.Path.value
                self.camera_node.RightScreenPath.value = self.screen_node.Path.value
                
                self.frame_trigger.Active.value = False # disable frame callback
        '''

    ### functions ###
    def set_eye_distance(self, FLOAT):
        self.camera_node.EyeDistance.value = FLOAT


    def run(self, LOCALS, GLOBALS):
        self.shell.start(LOCALS, GLOBALS)
        self.viewer.run()


    def list_variabels(self):
        self.shell.list_variables()


    def connect_navigation_matrix(self, SF_MATRIX):
        self.navigation_node.Transform.connect_from(SF_MATRIX)


    def get_head_position(self): # get relative head position (towards screen)
        return self.head_node.Transform.value.get_translate()



class DesktopViewingSetup(SimpleViewingSetup):

    ### constructor
    def __init__( self
                , SCENEGRAPH = None
                , ROOT_NODE = None    
                , STEREO_MODE = "mono"
                , NAVIGATION_START_MAT = avango.gua.make_identity_mat()
                ):

        # call base class constructor
        SimpleViewingSetup.__init__( self 
                                   , SCENEGRAPH = SCENEGRAPH
                                   , ROOT_NODE = ROOT_NODE
                                   , RESOLUTION = avango.gua.Vec2ui(2560, 1440) # DELL
                                   , STEREO_MODE = STEREO_MODE
                                   , SCREEN_DIMENSIONS = avango.gua.Vec2(0.595, 0.32) # in meter
                                   , SCREEN_MAT = avango.gua.make_identity_mat()
                                   , HEADTRACKING_FLAG = False
                                   , TRACKING_STATION = ""
                                   , TRANSMITTER_OFFSET_MAT = avango.gua.make_identity_mat()
                                   , NAVIGATION_START_MAT = NAVIGATION_START_MAT
                                   )

class ServerViewingSetup(SimpleViewingSetup):

    ### constructor
    def __init__( self
                , SCENEGRAPH = None
                , NAVIGATION_START_MAT = avango.gua.make_identity_mat()
                ):

        # call base class constructor
        SimpleViewingSetup.__init__( self 
                                   , SCENEGRAPH = SCENEGRAPH
                                   , RESOLUTION = avango.gua.Vec2ui(1200, 1200) # DELL
                                   , STEREO_MODE = "mono"
                                   , SCREEN_DIMENSIONS = avango.gua.Vec2(0.28, 0.28) # in meter
                                   , SCREEN_MAT = avango.gua.make_identity_mat()
                                   , HEADTRACKING_FLAG = False
                                   , TRACKING_STATION = ""
                                   , TRANSMITTER_OFFSET_MAT = avango.gua.make_identity_mat()
                                   , NAVIGATION_START_MAT = NAVIGATION_START_MAT
                                   )


class Samsung3DTVViewingSetup(SimpleViewingSetup):

    ### constructor
    def __init__( self
                , SCENEGRAPH = None
                , STEREO_MODE = "checkerboard"
                , HEADTRACKING_FLAG = True
                , NAVIGATION_START_MAT = avango.gua.make_identity_mat()                
                , CLIENT_FLAG = False
                , BLACK_LIST = []
                ):

        # call base class constructor
        SimpleViewingSetup.__init__( self 
                                   , SCENEGRAPH = SCENEGRAPH
                                   , RESOLUTION = avango.gua.Vec2ui(1920, 1080)
                                   , STEREO_MODE = STEREO_MODE
                                   , SCREEN_DIMENSIONS = avango.gua.Vec2(1.235, 0.7)
                                   , SCREEN_MAT = avango.gua.make_trans_mat(0.0, 0.64, 0.0) * avango.gua.make_rot_mat(90.0,0,0,1)
                                   , HEADTRACKING_FLAG = HEADTRACKING_FLAG
                                   , TRACKING_STATION = "tracking-lcd-glasses-2" # wired 3D-TV glasses
                                   , TRANSMITTER_OFFSET_MAT = avango.gua.make_trans_mat(0.0 + 0.48, -0.975, 3.48 + 0.48) * avango.gua.make_rot_mat(90.0,0,1,0) # pos of screen
                                   , NAVIGATION_START_MAT = NAVIGATION_START_MAT                                    
                                   , HOSTNAME = "arachne"
                                   , CLIENT_FLAG = CLIENT_FLAG
                                   , BLACK_LIST = BLACK_LIST
                                   )



class Mitsubishi3DTVViewingSetup(SimpleViewingSetup):

    ### constructor
    def __init__( self
                , SCENEGRAPH = None
                , STEREO_MODE = "checkerboard"
                , HEADTRACKING_FLAG = True
                , NAVIGATION_START_MAT = avango.gua.make_identity_mat()
                , CLIENT_FLAG = False
                , BLACK_LIST = []
                ):

        # call base class constructor
        SimpleViewingSetup.__init__( self 
                                   , SCENEGRAPH = SCENEGRAPH
                                   , RESOLUTION = avango.gua.Vec2ui(1920, 1080)
                                   , STEREO_MODE = STEREO_MODE
                                   , SCREEN_DIMENSIONS = avango.gua.Vec2(1.445, 0.81) # in meter
                                   , SCREEN_MAT = avango.gua.make_trans_mat(0.0, 0.58, 0.0) # From Screen to Middle of Screen
                                   , HEADTRACKING_FLAG = HEADTRACKING_FLAG
                                   , TRACKING_STATION = "tracking-lcd-glasses-1" # wireless 3D-TV glasses
                                   , TRANSMITTER_OFFSET_MAT = avango.gua.make_trans_mat(0.0 - 1.0, -0.975, 3.48 + 0.26) * avango.gua.make_rot_mat(90.0,0,1,0) # from navigation node to origin
                                   , NAVIGATION_START_MAT = NAVIGATION_START_MAT
                                   , HOSTNAME = "eris"
                                   , CLIENT_FLAG = CLIENT_FLAG
                                   , BLACK_LIST = BLACK_LIST
                                   )


class LCDWallViewingSetup(SimpleViewingSetup):

    ### constructor
    def __init__( self
                , SCENEGRAPH = None
                , STEREO_MODE = "SIDE_BY_SIDE"
                , HEADTRACKING_FLAG = True
                , NAVIGATION_START_MAT = avango.gua.make_identity_mat()
                , CLIENT_FLAG = False
                , BLACK_LIST = []
                ):

        # call base class constructor
        SimpleViewingSetup.__init__( self 
                                   , SCENEGRAPH = SCENEGRAPH
                                   , RESOLUTION = avango.gua.Vec2ui(1920, 1200)
                                   , STEREO_MODE = STEREO_MODE
                                   , SCREEN_DIMENSIONS = avango.gua.Vec2(3.0, 2.0) # in meter
                                   , SCREEN_MAT = avango.gua.make_trans_mat(0.0, 0.42, -1.6) # from head position to middle of the screen
                                   , HEADTRACKING_FLAG = HEADTRACKING_FLAG
                                   , TRACKING_STATION = "tracking-lcd-glasses-3" # passiv glasses
                                   , TRANSMITTER_OFFSET_MAT = avango.gua.make_trans_mat(0.0, -0.6, 0.0) # from navigation coord. system to origin
                                   , NAVIGATION_START_MAT = NAVIGATION_START_MAT
                                   , HOSTNAME = "athena"
                                   , CLIENT_FLAG = CLIENT_FLAG
                                   , BLACK_LIST = BLACK_LIST
                                   )




