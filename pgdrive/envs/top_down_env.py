from pgdrive.envs.pgdrive_env import PGDriveEnv
from pgdrive.pg_config import PGConfig
from pgdrive.scene_creator.vehicle.base_vehicle import BaseVehicle
from pgdrive.world.top_down_observation import TopDownMultiChannel, TopDownObservation


class TopDownSingleFramePGDriveEnv(PGDriveEnv):
    @classmethod
    def default_config(cls) -> PGConfig:
        config = PGDriveEnv.default_config()
        config["vehicle_config"]["lidar"] = {"num_lasers": 0, "distance": 0}  # Remove lidar
        config.extend_config_with_unknown_keys({"frame_skip": 5, "frame_stack": 5, "post_stack": 5, "rgb_clip": False})
        return config

    def get_observation(self, _=None):
        vehicle_config = BaseVehicle.get_vehicle_config(self.config["vehicle_config"])
        return TopDownObservation(vehicle_config, self, self.config["rgb_clip"])


class TopDownPGDriveEnv(TopDownSingleFramePGDriveEnv):
    def get_observation(self, _=None):
        vehicle_config = BaseVehicle.get_vehicle_config(self.config["vehicle_config"])
        return TopDownMultiChannel(
            vehicle_config,
            self,
            self.config["rgb_clip"],
            frame_stack=self.config["frame_stack"],
            post_stack=self.config["post_stack"],
            frame_skip=self.config["frame_skip"],
        )


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    # Test single RGB frame
    # env = TopDownSingleFramePGDriveEnv(dict(use_render=True, environment_num=1, map="C", traffic_density=1.0))
    # env.reset()
    # for _ in range(20):
    #     o, *_ = env.step([0, 1])
    #     assert env.observation_space.contains(o)
    # for _ in range(200):
    #     o, *_ = env.step([0.01, 1])
    #     env.render()
    #     # plt.imshow(o, cmap="gray")
    #     # plt.show()
    #     # print(o.mean())
    # env.close()

    # Test multi-channel frames
    env = TopDownPGDriveEnv(dict(environment_num=1, map="XTO", traffic_density=0.1, frame_stack=5))
    # env = TopDownPGDriveEnv(dict(use_render=True, manual_control=True))
    env.reset()
    names = [
        "road_network", "navigation", "target_vehicle", "past_pos", "traffic t", "traffic t-1", "traffic t-2",
        "traffic t-3", "traffic t-4"
    ]
    for _ in range(20):
        o, *_ = env.step([-0.05, 1])
        assert env.observation_space.contains(o)
    for _ in range(10000):
        o, *_ = env.step([1, 1])

        fig, axes = plt.subplots(1, o.shape[-1], figsize=(15, 3))

        # o = env.observations[env.DEFAULT_AGENT].get_screen_window()
        # import numpy as np
        # import pygame
        # o = pygame.surfarray.array3d(o)
        # o = np.transpose(o, (1, 0, 2))
        # axes[0].imshow(o)

        for o_i in range(o.shape[-1]):
            axes[o_i].imshow(o[..., o_i], cmap="gray")
            axes[o_i].set_title(names[o_i])

        fig.suptitle("Multi-channel Top-down Observation")
        plt.show()
        print(o.mean())
    env.close()