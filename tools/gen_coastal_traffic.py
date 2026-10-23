"""CC0 cabin cruiser + original detailed cruise liner for distant coastal traffic.

Reference silhouette: multiple passenger decks, balconies, davits and lifeboats.
Downloaded yacht source/license: Innerscene cabin-cruiser-597d60da (CC0).
Preserves packed editable Blender sources; no mesh decimation.
"""
from pathlib import Path
import bpy, bmesh, math, tempfile, shutil, requests, sys
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gen_code_props import mat, box, lathe
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/models/gen'

def save(name):
    # Merge by material to keep hundreds of windows from becoming draw calls.
    groups={}
    for obj in list(bpy.context.scene.objects):
        if obj.type=='MESH':groups.setdefault(tuple(m.name for m in obj.data.materials),[]).append(obj)
    for objects in groups.values():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        if len(objects)>1:bpy.ops.object.join()
    for im in bpy.data.images:
        if max(im.size)>1024:
            f=1024/max(im.size);im.scale(round(im.size[0]*f),round(im.size[1]*f))
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    stage=Path(tempfile.gettempdir())/(name+'_new.blend')
    if stage.exists():stage.unlink()
    bpy.ops.wm.save_as_mainfile(filepath=str(stage))
    source=ROOT/'art/blender'/f'{name}.blend'
    shutil.copyfile(stage,source);stage.unlink()
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{name}.glb'),export_format='GLB',export_apply=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
    vs=[o.matrix_world@Vector(v) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.bound_box]
    print('COAST_ASSET_PASS',name,[(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)],flush=True)

def yacht():
    cache=ROOT/'art/vendor/coastal';cache.mkdir(parents=True,exist_ok=True)
    src=cache/'cabin-cruiser.glb'
    if not src.exists():
        r=requests.get('https://www.innerscene.com/api/library/cabin-cruiser-597d60da/download',timeout=90)
        r.raise_for_status();assert r.content[:4]==b'glTF';src.write_bytes(r.content)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(src))
    save('coastal_yacht')

def loft(name,rings,material):
    # Smooth ship-shaped elliptical deck plan with sharpened bow; rings: L,W,Z.
    n=96;verts=[];faces=[]
    for length,width,z in rings:
        for i in range(n):
            t=2*math.pi*i/n
            x=math.cos(t)*length/2
            y=math.sin(t)*width/2
            if x>0:y*=max(.10,1-.65*(x/(length/2))**3)
            verts.append((x,y,z))
    for j in range(len(rings)-1):
        for i in range(n):
            k=j*n+i;q=j*n+(i+1)%n
            faces.append((k,q,q+n,k+n))
    faces.extend([tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);mesh.materials.append(material)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
    return ob

def rail(points,material,radius=.035):
    curve=bpy.data.curves.new('tubular railing','CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for p,v in zip(spline.points,points):p.co=(*v,1)
    ob=bpy.data.objects.new('railing',curve);bpy.context.collection.objects.link(ob);curve.materials.append(material)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False)

def cruise():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ivory=mat('ivory marine paint',(.78,.77,.72),.55)
    hull=mat('navy hull',(.035,.065,.085),.55)
    red=mat('antifouling',(.22,.055,.04),.85)
    teak=mat('teak deck',(.35,.24,.13),.85)
    dark=mat('bridge glazing',(.035,.075,.085),.22)
    metal=mat('railing steel',(.46,.47,.45),.35,metal=.25)
    orange=mat('lifeboat orange',(.67,.25,.065),.65)
    glow=mat('glow_cabin_windows',(.9,.71,.38),.35)
    bulb=next(n for n in glow.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bulb.inputs['Emission Color'].default_value=(1,.64,.26,1)
    bulb.inputs['Emission Strength'].default_value=1.5
    loft('underwater hull',[(78,7,-3.5),(87,12,-1.5),(90,14,.12)],red)
    loft('curved ship hull',[(90,14,0),(91,14.6,2.2),(90,14.8,3.4)],hull)
    for deck in range(5):
        length=76-deck*3.5;width=13.4-deck*.36;z=3.4+deck*2.1
        loft('passenger deck',[(length,width,z),(length,width,z+.20)],ivory)
        loft('passenger superstructure',[(length-2,width-1.1,z+.20),(length-3,width-1.35,z+1.95)],ivory)
        # Recessed windows, projecting balcony slabs and fine steel rails.
        for side in [-1,1]:
            for x in range(-31+deck*2,32-deck*2,2):
                box((1.10,.10,.82),(x,side*(width/2-.55),z+1.05),glow,.08)
                box((1.60,.45,.12),(x,side*(width/2-.22),z+.42),ivory,.03)
                rail([(x-.78,side*(width/2),z+1.12),(x+.78,side*(width/2),z+1.12)],metal)
            rail([(-length*.4,side*width*.48,z+2.1),(length*.4,side*width*.48,z+2.1)],metal)
    # Bow and stern promenade, bridge, upper sun deck, funnel and communications.
    loft('upper teak promenade',[(57,11.3,13.95),(57,11.3,14.1)],teak)
    box((9,11.2,2.0),(25,0,11.2),ivory,.55)
    box((.13,10.2,.95),(29.6,0,11.5),dark,.06)
    for side in [-1,1]:
        box((8,.12,.95),(25,side*5.57,11.5),dark,.08)
        for x in [-25,-15,-5,5,15]:
            boat=loft('enclosed lifeboat',[(5.3,1.15,0),(6.2,1.7,.65),(5.0,1.4,1.25)],orange)
            boat.location=(x,side*7.5,4.3)
            box((2.7,.95,.65),(x,side*7.5,5.6),ivory,.20)
            for xx in [x-2,x+2]:rail([(xx,side*6.2,6.9),(xx,side*8,6.9),(xx,side*8,5.5)],metal,.06)
    box((8,4.7,3.5),(-13,0,15.8),ivory,.65)
    box((8.2,4.9,.5),(-13,0,17.7),hull,.20)
    for x in [-15,-13,-11]:
        lathe([(.4,0),(.4,.7),(.3,.82)],dark,(x,0,17.95))
    rail([(14,0,14),(14,0,20)],metal,.11)
    rail([(10,0,18.4),(18,0,18.4)],metal,.08)
    for x in [11,17]:
        lathe([(.55,0),(.65,.45),(.45,.90),(0,1.1)],ivory,(x,0,14.1))
    # Pool and sun loungers are modeled details, not runtime primitives.
    box((9,3,.2),(0,0,14.18),dark,.5)
    for side in [-1,1]:
        for x in range(-5,7,2):box((1.2,.55,.23),(x,side*3.1,14.28),ivory,.10)
    for side in [-1,1]:
        for x in range(-35,36,3):box((.65,.12,.4),(x,side*7.32,1.75),glow,.15)
    save('coastal_cruise')

if __name__=='__main__':
    names=sys.argv[1:] or ['yacht','cruise']
    if 'yacht' in names:yacht()
    if 'cruise' in names:cruise()
