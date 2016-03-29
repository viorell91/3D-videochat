#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import time #start_clients
import os # to get path


### import application libraries
from lib.SimpleViewingSetup import DesktopViewingSetup, ServerViewingSetup, Mitsubishi3DTVViewingSetup, Samsung3DTVViewingSetup
from lib.Scene import Scene
from lib.Device import *
from lib.Navigation import SteeringNavigation
from lib.Manipulation import ManipulationManager


### global variables ###
NAVIGATION_MODE = "Spacemouse"
#NAVIGATION_MODE = "New Spacemouse" # blue LED

## import python libraries
import subprocess

def start_clients(SERVER_IP = "141.54.147.33", PATH = ""):
  print("Server-IP: ", SERVER_IP)

  _ssh_run_arachne = subprocess.Popen(["ssh", "arachne", PATH + "/start_client.sh " + SERVER_IP], stderr=subprocess.PIPE, universal_newlines=True)
  _ssh_run_eris = subprocess.Popen(["ssh", "eris", PATH + "/start_client.sh " + SERVER_IP], stderr=subprocess.PIPE, universal_newlines=True)
  _ssh_run_athena = subprocess.Popen(["ssh", "athena", PATH + "/start_client.sh " + SERVER_IP], stderr=subprocess.PIPE, universal_newlines=True)

  time.sleep(5)

def start():

    server_ip = subprocess.Popen(["hostname", "-I"], stdout = subprocess.PIPE, universal_newlines = True).communicate()[0]
    server_ip = server_ip.strip(" \n")
    server_ip = server_ip.rsplit(" ")
    server_ip = str(server_ip[-1])
    
    start_clients(server_ip, os.getcwd())

    nettrans = avango.gua.nodes.NetTransform( Name = "net", Groupname = "AVSERVER|{0}|7433".format(server_ip))

    ## create scenegraph
    scenegraph = avango.gua.nodes.SceneGraph(Name = "scenegraph")
    scenegraph.Root.value.Children.value.append(nettrans)

    ## init scene
    scene = Scene(PARENT_NODE = nettrans)



    ### init viewing && kinect setup for clients ###
    
    ## 1. eris ##
    # navigation eris
    device_input1 = SpacemouseInput()
    device_input1.my_constructor("device-spacemouse1")
    navigation_client1 = create_navigation_client("eris", device_input1, avango.gua.make_rot_mat(180.0, 0, 1, 0) * avango.gua.make_trans_mat(0.0, 0.1, 1.2), scenegraph, nettrans)
    navigation1_node   = create_navigation_node("eris", navigation_client1, nettrans)

    # pointer eris
    manipulationManager1 = create_manipulation_manager(navigation1_node, avango.gua.make_trans_mat(0.0 - 1.0, -0.975, 3.48 + 0.26) * avango.gua.make_rot_mat(90.0,0,1,0), "tracking-art-pointer-3", "device-pointer-3", scenegraph) 
    
    # kinect video avatar eris
    kinect1_node = create_kinect_node("eris", "kinect1_node", "/opt/kinect-resources/calib_3dvc/surface_50_51_54.ks",  avango.gua.make_trans_mat(0.0 - 1.0, -0.975, 3.48 + 0.26))
    navigation1_node.Children.value.append(kinect1_node)


    ## 2. arachne ##
    # navigation arachne
    device_input2 = SpacemouseInput()
    device_input2.my_constructor("device-spacemouse2") 
    navigation_client2 = create_navigation_client("arachne", device_input2, avango.gua.make_rot_mat(90.0, 0, 1, 0) * avango.gua.make_trans_mat(0.0, 0.1, 1.0), scenegraph, nettrans)
    navigation2_node   = create_navigation_node("arachne", navigation_client2, nettrans)
    
    # pointer arachne
    manipulationManager2 = create_manipulation_manager(navigation2_node, avango.gua.make_trans_mat(0.0 + 0.48, -0.975, 3.48 + 0.48) * avango.gua.make_rot_mat(90.0,0,1,0), "tracking-art-pointer-2", "device-pointer-2", scenegraph) 
    
    # kinect video avatar arachne
    kinect2_node = create_kinect_node("arachne", "kinect2_node", "/opt/kinect-resources/calib_3dvc/surface_52_53.ks", avango.gua.make_trans_mat(0.0 + 0.48, -0.975, 3.48 + 0.48))
    navigation2_node.Children.value.append(kinect2_node)


    ## 3. athena ##
    # navigation athena
    device_input3 = SpacemouseInput()
    device_input3.my_constructor("device-spacemouse3")   
    navigation_client3 = create_navigation_client("athena", device_input3, avango.gua.make_trans_mat(0.0, 0.1, 0.9), scenegraph, nettrans)
    navigation3_node   = create_navigation_node("athena", navigation_client3, nettrans)
    
    # pointer athena
    manipulationManager3 = create_manipulation_manager(navigation3_node, avango.gua.make_trans_mat(0.0, -0.6, 0.0), "tracking-art-pointer-1", "device-pointer-1", scenegraph)
    
    # kinect video avatar athena
    kinect_pos = avango.gua.make_rot_mat(-90.0,0,1,0) * avango.gua.make_trans_mat(0.0, -0.6, 0.0) # to actual position of navigation node
    kinect3_node = create_kinect_node("athena", "kinect3_node", "/opt/kinect-resources/calib_3dvc/surface_23.ks", kinect_pos)
    navigation3_node.Children.value.append(kinect3_node)

    #teacher gets a copy of the kinect
    #kinect3_node_copy = create_kinect_node("athena", "kinect3_node_copy", "/opt/kinect-resources/calib_3dvc/surface_23.ks", avango.gua.make_scale_mat(0.7, 0.7, 0.7) * avango.gua.make_rot_mat(-90.0,0,1,0) * avango.gua.make_trans_mat(2.0, -1.0, 0.0))
    #kinect3_node_copy.Tags.value = ["eris", "arachne", "moveable"]
    tmp_video_loader = avango.gua.nodes.Video3DLoader()
    kinect3_node_copy = tmp_video_loader.load("kinect3_node_copy", "/opt/kinect-resources/calib_3dvc/surface_23.ks")
    kinect3_node_copy.Transform.value = avango.gua.make_scale_mat(0.25, 0.25, 0.25) * avango.gua.make_trans_mat(0.0, 0.0, -1.8)
    kinect3_node_copy.Tags.value = ["eris", "arachne"]
    nettrans.Children.value.append(kinect3_node_copy)


    ## init viewing setup
    viewingSetup = ServerViewingSetup( SCENEGRAPH = scenegraph
                                     , NAVIGATION_START_MAT = avango.gua.make_trans_mat(0.0,2.0,0.0) * avango.gua.make_rot_mat(90.0,-1,0,0) * avango.gua.make_scale_mat(3.0)
                                     )

    print_graph(scenegraph.Root.value)

    distribute_all_nodes_below(NODE = nettrans, NETTRANS = nettrans)

    ## start application/render loop
    viewingSetup.run(locals(), globals())



