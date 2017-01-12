#! /usr/bin/env python3

from collections import defaultdict
from itertools import cycle, islice, product
import math
import sqlite3 as sql

from pprint import pprint

import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.pyplot as plt

CONFIG = {
    "Specfem3dDB" : "specfem3d_license_info.db",
    "DatabaseSchema" : """
        CREATE TABLE licenses
            (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                line_amount INTEGER DEFAULT NULL
            );
        CREATE TABLE project_files
            (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                manual_license REFERENCES licenses (id)
            );
        CREATE TABLE ranking_algorithms
            (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
        CREATE TABLE calculated_license_rank
            (
                file REFERENCES project_files (id),
                algorithm REFERENCES ranking_algorithms (id),
                license REFERENCES licenses (id),
                ranking REAL NOT NULL,
                position_lineno INTEGER NOT NULL,
                PRIMARY KEY (file, algorithm, license)
            );
        """,
    "ColorList" : cycle(
        colors.hsv_to_rgb(triple)
        for triple in product(
            [i / 8 for i in range(8)],
            [5 / 6],
            [7 / 8, 5 / 8],
        )
    ),
}


if __name__ == "__main__":
    with sql.connect(
        "file:{}?mode=ro".format(CONFIG["Specfem3dDB"]),
        uri=True,
    ) as conn:
        cursor = conn.cursor()

        # bar graph showing number of files per license
        cursor = cursor.execute("""
            SELECT
              licenses.name,
              COUNT(*)
            FROM
                  project_files
              JOIN
                  licenses
                ON
                  project_files.manual_license = licenses.id
            GROUP BY
              project_files.manual_license
        """)

        data = { license : count for license, count in cursor }

        data_keys, data_values = zip(
            *sorted(
                data.items(),
                key=lambda pair: tuple(reversed(pair)),
            )
        )

        data_keys = list(data_keys)
        data_values = list(data_values)

        files_per_license_fig = plt.figure()
        files_per_license_fig.suptitle(
            "# of Files Per License (Manually Classified)"
        )

        files_per_license_fig.add_subplot(2,1,1)
        files_per_license_ax = files_per_license_fig.gca()

        files_per_license_fig.add_subplot(2,1,2)
        files_per_license_zoomed_ax = files_per_license_fig.gca()

        files_per_license_ax.barh(
            range(len(data_keys)),
            data_values,
            tick_label=data_keys,
            align="center",
            color=list(islice(CONFIG["ColorList"], 1)),
            edgecolor="",
        )

        files_per_license_zoomed_ax.barh(
            range(len(data_keys)),
            data_values,
            tick_label=data_keys,
            align="center",
            color=list(islice(CONFIG["ColorList"], 1)),
            edgecolor="",
        )

        files_per_license_ax.set_xlabel("# of files")
        files_per_license_zoomed_ax.set_xlabel("# of files")

        files_per_license_ax.set_ylim(-9 / 8, len(data_keys))
        files_per_license_zoomed_ax.set_ylim(-9 / 8, len(data_keys))
        files_per_license_zoomed_ax.set_xlim(0, 35)

        files_per_license_ax.grid(axis="x")
        files_per_license_zoomed_ax.grid(axis="x")

        # histograms showing rank distribution for correctly and incorrectly
        # ranked licenses (matching or not matching manual license
        # determination)
        rank_dist_fig = plt.figure()
        rank_dist_fig.suptitle(
            "Sameness Distribution"
        )
        rank_dist_license_fig = plt.figure()
        rank_dist_license_fig.suptitle(
            "Sameness Distribution per License"
        )

        rank_dist_fig.add_subplot()
        rank_dist_ax = rank_dist_fig.gca()

        cursor = cursor.execute("""
            SELECT
              calculated_license_rank.license = project_files.manual_license,
              ranking_algorithms.name,
              licenses.name,
              calculated_license_rank.ranking
            FROM
                  calculated_license_rank
              JOIN
                  project_files
                ON
                  calculated_license_rank.file = project_files.id
              JOIN
                  ranking_algorithms
                ON
                  calculated_license_rank.algorithm = ranking_algorithms.id
              JOIN
                  licenses
                ON
                  project_files.manual_license = licenses.id
            GROUP BY
                calculated_license_rank.file,
                calculated_license_rank.algorithm
              HAVING
                MAX(calculated_license_rank.ranking)
        """)

        data = defaultdict(list)
        data_per_license = defaultdict(lambda: defaultdict(list))

        for match, algorithm, manual_license, ranking in cursor:
            data[(bool(match), algorithm)].append(ranking)

            data_per_license[manual_license][
                (bool(match), algorithm)
            ].append(ranking)

        data_keys, data_values = zip(*sorted(data.items()))

        rank_dist_ax.hist(
            data_values,
            range=(0,1),
            bins=50,
            color=list(islice(CONFIG["ColorList"], len(data))),
            edgecolor="None",
            label=[
                "{} - {} {}".format(
                    algorithm,
                    len(data[(match, algorithm)]),
                    "correctly ranked" if match else "incorrectly ranked",
                )
                for match, algorithm in data_keys
            ],
        )

        rank_dist_ax.set_xticklabels([
            "{:.0%}".format(tick)
            for tick in rank_dist_ax.get_xticks()
        ])

        rank_dist_ax.set_xlabel("Algorithm Result (Sameness)")
        rank_dist_ax.legend(loc="best")
        rank_dist_ax.grid(True)

        data_per_license = dict(
            filter(
                lambda pair: 4 < sum(len(ranks) for ranks in pair[1].values()),
                data_per_license.items(),
            )
        )

        for index, (license, license_dict) in enumerate(
            sorted(
                data_per_license.items(),
                key=lambda pair: sum(len(ranks) for ranks in pair[1].values()),
                reverse=True,
            ),
            1,
        ):
            license_dict_keys, license_dict_values = zip(
                *sorted(license_dict.items(), reverse=True)
            )

            rank_dist_license_fig.add_subplot(
                math.floor(len(data_per_license) ** (1 / 2)),
                math.ceil(len(data_per_license) ** (1 / 2)),
                index,
            )
            ax = rank_dist_license_fig.gca()

            ax.hist(
                license_dict_values,
                range=(0,1),
                bins=50,
                label=[
                    "{} - {} {}".format(
                        algorithm,
                        len(license_dict[(match, algorithm)]),
                        "correctly ranked" if match else "incorrectly ranked",
                    )
                    for match, algorithm in license_dict_keys
                ],
                color=list(islice(
                    CONFIG["ColorList"],
                    len(license_dict) + len(license_dict) % 2,
                ))[:len(license_dict)],
                edgecolor="None",
                width=1 / 100,
                rwidth=1,
            )

            ax.set_xticklabels([
                "{:.0%}".format(tick)
                for tick in ax.get_xticks()
            ])

            ax.grid(True)
            ax.legend(loc='best', fontsize="small")
            ax.set_title("{}".format(license))

        plt.show()
