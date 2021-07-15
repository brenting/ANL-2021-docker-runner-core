import json
import subprocess

from scripts.utility_space import UtilitySpace


class Session:
    exec_command = [
        "java",
        "-cp",
        "scripts/simplerunner-1.6.0-jar-with-dependencies.jar:parties/*",
        "geniusweb.simplerunner.NegoRunner",
        "settings.json",
    ]

    def __init__(self, session_data):
        self.mode = next(iter(session_data.keys()))
        self.profiles = []
        session_data = next(iter(session_data.values()))

        participants = []
        for party in session_data["parties"]:
            self.profiles.append(party["profile"])
            participants.append(
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"classpath:{party['party']}",
                                    "parameters": party["parameters"]
                                    if "parameters" in party
                                    else {},
                                },
                                "profile": party["profile"],
                            }
                        ]
                    }
                }
            )

        self.settings = {
            "LearnSettings"
            if self.mode == "learn"
            else "SAOPSettings": {
                "participants": participants,
                "deadline": {
                    "deadlinetime": {"durationms": session_data["deadline"] * 1000}
                },
            }
        }

    def execute(self):
        with open("settings.json", "w") as f:
            f.write(json.dumps(self.settings))

        subprocess.call(self.exec_command)

    def post_process(self, id):
        with open("results.json", "r") as f:
            results = json.load(f)

        if self.mode == "negotiation":
            self.add_utilities_to_results(results)

        with open(f"results/{id+1:04d}_{self.mode}.json", "w") as f:
            f.write(json.dumps(results, indent=2))

    def add_utilities_to_results(self, results):
        results = results["SAOPState"]

        if results["actions"]:
            utility_spaces = {
                k: UtilitySpace(v["profile"])
                for k, v in results["partyprofiles"].items()
            }
            for action in results["actions"]:
                if "offer" in action:
                    offer = action["offer"]
                elif "accept" in action:
                    offer = action["accept"]
                else:
                    continue

                bid = offer["bid"]["issuevalues"]
                offer["utilities"] = {
                    k: v.get_utility(bid) for k, v in utility_spaces.items()
                }
