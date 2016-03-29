#!/usr/bin/python

# import avango-guacamole libraries
import avango
import avango.gua


# import framework libraries
from lib.SimpleViewingSetup import Mitsubishi3DTVViewingSetup, Samsung3DTVViewingSetup, LCDWallViewingSetup

# import python libraries
import sys


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





## Main method for the client application.
def start():

    # get the server ip
    server_ip = str(sys.argv[1])
        
    # create scenegraph
    scenegraph = avango.gua.nodes.SceneGraph(Name = "scenegraph")

    # create distribution node
    nettrans = avango.gua.nodes.NetTransform( Name = "net"
                                            , Groupname = "AVCLIENT|{0}|7433".format(server_ip)
                                            )
    scenegraph.Root.value.Children.value = [nettrans]


    hostname = open('/etc/hostname', 'r').readline()
    hostname = hostname.strip(" \n")

    print("Starting Client!", hostname)
    
    if hostname == "eris":
      viewingSetup = Mitsubishi3DTVViewingSetup( SCENEGRAPH = scenegraph
                                               , CLIENT_FLAG = True
                                               , BLACK_LIST = ["eris", "invisible"]
                                               )

    elif hostname == "arachne":
      viewingSetup = Samsung3DTVViewingSetup( SCENEGRAPH = scenegraph
                                            , CLIENT_FLAG = True
                                            , BLACK_LIST = ["arachne", "invisible"]
                                            )

    elif hostname == "athena":
      viewingSetup = LCDWallViewingSetup( SCENEGRAPH = scenegraph
                                        , CLIENT_FLAG = True
                                        , BLACK_LIST = ["athena", "invisible"]
                                        )
                                              
     ## start application/render loop
    viewingSetup.run(locals(), globals())

   

if __name__ == '__main__':
    start()
