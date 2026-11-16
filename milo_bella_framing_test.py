"""Free Blender camera/framing proof. NOT a final-quality AI cartoon."""
import bpy, math, random
from mathutils import Vector
random.seed(8)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine='CYCLES'
sc.cycles.device='CPU'
sc.cycles.samples=12
sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100
sc.render.fps=24; sc.frame_start=1; sc.frame_end=120
sc.render.image_settings.file_format='FFMPEG' if False else 'PNG'
sc.render.filepath='/tmp/milo_frame.png'
sc.world.color=(0.23,0.37,0.28)
def mat(name,color,rough=.75):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
gray=mat('Milo warm gray',(.59,.63,.67));pink=mat('pink inner ears',(.95,.46,.43));white=mat('Bella white',(.91,.91,.83));black=mat('eyes',(.018,.033,.05),.16);green=mat('deep green',(.08,.29,.12));green2=mat('light green',(.17,.46,.14));red=mat('bright red',(.88,.09,.08));orange=mat('coral orange',(1,.31,.06));gold=mat('warm path',(.65,.47,.22));brown=mat('bark',(.30,.18,.09))
def sphere(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);bpy.ops.object.shade_smooth();return o
def cylinder(name,loc,radius,depth,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(material);return o
def animal(name,x,bodymat,elephant=False):
 y=0;z=.95 if elephant else .6
 body=sphere(name+' body',(x,y,z),(0.62 if elephant else .35,.44 if elephant else .29,.63 if elephant else .38),bodymat)
 head=sphere(name+' head',(x,y-.21,z+.63 if elephant else z+.38),(.51 if elephant else .31,)*3,bodymat)
 for dx in [-1,1]:
  sphere(name+' foot',(x+dx*(.32 if elephant else .17),-.2,.21),(.21,.24,.22) if elephant else (.13,.16,.14),bodymat)
  sphere(name+' eye',(x+dx*(.19 if elephant else .13),-.65 if elephant else -.48,z+.72 if elephant else z+.47),(.09,.06,.11),black)
  if elephant:
   sphere(name+' ear',(x+dx*.58,-.18,z+.67),(.31,.10,.42),pink)
  else:
   sphere(name+' ear',(x+dx*.16,-.18,z+.92),(.13,.11,.48),white)
   sphere(name+' ear inset',(x+dx*.16,-.29,z+.92),(.075,.035,.35),pink)
 if elephant:
  for i in range(5):sphere(name+' trunk',(x,-.69-i*.045,z+.39-i*.14),(.19-i*.022,.20-i*.025,.19),gray)
 for frame,delta in [(1,0),(60,.10),(120,0)]:
  body.location.z=z+delta;body.keyframe_insert(data_path='location',frame=frame)
animal('Milo',-1.2,gray,True);animal('Bella',1.2,white,False)
cylinder('ground',(0,0,-.15),200,.25,green)
# Path and layered scenery, no animal duplicates
sphere('path',(0,-1,-.12),(2.4,6,.07),gold)
for i in range(38):
 x=random.choice([-1,1])*random.uniform(3.4,13)
 y=random.uniform(-5,14)
 h=random.uniform(2,5)
 cylinder('tree trunk',(x,y,h/2),.28,h,brown)
 for j in range(4):sphere('leaf canopy',(x+random.uniform(-1,1),y+random.uniform(-1,1),h+random.uniform(-.2,.9)),(1.1,1.1,.8),random.choice([green,green2]))
for i in range(80):
 x=random.choice([-1,1])*random.uniform(2.5,8);y=random.uniform(-4,10)
 sphere('flower',(x,y,.12),(.14,.14,.11),random.choice([red,orange]))
bpy.ops.object.camera_add(location=(0,-13,5.4));cam=bpy.context.object
direction=Vector((0,0,1.35))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=10.5;sc.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-4,-6,10));bpy.context.object.data.energy=1800;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
sc.view_settings.view_transform='Standard'
sc.render.filepath='output/milo_bella_framing_test.png'
bpy.ops.render.render(write_still=True)
