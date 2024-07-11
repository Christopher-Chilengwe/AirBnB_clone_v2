#!/usr/bin/python3
# Fabfile to create and distribute an archive to a web server.
import os.path
from datetime import datetime
from fabric.api import env, local, put, run

env.hosts = ["104.196.168.90", "35.196.46.172"]

def do_pack():
    """Create a tar gzipped archive of the directory web_static."""
    dt = datetime.utcnow()
    file = "versions/web_static_{}{}{}{}{}{}.tgz".format(dt.year,
                                                         dt.month,
                                                         dt.day,
                                                         dt.hour,
                                                         dt.minute,
                                                         dt.second)
    if not os.path.isdir("versions"):
        if local("mkdir -p versions").failed:
            print("Failed to create versions directory.")
            return None
    if local("tar -cvzf {} web_static".format(file)).failed:
        print("Failed to create tar archive.")
        return None
    return file

def do_deploy(archive_path):
    """Distributes an archive to a web server.

    Args:
        archive_path (str): The path of the archive to distribute.
    Returns:
        If the file doesn't exist at archive_path or an error occurs - False.
        Otherwise - True.
    """
    if not os.path.isfile(archive_path):
        print("Archive path does not exist.")
        return False
    
    file = archive_path.split("/")[-1]
    name = file.split(".")[0]

    try:
        if put(archive_path, "/tmp/{}".format(file)).failed:
            print("Failed to upload archive.")
            return False
        if run("rm -rf /data/web_static/releases/{}/".format(name)).failed:
            print("Failed to remove old release.")
            return False
        if run("mkdir -p /data/web_static/releases/{}/".format(name)).failed:
            print("Failed to create release directory.")
            return False
        if run("tar -xzf /tmp/{} -C /data/web_static/releases/{}/".format(file, name)).failed:
            print("Failed to extract archive.")
            return False
        if run("rm /tmp/{}".format(file)).failed:
            print("Failed to remove temporary archive.")
            return False
        if run("mv /data/web_static/releases/{}/web_static/* /data/web_static/releases/{}/".format(name, name)).failed:
            print("Failed to move files.")
            return False
        if run("rm -rf /data/web_static/releases/{}/web_static".format(name)).failed:
            print("Failed to remove web_static directory.")
            return False
        if run("rm -rf /data/web_static/current").failed:
            print("Failed to remove current symbolic link.")
            return False
        if run("ln -s /data/web_static/releases/{}/ /data/web_static/current".format(name)).failed:
            print("Failed to create new symbolic link.")
            return False
        print("New version deployed!")
        return True
    except Exception as e:
        print(f"Deployment failed: {e}")
        return False

def deploy():
    """Create and distribute an archive to a web server."""
    file = do_pack()
    if file is None:
        print("Packing failed.")
        return False
    return do_deploy(file)
