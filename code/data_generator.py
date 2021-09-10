#!/usr/bin/env python3
import random
import argparse

import cv2
import pygame
import numpy as np
import carla
from carla import ColorConverter as cc


def game_loop(args):
    pygame.init()
    actor_list = []

    UNIT_WIDTH = args.width / 3
    UNIT_HEIGHT = args.height / 3

    CAMERA_CONFIGS = [
        ["front1", carla.Transform(carla.Location(x=1.5, y=0, z=2.4), carla.Rotation(yaw=0)), 120, (UNIT_WIDTH, 0), None],
        ["front2", carla.Transform(carla.Location(x=1.5, y=0.1, z=2.4), carla.Rotation(yaw=0)), 90, (2*UNIT_WIDTH, 0), None],
        ["right_front", carla.Transform(carla.Location(x=0, y=1.1, z=2.4), carla.Rotation(yaw=45)), 90, (2*UNIT_WIDTH, UNIT_HEIGHT), None],
        ["right_rear", carla.Transform(carla.Location(x=1.0, y=1.1, z=1), carla.Rotation(yaw=135)), 120, (2*UNIT_WIDTH, 2*UNIT_HEIGHT), None],
        ["left_front", carla.Transform(carla.Location(x=-1.5, y=0, z=2.4), carla.Rotation(yaw=180)), 120, (UNIT_WIDTH, 2*UNIT_HEIGHT), None],
        ["left_rear", carla.Transform(carla.Location(x=1.0, y=-1.1, z=1), carla.Rotation(yaw=225)), 120, (0, 2*UNIT_HEIGHT), None],
        ["front2", carla.Transform(carla.Location(x=0, y=-1.1, z=2.4), carla.Rotation(yaw=315)), 90, (0, UNIT_HEIGHT), None],
        ["front3", carla.Transform(carla.Location(x=1.5, y=-0.1, z=2.4), carla.Rotation(yaw=0)), 45, (0, 0), None]
    ]

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(12.0)
        client.load_world(args.map)
        world = client.get_world()
        map = world.get_map()

        blueprint_library = world.get_blueprint_library()
        bp = blueprint_library.filter("model3")[0]
        spawn_points = map.get_spawn_points()
        spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
        vehicle = world.try_spawn_actor(bp, spawn_point)
        vehicle.set_autopilot(True)
        actor_list.append(vehicle)

        def make_listener(config, idx):
            def callback(image):
                image.convert(cc.Raw)
                array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
                array = np.reshape(array, (image.height, image.width, 4))
                array = array[:, :, :3]
                array = array[:, :, ::-1]
                config[4] = pygame.surfarray.make_surface(array.swapaxes(0, 1))
                cv2.imwrite(f"{config[0]}_{idx}.png", array)
            return callback

        for i, config in enumerate(CAMERA_CONFIGS):
            rgb_bp = blueprint_library.find("sensor.camera.rgb")
            rgb_bp.set_attribute("image_size_x", str(UNIT_WIDTH))
            rgb_bp.set_attribute("image_size_y", str(UNIT_HEIGHT))
            rgb_bp.set_attribute("fov", str(config[2]))
            rgb_bp.set_attribute("sensor_tick", "0.033")

            rgb_camera = world.spawn_actor(rgb_bp, config[1], attach_to=vehicle)
            actor_list.append(rgb_camera)
            print("created %s %d" % (rgb_camera.type_id, i))
            rgb_camera.listen(make_listener(config, i))

        display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(60)
            for i, config in enumerate(CAMERA_CONFIGS):
                if config[4]:
                    display.blit(config[4], config[3])
            pygame.display.flip()

    finally:
        print("Destroying actors")
        for actor in actor_list:
            print("destroy %s" % actor.type_id)
            if(isinstance(actor, carla.Sensor)):
                print("stop %s" % actor.type_id)
                actor.stop()
            actor.destroy()
        print("done.")

        pygame.quit()


def main():
    argparser = argparse.ArgumentParser(
        description="CARLA Manual Control Client")
    argparser.add_argument(
        "--host",
        metavar="HOST",
        default="127.0.0.1",
        help="IP of the host server (default: 127.0.0.1)")
    argparser.add_argument(
        "-p", "--port",
        metavar="PORT",
        default=2000,
        type=int,
        help="TCP port to listen to (default: 2000)")
    argparser.add_argument(
        "-m", "--map",
        metavar="MAP",
        default="Town02",
        help="Specify which map to load")
    argparser.add_argument(
        "-a", "--autopilot",
        action="store_true",
        help="Enable autopilot")
    argparser.add_argument(
        "--res",
        metavar="WIDTHxHEIGHT",
        default="960x540",
        help="Window resolution (default: 960x540)")

    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.res.split("x")]

    try:
        game_loop(args)

    except KeyboardInterrupt:
        print("\nCancelled by user. Bye!")

if __name__ == "__main__":

    main()
