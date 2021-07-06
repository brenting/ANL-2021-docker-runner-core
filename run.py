import glob
import os
import tempfile
import zipfile
from shutil import move
from typing import DefaultDict
from uuid import uuid4

import yaml

from scripts.session import Session
from scripts.plot import plot_results

tmp_dir = os.path.join(tempfile.gettempdir(), "geniusweb")


def main():
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    jar_to_classpath = check_agent_jars(glob.glob("parties/*"))

    with open("settings.yaml", "r") as f:
        settings = yaml.load(f.read(), Loader=yaml.FullLoader)

    uuid_to_name = prepare_check_settings(settings, jar_to_classpath)

    for id, session_data in enumerate(settings):
        session = Session(session_data)
        session.execute()
        session.post_process(id)

    rename_tmp_files(uuid_to_name)
    plot_results()



def check_agent_jars(agent_jar_files):
    agent_pkgs = DefaultDict(list)
    jar_to_classpath = {}

    for agent_jar_file in agent_jar_files:
        jar = zipfile.ZipFile(agent_jar_file, "r")
        manifest = jar.read("META-INF/MANIFEST.MF").decode("ascii").split()

        main_cls = [
            manifest[i + 1] for i, x in enumerate(manifest) if x == "Main-Class:"
        ][0]
        agent_pkg = main_cls.rsplit(".", 1)[0]
        agent_pkgs[agent_pkg].append(agent_jar_file)

        jar_to_classpath[agent_jar_file] = main_cls

        jar.close()

    for agent_pkg, jar_files in agent_pkgs.items():
        if len(jar_files) > 1:
            files = "\n".join(jar_files)
            raise RuntimeError(
                f"Found duplicate agent package classpath:\n{agent_pkg}\nin:\n{files}\nPlease make sure that the agent jar-files do not contain duplicate package classpaths."
            )

    return jar_to_classpath


def prepare_check_settings(settings, jar_to_classpath):
    profiles = set(glob.glob("profiles/**/*.json", recursive=True))

    def str_uuid():
        return str(uuid4())

    file_to_uuid = DefaultDict(str_uuid)
    track_files = DefaultDict(list)

    assert isinstance(settings, list)
    for idx, session in enumerate(settings):
        assert isinstance(session, dict)
        assert len(session) == 1
        assert next(iter(session)) in {"negotiation", "learn"}
        session_details = next(iter(session.values()))
        assert isinstance(session_details, dict)
        assert len(session_details) == 2
        assert "deadline" in session_details
        assert "parties" in session_details
        assert session_details["deadline"] > 0
        parties = session_details["parties"]
        assert isinstance(parties, list)
        if "negotiation" in session:
            assert len(parties) == 2
        for party in parties:
            assert "party" in party
            assert all([key in {"party", "profile", "parameters"} for key in party])
            assert party["party"] in jar_to_classpath
            party["party"] = jar_to_classpath[party["party"]]
            party_name = party["party"].split(".")[-1]
            prms = {}
            if "negotiation" in session:
                assert party["profile"] in profiles
                party["profile"] = f"file:{party['profile']}"
                prms["persistentstate"] = file_to_uuid[f"{party_name}_state"]
                negotiationdata_fn = file_to_uuid[f"{party_name}_session_{idx}"]
                prms["negotiationdata"] = [negotiationdata_fn]
                track_files[party_name].append(negotiationdata_fn)
            elif "learn" in session:
                party["profile"] = "http://prof1"
                prms["persistentstate"] = file_to_uuid[f"{party_name}_state"]
                prms["negotiationdata"] = track_files[party_name]
                track_files[party_name] = []

            if "parameters" in party:
                prms_yaml = party["parameters"]
                assert "persistentstate" not in prms_yaml
                assert "negotiationdata" not in prms_yaml
                prms.update(prms_yaml)

            party["parameters"] = prms

    uuid_to_name = {v: k for k, v in file_to_uuid.items()}

    return uuid_to_name


def rename_tmp_files(uuid_to_name):
    uuid_files = glob.glob(f"{tmp_dir}/*")

    for uuid_file in uuid_files:
        uuid = os.path.basename(uuid_file)
        if uuid in uuid_to_name:
            move(uuid_file, f"tmp/{uuid_to_name[uuid]}")


if __name__ == "__main__":
    main()