## Registers a scenegraph node and all of its children at a NetMatrixTransform node for distribution.
# @param NET_TRANS_NODE The NetMatrixTransform node on which all nodes should be marked distributable.
# @param PARENT_NODE The node that should be registered distributable with all of its children.
def distribute_all_nodes_below(NODE = None, NETTRANS = None):
       
    # do not distribute the nettrans node itself
    if NODE != NETTRANS:
        NETTRANS.distribute_object(NODE)
        #print ("distribute", NODE, NODE.Name.value, NODE.Path.value)


    # iterate over children and make them distributable
    for _child_node in NODE.Children.value:
        distribute_all_nodes_below(NODE = _child_node, NETTRANS = NETTRANS)


### helper functions ###

## print the subgraph under a given node to the console
def print_graph(root_node):
  stack = [(root_node, 0)]
  while stack:
    node, level = stack.pop()
    print("│   " * level + "├── {0} <{1}>".format(
      node.Name.value, node.__class__.__name__))
    stack.extend(
      [(child, level + 1) for child in reversed(node.Children.value)])

## print all fields of a fieldcontainer to the console
def print_fields(node, print_values = False):
  for i in range(node.get_num_fields()):
    field = node.get_field(i)
    print("→ {0} <{1}>".format(field._get_name(), field.__class__.__name__))
    if print_values:
      print("  with value '{0}'".format(field.value))


def create_manipulation_manager(NAVIGATION_NODE, TRANSMITTER_OFFSET, TRACKING_STATION, DEVICE_STATION, SCENEGRAPH):

  return ManipulationManager( SCENEGRAPH = SCENEGRAPH
                            , PARENT_NODE = NAVIGATION_NODE
                            , POINTER_TRACKING_STATION = TRACKING_STATION
                            , POINTER_DEVICE_STATION = DEVICE_STATION
                            , HEAD_NODE = NAVIGATION_NODE
                            , TRACKING_TRANSMITTER_OFFSET = TRANSMITTER_OFFSET #avango.gua.make_trans_mat(0.0, -0.8, 1.5)#avango.gua.make_trans_mat(0.48, -(0.64 + 0.975), 0.48 + 3.48) * avango.gua.make_rot_mat(90.0,0,1,0) # transformation into tracking coordinate system
                            )

def create_navigation_client(HOST_NAME, DEVICE_INPUT, START_POSITION, SCENEGRAPH, SCENE_ROOT):
  
  navigation_client = SteeringNavigation()
  navigation_client.set_start_transformation(START_POSITION)
  navigation_client.my_constructor(DEVICE_INPUT.mf_dof, 1.0, SCENEGRAPH, SCENE_ROOT, HOST_NAME) # connect navigation with spacemouse input
  return navigation_client

def create_navigation_node(HOST_NAME, NAVIGATION_CLIENT, NETTRANS):

  navigation_node = avango.gua.nodes.TransformNode(Name = HOST_NAME)
  NETTRANS.Children.value.append(navigation_node)
  navigation_node.Transform.connect_from(NAVIGATION_CLIENT.sf_nav_mat)
  return navigation_node

def create_kinect_node(HOST_NAME, KINECT_NODE, KINECT_SURFACE, TRANSMAT):

  _video_loader = avango.gua.nodes.Video3DLoader()
  kinect_node = _video_loader.load(KINECT_NODE, KINECT_SURFACE)
  kinect_node.Transform.value = TRANSMAT * avango.gua.make_rot_mat(90.0,0,1,0)
  kinect_node.Tags.value = [HOST_NAME, "unpickable"]
  return kinect_node


if __name__ == '__main__':
    start()

