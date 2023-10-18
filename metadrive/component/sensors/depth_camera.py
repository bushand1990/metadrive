import cv2
from panda3d.core import Shader, RenderState, ShaderAttrib, GeoMipTerrain, PNMImage, Texture, LightAttrib, \
    TextureAttrib, ColorAttrib

from metadrive.component.sensors.base_camera import BaseCamera
from metadrive.constants import CamMask
from metadrive.constants import RENDER_MODE_NONE
from metadrive.engine.asset_loader import AssetLoader
from panda3d.core import FrameBufferProperties


class DepthCamera(BaseCamera):
    # shape(dim_1, dim_2)
    CAM_MASK = CamMask.DepthCam

    GROUND_HEIGHT = -0.5
    VIEW_GROUND = False
    GROUND = None
    GROUND_MODEL = None

    def __init__(self, width, height, engine, *, cuda=False):
        self.BUFFER_W, self.BUFFER_H = width, height
        self.VIEW_GROUND = True  # default true
        frame_buffer_property = FrameBufferProperties()
        frame_buffer_property.set_rgba_bits(8, 8, 8, 0)  # disable alpha for RGB camera
        # TODO It can be made more efficient by only using one channel
        super(DepthCamera, self).__init__(engine, False, cuda)
        cam = self.get_cam()
        lens = self.get_lens()

        # cam.lookAt(0, 2.4, 1.3)
        cam.lookAt(0, 10.4, 1.6)

        lens.setFov(60)
        # lens.setAspectRatio(2.0)
        if self.engine.mode == RENDER_MODE_NONE or not AssetLoader.initialized():
            return
        # add shader for it
        # if get_global_config()["headless_machine_render"]:
        #     vert_path = AssetLoader.file_path("shaders", "depth_cam_gles.vert.glsl")
        #     frag_path = AssetLoader.file_path("shaders", "depth_cam_gles.frag.glsl")
        # else:
        from metadrive.utils import is_mac
        if is_mac():
            vert_path = AssetLoader.file_path("shaders", "depth_cam_mac.vert.glsl")
            frag_path = AssetLoader.file_path("shaders", "depth_cam_mac.frag.glsl")
        else:
            vert_path = AssetLoader.file_path("shaders", "depth_cam.vert.glsl")
            frag_path = AssetLoader.file_path("shaders", "depth_cam.frag.glsl")
        custom_shader = Shader.load(Shader.SL_GLSL, vertex=vert_path, fragment=frag_path)
        cam.node().setInitialState(
            RenderState.make(
                LightAttrib.makeAllOff(), TextureAttrib.makeOff(), ColorAttrib.makeOff(),
                ShaderAttrib.make(custom_shader, 1)
            )
        )

        if self.VIEW_GROUND:
            ground = PNMImage(513, 513, 4)
            ground.fill(1., 1., 1.)

            self.GROUND = GeoMipTerrain("mySimpleTerrain")
            self.GROUND.setHeightfield(ground)
            self.GROUND.setAutoFlatten(GeoMipTerrain.AFMStrong)
            # terrain.setBruteforce(True)
            # # Since the terrain is a texture, shader will not calculate the depth information, we add a moving terrain
            # # model to enable the depth information of terrain
            self.GROUND_MODEL = self.GROUND.getRoot()
            self.GROUND_MODEL.setPos(-128, -128, self.GROUND_HEIGHT)
            self.GROUND_MODEL.reparentTo(self.engine.render)
            self.GROUND_MODEL.hide(CamMask.AllOn)
            self.GROUND_MODEL.show(CamMask.DepthCam)
            self.GROUND.generate()

    def track(self, base_object):
        if self.VIEW_GROUND:
            pos = base_object.origin.getPos()
            self.GROUND_MODEL.setPos(pos[0], pos[1], self.GROUND_HEIGHT)
            self.GROUND_MODEL.setH(base_object.origin.getH())
            # self.GROUND_MODEL.setP(-base_object.origin.getR())
            # self.GROUND_MODEL.setR(-base_object.origin.getR())
        return super(DepthCamera, self).track(base_object)
