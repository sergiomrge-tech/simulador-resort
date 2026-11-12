import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='D:/Projetos/MareAltaUE58/assets/models/gen/life_vest.glb')
for k, m in enumerate(list(bpy.data.materials)):
    m.name = 'TourBoat_vest_M%d' % k
for k, i in enumerate(list(bpy.data.images)):
    i.name = 'TourBoat_vest_T%d' % k
    i.pack()
objs = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(objs) > 1: bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
o.name = o.data.name = 'TourBoat_vest'
d = [round(max(v.co[i] for v in o.data.vertices) - min(v.co[i] for v in o.data.vertices), 3) for i in range(3)]
c = [round((max(v.co[i] for v in o.data.vertices) + min(v.co[i] for v in o.data.vertices)) / 2, 3) for i in range(3)]
print('VEST dims', d, 'centre', c, [m.name for m in o.data.materials])
bpy.ops.export_scene.gltf(filepath='D:/CodexTemp/tourboat/TourBoat_vest.glb', export_format='GLB', export_apply=True)
