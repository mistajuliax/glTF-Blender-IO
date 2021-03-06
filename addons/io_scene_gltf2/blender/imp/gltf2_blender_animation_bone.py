# Copyright 2018 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from mathutils import Quaternion, Matrix

from ..com.gltf2_blender_conversion import *
from ...io.imp.gltf2_io_binary import *

class BlenderBoneAnim():

    @staticmethod
    def set_interpolation(interpolation, kf):
        if interpolation == "LINEAR":
            kf.interpolation = 'LINEAR'
        elif interpolation == "STEP":
            kf.interpolation = 'CONSTANT'
        elif interpolation == "CATMULLROMSPLINE":
            kf.interpolation = 'BEZIER' #TODO
        elif interpolation == "CUBICSPLINE":
            kf.interpolation = 'BEZIER' #TODO
        else:
            kf.interpolation = 'BEZIER'

    @staticmethod
    def anim(gltf, anim_idx, node_idx):
        node  = gltf.data.nodes[node_idx]
        obj   = bpy.data.objects[gltf.data.skins[node.skin_id].blender_armature_name]
        bone  = obj.pose.bones[node.blender_bone_name]
        fps = bpy.context.scene.render.fps

        if anim_idx not in node.animations.keys():
            return

        animation = gltf.data.animations[anim_idx]

        if animation.name:
            name = animation.name + "_" + obj.name
        else:
            name = "Animation_" + str(anim_idx) + "_" + obj.name
        if name not in bpy.data.actions:
            action = bpy.data.actions.new(name)
        else:
            action = bpy.data.actions[name]
        if not obj.animation_data:
            obj.animation_data_create()
        obj.animation_data.action = bpy.data.actions[action.name]

        for channel_idx in node.animations[anim_idx]:
            channel = animation.channels[channel_idx]

            keys   = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].input)
            values = BinaryData.get_data_from_accessor(gltf, animation.samplers[channel.sampler].output)

            if channel.target.path == "translation":
                blender_path = "location"
                for idx, key in enumerate(keys):
                    transform = Matrix.Translation(Conversion.loc_gltf_to_blender(list(values[idx])))
                    if not node.parent:
                        mat = transform
                    else:
                        if not gltf.data.nodes[node.parent].is_joint:
                            parent_mat = bpy.data.objects[gltf.data.nodes[node.parent].blender_object].matrix_world
                            mat = transform
                        else:
                            parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

                            mat = (parent_mat.to_quaternion() * transform.to_quaternion()).to_matrix().to_4x4()
                            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * transform.to_translation() )) * mat
                            #TODO scaling of bones ?

                    bone.location = node.blender_bone_matrix.inverted() * mat.to_translation()
                    bone.keyframe_insert(blender_path, frame = key[0] * fps, group='location')


                # Setting interpolation
                for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "location"]:
                    for kf in fcurve.keyframe_points:
                        BlenderBoneAnim.set_interpolation(animation.samplers[channel.sampler].interpolation, kf)


            elif channel.target.path == "rotation":
                blender_path = "rotation_quaternion"
                for idx, key in enumerate(keys):
                    transform = Conversion.quaternion_gltf_to_blender(values[idx]).to_matrix().to_4x4()
                    if not node.parent:
                        mat = transform
                    else:
                        if not gltf.data.nodes[node.parent].is_joint:
                            parent_mat = bpy.data.objects[gltf.data.nodes[node.parent].blender_object].matrix_world
                            mat = transform
                        else:
                            parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix

                            mat = (parent_mat.to_quaternion() * transform.to_quaternion()).to_matrix().to_4x4()
                            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * transform.to_translation() )) * mat
                            #TODO scaling of bones ?

                    bone.rotation_quaternion = node.blender_bone_matrix.to_quaternion().inverted() * mat.to_quaternion()
                    bone.keyframe_insert(blender_path, frame = key[0] * fps, group='rotation')

                # Setting interpolation
                for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                    for kf in fcurve.keyframe_points:
                        BlenderBoneAnim.set_interpolation(animation.samplers[channel.sampler].interpolation, kf)

            elif channel.target.path == "scale":
                blender_path = "scale"
                for idx, key in enumerate(keys):
                    s = Conversion.scale_gltf_to_blender(list(values[idx]))
                    transform = Matrix([
                        [s[0], 0, 0, 0],
                        [0, s[1], 0, 0],
                        [0, 0, s[2], 0],
                        [0, 0, 0, 1]
                    ])

                    if not node.parent:
                        mat = transform
                    else:
                        if not gltf.data.nodes[node.parent].is_joint:
                            parent_mat = bpy.data.objects[gltf.data.nodes[node.parent].blender_object].matrix_world
                            mat = transform
                        else:
                            parent_mat = gltf.data.nodes[node.parent].blender_bone_matrix
                            mat = parent_mat.inverted() * transform


                    #bone.scale # TODO
                    bone.scale = mat.to_scale()
                    bone.keyframe_insert(blender_path, frame = key[0] * fps, group='scale')

                # Setting interpolation
                for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "scale"]:
                    for kf in fcurve.keyframe_points:
                        BlenderBoneAnim.set_interpolation(animation.samplers[channel.sampler].interpolation, kf)
